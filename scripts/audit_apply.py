#!/usr/bin/env python3
"""
audit_apply.py — 审核申请（解密申请者发来的 RSA 密文）

用法:
    python3 scripts/audit_apply.py "<申请密文>"      # 直接传密文
    python3 scripts/audit_apply.py                   # 或交互粘贴

流程:
    1. 用本地私钥解密密文，显示申请信息（账号/密码/姓名/电话/时间）
    2. 确认通过后，自动把账号写入 accounts.json
    3. 提示重新运行 encrypt_private.py 加密并推送，账号即生效

说明:
    私钥在 scripts/keys/private_key.pem，仅本地持有，永不提交。
"""
import os
import sys
import json
import base64
import datetime

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA256

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRIV_KEY = os.path.join(ROOT, "scripts/keys/private_key.pem")
ACCOUNTS = os.path.join(ROOT, "accounts.json")


def decrypt(cipher_b64):
    key = RSA.import_key(open(PRIV_KEY, encoding="utf-8").read())
    cipher = PKCS1_OAEP.new(key, hashAlgo=SHA256)
    return cipher.decrypt(base64.b64decode(cipher_b64)).decode("utf-8")


def main():
    cipher_b64 = sys.argv[1] if len(sys.argv) > 1 else None
    if cipher_b64 is None:
        cipher_b64 = input("粘贴申请密文: ").strip()
    if not cipher_b64:
        print("❌ 密文为空")
        sys.exit(1)

    try:
        info = json.loads(decrypt(cipher_b64))
    except Exception as e:
        print(f"❌ 解密失败: {e}")
        sys.exit(1)

    print("\n" + "=" * 40)
    print("📋 收到的申请：")
    print(f"  账号: {info.get('user')}")
    print(f"  密码: {info.get('pass')}")
    print(f"  姓名: {info.get('name')}")
    print(f"  电话: {info.get('phone')}")
    print(f"  时间: {info.get('ts')}")
    print("=" * 40)

    choice = input("审核通过？[y/N] ").strip().lower()
    if choice not in ("y", "yes"):
        print("已拒绝，未写入账号库。")
        sys.exit(0)

    user = info.get("user", "").strip()
    if not user:
        print("❌ 申请里没有账号字段")
        sys.exit(1)

    accounts = json.load(open(ACCOUNTS, encoding="utf-8"))
    if any(a.get("user") == user for a in accounts):
        print(f"⚠️ 账号 {user} 已存在，跳过写入（如需改密码请手动编辑 accounts.json）")
    else:
        accounts.append({
            "user": user,
            "pass": info.get("pass", ""),
            "name": info.get("name", ""),
            "phone": info.get("phone", ""),
            "added": datetime.date.today().isoformat(),
        })
        json.dump(accounts, open(ACCOUNTS, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        print(f"✅ 账号 {user} 已加入 accounts.json")

    print("\n下一步：")
    print("  python3 scripts/encrypt_private.py   # 重新加密（会用账号库中全部账号）")
    print("  然后 git 提交推送，账号即可登录 /private/")


if __name__ == "__main__":
    main()
