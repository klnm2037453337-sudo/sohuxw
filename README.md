# 🔥 搜狐热帖助手

每天帮你生成有营养的原创短帖子，复制后搬运到搜狐新闻发布。

## 使用方法

1. 打开网址: `https://YOUR_USERNAME.github.io/sohuxw/`
2. 选择风格（闲聊 / 快讯）
3. 点「生成一篇」
4. 等 15-60 秒，新帖子出现在列表中
5. 点「复制」→ 去搜狐新闻发布

## 首次设置

### 1. Fork 或创建此仓库到你的 GitHub

### 2. 创建 GitHub Personal Access Token (PAT)
Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token:
- Repository access: 仅选择 `sohuxw` 仓库
- Permissions: `Actions` → Read and write
- 生成后复制 token（只显示一次！）

### 3. 设置 Secrets
仓库 Settings → Secrets and variables → Actions → New repository secret:
- 名称: `DEEPSEEK_API_KEY`
- 值: 你的 DeepSeek API Key

### 4. 修改 script.js 中的配置
```javascript
const REPO_OWNER = '你的GitHub用户名';
const REPO_NAME = 'sohuxw';
const GH_PAT = '步骤2生成的PAT';
```

> ⚠️ **安全说明：** PAT 写在 script.js 中，理论上查看网页源码的人可以看到。但 PAT 已限定为仅 `actions:write` 权限 + 仅此仓库，他人最多只能触发你的生成动作（消耗约 ¥0.01/次）。仓库保持公开是为了使用免费 GitHub Pages。如介意，可将仓库改为私有（需 GitHub 付费方案）。

### 5. 启用 GitHub Pages
Settings → Pages → Source: Deploy from a branch → Branch: main, / (root) → Save

### 6. 启用 Actions 权限
Settings → Actions → General → Workflow permissions → 选 "Read and write permissions" → Save

## 技术栈
- GitHub Pages（静态托管）
- GitHub Actions（云端执行）
- DeepSeek API 生成文字
- Unsplash API 搜索配图
