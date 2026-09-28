#!/usr/bin/env python3
"""
encrypt_private.py — 私密空间加密脚本（列表页 + 每篇文章独立页）

用法:
    python3 scripts/encrypt_private.py                 # 交互输入账号和密码
    python3 scripts/encrypt_private.py "账号" "密码"    # 或直接传

流程:
    1. 读取 _private/*.md（排除 README.md），每篇支持 front matter: title/date
    2. 每篇渲染 HTML → 独立加密 → 生成 private-<slug>.md（/private/<slug>/）
    3. 生成列表页 private.md（/private/）：标题 + 日期 + 摘要 + 链接，整体加密

前端解密: 浏览器 Web Crypto（PBKDF2 200000 次 + AES-256-GCM），账号密码格式 "账号:密码"
会话: 登录列表页成功后写入 sessionStorage，文章页自动复用账号密码解密。
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
    """返回 (slug, title, date_str, body_html, summary)"""
    raw = open(path, encoding="utf-8").read()
    fm, body = split_front_matter(raw)
    slug = os.path.splitext(os.path.basename(path))[0]
    title = fm.get("title", slug)
    date_str = fm.get("date", "")
    MD.reset()
    body_html = MD.convert(body)
    # 摘要：去 markdown 符号后截取
    summary = re.sub(r"[#>*`\[\]!|\-]", "", body)
    summary = re.sub(r"\s+", " ", summary).strip()
    if len(summary) > 80:
        summary = summary[:80] + "…"
    return slug, title, date_str, body_html, summary


def encrypt(accounts, plaintext):
    """信封加密：内容密钥 dek 随机生成；每个账号用自己密码派生的 KEK 包裹 dek"""
    dek = os.urandom(32)
    salt = os.urandom(16)
    iv = os.urandom(12)
    cipher = AES.new(dek, AES.MODE_GCM, nonce=iv)
    ct, tag = cipher.encrypt_and_digest(plaintext.encode("utf-8"))

    wraps = {}
    for acc in accounts:
        user = acc["user"]
        password = acc["pass"]
        kek = PBKDF2(f"{user}:{password}", salt, 32,
                     count=PBKDF2_ITERATIONS, hmac_hash_module=SHA256)
        wiv = os.urandom(12)
        wc = AES.new(kek, AES.MODE_GCM, nonce=wiv)
        wct, wtag = wc.encrypt_and_digest(dek)
        wraps[user] = {
            "i": base64.b64encode(wiv).decode(),
            "k": base64.b64encode(wct + wtag).decode(),
        }

    payload = {
        "s": base64.b64encode(salt).decode(),
        "i": base64.b64encode(iv).decode(),
        "c": base64.b64encode(ct + tag).decode(),
        "wraps": wraps,
    }
    # 整体再 base64 一层，避免任何字符与 front matter / Liquid 冲突
    return base64.b64encode(json.dumps(payload).encode()).decode()


def make_page(title, permalink, cipher_b64):
    lines = [
        "---",
        "layout: page",
        f"title: {title}",
        f"permalink: {permalink}",
        "encrypted: true",
        "ciphertext: |",
        f"  {cipher_b64}",
        "---",
        "",
    ]
    return "\n".join(lines)


ACCOUNTS_FILE = os.path.join(ROOT, "accounts.json")


def load_accounts():
    """从 accounts.json 读取账号库（user/pass/name/phone）"""
    if not os.path.exists(ACCOUNTS_FILE):
        print(f"❌ 缺少 {ACCOUNTS_FILE}，请先创建账号库（含站长账号）")
        sys.exit(1)
    accounts = json.load(open(ACCOUNTS_FILE, encoding="utf-8"))
    accounts = [
        {"user": a.get("user", "").strip(), "pass": a.get("pass", "")}
        for a in accounts
        if a.get("user", "").strip() and a.get("pass")
    ]
    if not accounts:
        print("❌ accounts.json 里没有可用账号（需要 user + pass）")
        sys.exit(1)
    return accounts


def main():
    user = sys.argv[1] if len(sys.argv) > 1 else None
    password = sys.argv[2] if len(sys.argv) > 2 else None

    files = [
        f for f in sorted(glob.glob(os.path.join(PRIVATE_DIR, "*.md")))
        if os.path.basename(f).lower() != "readme.md"
    ]
    if not files:
        print(f"❌ {PRIVATE_DIR}/ 目录下没有 .md 文章，请先放入私密文章")
        sys.exit(1)

    if user is None:
        user = input("设置账号 [默认 news]: ").strip() or "news"
    if password is None:
        password = getpass.getpass("设置密码: ")
    if not password:
        print("❌ 密码不能为空")
        sys.exit(1)
    accounts = load_accounts()
    if user not in [a["user"] for a in accounts]:
        print(f"❌ 账号 {user} 不在 accounts.json 授权名单里")
        sys.exit(1)

    # 清理旧的独立文章页（防止删除文章后残留）
    for old in glob.glob(os.path.join(ROOT, "private-*.md")):
        os.remove(old)

    items = []
    for f in files:
        slug, title, date_str, body_html, summary = render_article(f)

        # 每篇文章独立加密页
        permalink = f"/private/{slug}/"
        cipher = encrypt(accounts, body_html)
        with open(os.path.join(ROOT, f"private-{slug}.md"), "w",
                  encoding="utf-8") as fh:
            fh.write(make_page(title, permalink, cipher))

        # 列表项
        date_html = f'<div class="text-muted small mb-1">{date_str}</div>' if date_str else ""
        items.append(
            f'<article class="mb-4">'
            f'<h2 class="h4 mb-1"><a href="{permalink}">{title}</a></h2>'
            f"{date_html}"
            f'<p class="mb-0">{summary}</p>'
            f"</article>"
        )
        print(f"  📄 {slug}.md → /private/{slug}/")

    list_html = "\n".join(items)
    cipher = encrypt(accounts, list_html)
    with open(os.path.join(ROOT, "private.md"), "w", encoding="utf-8") as fh:
        fh.write(make_page("私密空间", "/private/", cipher))

    print(f"✅ 已加密 {len(files)} 篇文章，授权账号 {len(accounts)} 个")
    print(f"   列表页: /private/  （当前操作账号: {user}）")
    print("   ⚠️ 请务必记好账号和密码，忘记后无法找回（只能重新加密）")


if __name__ == "__main__":
    main()
