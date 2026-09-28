# 私密空间使用手册

## 一、写/改私密文章

1. 把私密文章的 Markdown 放进本目录（文件名任意，如 `MyNote.md`），可带 front matter：

   ```yaml
   ---
   title: 文章标题
   date: 2026-09-28 12:00:00 +0800
   ---
   ```

2. 在项目根目录运行：

   ```bash
   python3 scripts/encrypt_private.py
   ```

   按提示输入操作账号（默认 `news`）和密码，脚本会对**所有已授权账号**重新加密并生成：
   - `private.md`（私密列表页 → `/private/`）
   - `private-<文件名>.md`（单篇页 → `/private/<文件名>/`）

3. 用 GitHub Desktop 提交推送，线上即更新。

> ⚠️ 本目录的 `*.md` 全部被 .gitignore 忽略，**绝不推送到公开仓库**。忘记管理员密码只能重新加密（其他账号密码也会跟着重置）。

## 二、审批新账号（收到申请后）

申请人填 `/apply/` 表单后，会得到一段加密密文并发给你。审批步骤：

```bash
# 1. 在项目根目录运行审核脚本（密文较长也可以直接粘贴）
python3 scripts/audit_apply.py "<申请人发来的密文>"

# 2. 屏幕上会显示申请信息（账号/密码/姓名/电话/时间）
#    核对无误后输入 y 回车 → 账号写入本地 accounts.json

# 3. 重新加密（让新账号的解密密钥包进每篇文章）
python3 scripts/encrypt_private.py

# 4. GitHub Desktop 提交推送
```

推送完成后告诉申请人：去 `https://zhuzheming001.github.io/private/` 用申请的账号密码登录即可。

> ⚠️ 忘记步骤 3（重新加密+推送），新账号即使写进 accounts.json 也登录不了，因为文章密文里还没包他的密钥信封。

## 三、删除账号 / 改密码

编辑根目录的 `accounts.json`（一行一个账号），删掉或改掉对应条目后：
重跑 `python3 scripts/encrypt_private.py` → 推送。

## 四、账号库与密钥（切勿外传）

- `accounts.json`：已授权账号清单（账号/密码/姓名/电话）
- `scripts/keys/`：RSA 密钥对（私钥只有你本地有，gitignored）
- 两者都不在任何公开文件里
