---
title: 本站搭建记录：从零到上线 🔧
date: 2026-09-15 19:25:00 +0800
categories: [技术, 折腾]
tags: [Jekyll, GitHub Pages, Chirpy, 建站]
---

记录一下这个网站是怎么搭起来的，方便以后维护，也给想建个人网站的朋友留份参考。📝

## 选型 🧐

- **托管**：GitHub Pages —— 免费、稳定、支持自定义域名
- **静态站生成器**：Jekyll —— GitHub Pages 原生支持，无需额外服务器
- **主题**：Chirpy —— 自带暗色/亮色模式、标签、分类、归档、全文搜索、PWA，适合「个人简历 + 博客」的定位

## 搭建步骤 🛠️

1. 拉取 Chirpy 官方 starter 模板到本地仓库
2. 修改 `_config.yml`：站点标题、时区、头像、社交链接、部署地址
3. 编写 `_tabs/about.md` 作为个人简历页，往 `_posts/` 添加博客文章
4. 本地预览：`bundle exec jekyll s`
5. 推送代码到 GitHub，仓库自带 `.github/workflows/pages-deploy.yml`，push 后自动构建并发布

## 日常写博客的流程 ✍️

以后每次写文章只需三步：

```bash
# 1. 在 _posts/ 下新建一个 markdown 文件，命名格式：
#    YYYY-MM-DD-标题.md（front matter 里写 title/date/categories/tags）

# 2. 本地预览确认效果
bundle exec jekyll s

# 3. 提交并推送，网站自动更新
git add .
git commit -m "add new post"
git push
```

## 一些坑 ⚠️

- 网络直连 GitHub 不稳定，克隆/推送失败时可以多试几次或换 SSH；
- 文章文件名里的日期就是发布日期，写错会导致文章被跳过；
- 图片统一放在 `assets/img/` 下，用相对路径引用。

以后有新玩法再补充。🚀
