# 对话核心摘要 — 2026-06-10 内容质量升级（未完成）

> 新对话时读此文件无缝接续。

---

## 1. 项目背景

搜狐新闻时间线内容生成工具。网页选类型→点按钮→GitHub Actions 调 AI 生成帖子→结果显示在网页→复制发布。

- 网站: https://klnm2037453337-sudo.github.io/sohuxw/
- 仓库: klnm2037453337-sudo/sohuxw
- 目标平台: **仅搜狐新闻时间线** (timeline.sohu.com，2000字限制，#话题#，转发链)

---

## 2. 本次对话要解决的问题

1. **API 迁移**: DeepSeek → 豆包 → DeepSeek（兜了一圈回来了）
2. **内容质量**: 三层 Prompt（人设+语气+类型指导）、联网搜索主流媒体多源改写
3. **触发方式**: JS fetch API 调 GitHub → 直接打开 Actions 页面手动触发（去掉 PAT）

---

## 3. 已完成改动

| 文件 | 改动 | 状态 |
|------|------|------|
| `scripts/generate.py` | **重写** — 三层 Prompt 架构（PERSONA + TONE_FORMAL/TONE_CASUAL + GENRE_CONFIGS 12种），API 用 DeepSeek `deepseek-chat`，环境变量 `DEEPSEEK_API_KEY` | ✅ 已部署 |
| `.github/workflows/generate.yml` | env 改回 `DEEPSEEK_API_KEY`，依赖 `pip install openai requests` | ✅ 已部署 |
| `script.js` | **去掉 GH_PAT**，生成按钮改为 `window.open()` 打开 Actions 页面让用户手动点 Run workflow，保留轮询机制 | ✅ 已部署 |
| `style.css` | 新增参考来源链接样式（preview/post-card/modal） | ✅ 已部署 |
| `index.html` | 预览面板新增参考来源元素 `#preview-source` | ✅ 已部署 |

---

## 4. 关键踩坑记录

| 问题 | 原因 | 解决 |
|------|------|------|
| GitHub API 401 Bad credentials | PAT 过期 / 推送到公开仓库后被 GitHub 自动吊销 | **去掉 PAT**，改为打开 Actions 页面手动触发 |
| Git push 被 Push Protection 拦截 | 公开仓库提交 PAT 被检测为密钥泄露 | 放弃 PAT 方案 |
| 豆包 API 404 ModelNotOpen | 模型 `doubao-seed-1-8-251228` 未在火山引擎控制台开通 | 改回 DeepSeek |
| 豆包 `/responses` 端点格式错误 | 豆包 ARK 用的是 `/chat/completions` OpenAI 兼容格式，不是 `/responses` | 已修复（但后来改回 DeepSeek 了） |
| 用户网页改 script.js 不生效 | GitHub.com web editor 可能未点 Commit 或未保存 | 改为本地提交推送 |

---

## 5. 当前生成流程

```
网页选类型+字数 → 点「生成」
  → 新标签页打开 GitHub Actions workflow 页面
  → 用户手动点 Run workflow → 选择 genre/word_count → 点绿色 Run workflow
  → 切回原标签页 → JS 轮询 posts.json → 检测到新帖子 → 显示预览
```

---

## 6. 当前 Prompt 架构

```
PERSONA（共享人设："江"，有思考深度的内容创作者）
  ↓
TONE（语气档：正式-可读型 vs 轻松-个人型）
  ├── 正式-可读：观点态度(3种) + 知识科普(5种)
  └── 轻松-个人：实用生活(4种)
  ↓
GENRE_GUIDE（类型专属：选题+结构+话题+字数）
```

12 种类型配置在 `generate.py` 的 `GENRE_CONFIGS` 字典中。

---

## 7. 下一步：当前阻塞 + 待解决

### 🔴 当前阻塞
**DeepSeek API 调用失败** — 最新一次 Actions 运行报错，需要看日志确定原因。可能的原因：
- DEEPSEEK_API_KEY 余额不足或过期
- 模型名 `deepseek-chat` 需要确认是否正确
- API 返回格式问题（之前 DeepSeek 返回的 JSON 格式不稳定，已有容错代码）

### 🟡 待完成
1. **确认 DeepSeek API 能正常调用** — 跑通一次完整流程
2. **语气分级效果验证** — 对比正式型和轻松型的输出质量
3. **Prompt 精调** — 根据实际生成效果调整 12 种类型的指导
4. **配图功能** — 暂无方案

---

## 8. 用户偏好

- 发布平台：仅搜狐新闻时间线
- 观点态度 + 知识科普 = 偏正式，实用生活 = 口语化
- 内容基于主流媒体搜索改写（微信公众号、头条、网易、搜狐、腾讯、微博）
- 附参考来源链接
- API 选择：DeepSeek（豆包开通太麻烦）

---

## 9. 关键代码路径

- Prompt 配置: `scripts/generate.py` → `PERSONA` / `TONE_FORMAL` / `TONE_CASUAL` / `GENRE_CONFIGS`
- API 调用: `scripts/generate.py` → `generate_post_text()` (DeepSeek, `deepseek-chat`)
- Workflow 配置: `.github/workflows/generate.yml` → env `DEEPSEEK_API_KEY`
- 触发按钮: `script.js` → `triggerWorkflow()` (打开 Actions 页面)
- 预览面板: `script.js` → `updatePreview()` (含参考来源)
- 帖子卡片: `script.js` → `createPostCard()` (含参考来源)

---

## 10. GitHub Secrets 配置

| Secret | 用途 | 状态 |
|--------|------|------|
| `DEEPSEEK_API_KEY` | DeepSeek API 认证 | ✅ 已配置 |
| `DOUBAO_API_KEY` | 豆包 API（已弃用） | 可删除 |
