#!/usr/bin/env python3
"""
encrypt_private.py — 把 _private/ 目录里的私密文章合并加密，生成私密空间页面

用法:
    python3 scripts/encrypt_private.py            # 交互输入通用密码
    python3 scripts/encrypt_private.py "密码"     # 或直接传密码

流程:
    1. 读取 _private/*.md 全部文章（每篇可有自己的 front matter: title/date）
    2. 渲染为 HTML 并合并
    3. 密码经 PBKDF2(200000 次) 派生密钥，AES-256-GCM 加密
    4. 生成根目录 private.md（front matter 带 ciphertext，正文留空）

前端解密: 浏览器 Web Crypto API（PBKDF2 + AES-GCM），参数与本脚本一致。
"""
import os
import sys
import re
import glob
import json
import base64
import getpass

from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256
import markdown

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRIVATE_DIR = os.path.join(ROOT, "_private")
OUTPUT = os.path.join(ROOT, "private.md")

MD = markdown.Markdown(
    extensions=["tables", "fenced_code", "attr_list", "footnotes"]
)

PBKDF2_ITERATIONS = 200000


def split_front_matter(text):
    """拆出 front matter 字典和正文"""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
    if not m:
        return {}, text
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm, m.group(2)


def render_article(path):
    raw = open(path, encoding="utf-8").read()
    fm, body = split_front_matter(raw)
    title = fm.get("title", os.path.splitext(os.path.basename(path))[0])
    date_str = fm.get("date", "")
    html = f'<h2 class="mt-4">{title}</h2>'
    if date_str:
        html += f'<div class="text-muted mb-2">{date_str}</div>'
    # 每篇单独重置，避免 markdown 状态残留
    MD.reset()
    html += MD.convert(body)
    return html


def encrypt(password, plaintext):
    salt = os.urandom(16)
    iv = os.urandom(12)
    key = PBKDF2(password, salt, 32, count=PBKDF2_ITERATIONS,
                 hmac_hash_module=SHA256)
    cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
    ct, tag = cipher.encrypt_and_digest(plaintext.encode("utf-8"))
    payload = {
        "s": base64.b64encode(salt).decode(),
        "i": base64.b64encode(iv).decode(),
        "c": base64.b64encode(ct + tag).decode(),
    }
    # 整体再 base64 一层，避免任何字符与 front matter / Liquid 冲突
    return base64.b64encode(json.dumps(payload).encode()).decode()


def main():
    password = sys.argv[1] if len(sys.argv) > 1 else None
    files = [
        f for f in sorted(glob.glob(os.path.join(PRIVATE_DIR, "*.md")))
        if os.path.basename(f).lower() != "readme.md"
    ]
    if not files:
        print(f"❌ {PRIVATE_DIR}/ 目录下没有 .md 文章，请先放入私密文章")
        sys.exit(1)

    if password is None:
        password = getpass.getpass("输入通用密码: ")
    if not password:
        print("❌ 密码不能为空")
        sys.exit(1)

    html = "\n<hr class=\"my-5\">\n".join(render_article(f) for f in files)
    cipher_b64 = encrypt(password, html)

    output = (
        "---\n"
        "layout: page\n"
        "title: 私密空间\n"
        "permalink: /private/\n"
        "encrypted: true\n"
        "ciphertext: |\n"
        f"  {cipher_b64}\n"
        "---\n"
    )
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"✅ 已加密 {len(files)} 篇文章 → {OUTPUT}")
    print(f"   页面地址: {ROOT}/private.md (部署后访问 /private/)")
    print("   ⚠️ 请务必记好密码，忘记后无法找回（只能重新加密）")


if __name__ == "__main__":
    main()
