# 搜狐自媒体热帖生成器 — 实现计划

> **For agentic workers:** 按任务顺序执行，每步完成后再进行下一步。Steps 使用 checkbox (`- [ ]`) 语法追踪。

**目标：** 搭建一个 GitHub Pages 静态网页 + GitHub Actions 自动化脚本，用户点击按钮即可生成一篇带配图的原创短帖。

**架构：** GitHub Actions（workflow_dispatch 触发 → Python 脚本调 Claude API + Unsplash API → 写入 posts.json → git push）→ GitHub Pages 自动部署 → 用户网页读取 JSON 渲染。

**技术栈：** GitHub Pages + GitHub Actions + Python 3 + Claude API (Haiku) + Unsplash API + 原生 HTML/CSS/JS

---

## 文件地图

```
sohuxw/
├── .github/workflows/
│   └── generate.yml          # Actions 定义: workflow_dispatch + style 参数
├── scripts/
│   └── generate.py            # Python: 调 Claude + Unsplash, 写 posts.json
├── data/
│   └── posts.json             # 初始为 []
├── index.html                 # 页面结构 + 帖子卡片模板
├── style.css                  # 响应式样式, 按钮动画, 卡片效果
├── script.js                  # 前端逻辑: 触发生成/轮询/渲染/复制/删除
├── .gitignore                 # Python 缓存, 密钥文件
└── README.md                  # 仓库说明 + 设置步骤
```

---

### 任务 1: 项目脚手架搭建

**文件:**
- 创建: `.gitignore`
- 创建: `data/posts.json`

- [ ] **步骤 1: 创建 .gitignore**

```bash
# .gitignore
__pycache__/
*.pyc
.env
.venv/
*.egg-info/
dist/
.DS_Store
```

- [ ] **步骤 2: 创建 data/posts.json 初始文件**

```json
[]
```

- [ ] **步骤 3: 创建目录结构**

```bash
mkdir -p .github/workflows scripts data
```

- [ ] **步骤 4: Git 初始化并提交**

```bash
cd d:/AI/souhuxw
git init
git add .gitignore data/posts.json
git commit -m "chore: init project scaffold"
```

---

### 任务 2: GitHub Actions 工作流

**文件:**
- 创建: `.github/workflows/generate.yml`

- [ ] **步骤 1: 编写 generate.yml**

```yaml
name: Generate Post

on:
  workflow_dispatch:
    inputs:
      style:
        description: '帖子风格'
        required: true
        type: choice
        default: 'chatty'
        options:
          - chatty      # 轻松闲聊
          - newsflash   # 一句话快讯

jobs:
  generate:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - name: Checkout repo
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install anthropic requests

      - name: Generate post
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: python scripts/generate.py --style "${{ inputs.style }}"

      - name: Commit and push
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add data/posts.json
          git diff --staged --quiet || git commit -m "feat: add new post [skip ci]"
          git push
```

- [ ] **步骤 2: 提交**

```bash
git add .github/workflows/generate.yml
git commit -m "feat: add GitHub Actions workflow for post generation"
```

---

### 任务 3: Python 内容生成脚本

**文件:**
- 创建: `scripts/generate.py`

- [ ] **步骤 1: 编写 generate.py — 导入和 System Prompt**

```python
"""搜狐热帖生成器 — AI 生成短文 + 自动配图"""
import argparse
import json
import os
import random
import string
from datetime import datetime, timezone, timedelta

import anthropic
import requests

CST = timezone(timedelta(hours=8))

SYSTEM_PROMPT = """你是搜狐新闻自媒体作者"江"，每天发布有营养的原创短内容，不标题党，不博眼球。

你的写作风格由 style 参数决定：
- style=chatty：轻松闲聊型。像跟朋友聊天一样分享一个热点话题。口语化、自然、有个人感受。可使用适当的 emoji。字数控制在150-200字。必须原创，不要以"//@某人"的形式转发。
- style=newsflash：一句话快讯型。用一句简洁的话说清楚一个热点事件的要点。纯事实陈述，不带观点和情绪。字数控制在50-80字。

话题选择：从最近的社会、科技、财经、文娱、生活等领域的广泛热点中选取。不局限于单一领域。

除了文字内容，你还需要输出1-3个英文图片搜索关键词（image_keywords），用于从免费图库为帖子匹配一张相关配图。关键词应该具体、视觉化（如"electric car charging station"而不是"car"）。

输出格式必须是严格的 JSON，不要输出其他内容：
{"content": "帖子正文", "image_keywords": ["keyword1", "keyword2", "keyword3"]}"""


def generate_post_text(style: str) -> dict:
    """调用 Claude API 生成帖子文字和图片关键词"""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"请生成一篇 style={style} 的帖子。"
        }]
    )
    
    raw = message.content[0].text.strip()
    # 提取 JSON（处理可能的 markdown 代码块）
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()
    
    return json.loads(raw)
```

- [ ] **步骤 2: 编写图像搜索函数**

```python
def search_image(keywords: list[str]) -> tuple[str | None, str | None]:
    """用关键词搜索 Unsplash，返回 (image_url, image_credit)"""
    # 尝试每个关键词，取第一个有结果的
    for keyword in keywords:
        url = "https://api.unsplash.com/search/photos"
        params = {
            "query": keyword,
            "per_page": 1,
            "orientation": "landscape"
        }
        # Unsplash 免费版无需 API Key，但有限速。使用演示级 access
        resp = requests.get(
            url,
            params=params,
            headers={"Accept-Version": "v1"},
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            if results:
                photo = results[0]
                image_url = photo["urls"]["regular"]
                credit = f"Photo by {photo['user']['name']} / Unsplash"
                return image_url, credit
    
    return None, None
```

- [ ] **步骤 3: 编写 JSON 文件读写**

```python
POSTS_FILE = "data/posts.json"
MAX_POSTS = 200


def load_posts() -> list[dict]:
    """读取现有帖子"""
    with open(POSTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_posts(posts: list[dict]):
    """写入帖子，保留最近 MAX_POSTS 条"""
    trimmed = posts[:MAX_POSTS]
    with open(POSTS_FILE, "w", encoding="utf-8") as f:
        json.dump(trimmed, f, ensure_ascii=False, indent=2)


def append_post(post: dict):
    """将新帖子插入到数组头部"""
    posts = load_posts()
    posts.insert(0, post)
    save_posts(posts)
```

- [ ] **步骤 4: 编写 main 函数**

```python
def make_post_id() -> str:
    """生成唯一 ID: YYYYMMDD-HHMMSS-随机6位"""
    now = datetime.now(CST)
    ts = now.strftime("%Y%m%d-%H%M%S")
    rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{ts}-{rand}"


def main():
    parser = argparse.ArgumentParser(description="生成一篇搜狐热帖")
    parser.add_argument(
        "--style",
        choices=["chatty", "newsflash"],
        default="chatty",
        help="帖子风格"
    )
    args = parser.parse_args()

    # 1. 生成文字
    result = generate_post_text(args.style)
    content = result["content"]
    keywords = result["image_keywords"]

    # 2. 搜索配图
    image_url, image_credit = search_image(keywords)

    # 3. 组装帖子
    post = {
        "id": make_post_id(),
        "content": content,
        "style": args.style,
        "image_url": image_url,
        "image_credit": image_credit,
        "created_at": datetime.now(CST).isoformat()
    }

    # 4. 写入 JSON
    append_post(post)
    print(f"Generated post: {post['id']}")
    print(f"  style: {args.style}")
    print(f"  content: {content[:60]}...")
    print(f"  image: {image_url or 'none'}")


if __name__ == "__main__":
    main()
```

- [ ] **步骤 5: 本地测试脚本**

```bash
# 测试 chatty 风格
ANTHROPIC_API_KEY=your_key python scripts/generate.py --style chatty

# 测试 newsflash 风格
ANTHROPIC_API_KEY=your_key python scripts/generate.py --style newsflash

# 检查输出
cat data/posts.json | python -m json.tool | head -20
```

- [ ] **步骤 6: 提交**

```bash
git add scripts/generate.py
git commit -m "feat: add Python post generation script"
```

---

### 任务 4: 前端 HTML 页面

**文件:**
- 创建: `index.html`

- [ ] **步骤 1: 编写 index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>搜狐热帖助手</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <!-- 头部 -->
        <header class="header">
            <h1>🔥 搜狐热帖助手</h1>
            <span class="badge">江的助手</span>
        </header>

        <!-- 控制栏 -->
        <div class="controls">
            <div class="style-selector">
                <label class="radio-label">
                    <input type="radio" name="style" value="chatty" checked>
                    <span>💬 闲聊</span>
                </label>
                <label class="radio-label">
                    <input type="radio" name="style" value="newsflash">
                    <span>⚡ 快讯</span>
                </label>
            </div>
            <button id="generate-btn" class="btn-generate">生成一篇 →</button>
            <span id="today-count" class="counter">今日: 0</span>
        </div>

        <!-- 提示信息 -->
        <p id="hint" class="hint hidden">点击生成后请稍等几秒，江 正在为你写稿 ✍️</p>

        <!-- 全局消息 -->
        <div id="message" class="message hidden"></div>

        <!-- 帖子列表 -->
        <main id="post-list" class="post-list">
            <div id="empty-state" class="empty-state">
                暂无帖子，点击上方按钮生成第一条吧~
            </div>
        </main>
    </div>

    <!-- 确认对话框 -->
    <div id="confirm-dialog" class="dialog-overlay hidden">
        <div class="dialog-box">
            <p id="confirm-text">确认删除这条帖子吗？</p>
            <div class="dialog-actions">
                <button id="confirm-cancel" class="btn-cancel">取消</button>
                <button id="confirm-ok" class="btn-danger">确定</button>
            </div>
        </div>
    </div>

    <script src="script.js"></script>
</body>
</html>
```

- [ ] **步骤 2: 提交**

```bash
git add index.html
git commit -m "feat: add HTML page structure"
```

---

### 任务 5: 前端样式 CSS

**文件:**
- 创建: `style.css`

- [ ] **步骤 1: 编写 style.css**

```css
/* === 基础重置 === */
*, *::before, *::after {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
                 "Microsoft YaHei", sans-serif;
    background: #f5f7fa;
    color: #333;
    line-height: 1.6;
    min-height: 100vh;
}

/* === 容器 === */
.container {
    max-width: 640px;
    margin: 0 auto;
    padding: 20px 16px 40px;
}

/* === 头部 === */
.header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 20px;
}
.header h1 {
    font-size: 24px;
    font-weight: 700;
}
.badge {
    font-size: 12px;
    background: #ffeaa7;
    color: #8b6914;
    padding: 2px 10px;
    border-radius: 12px;
    font-weight: 500;
}

/* === 控制栏 === */
.controls {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
    margin-bottom: 8px;
}
.style-selector {
    display: flex;
    gap: 8px;
    background: #fff;
    border-radius: 10px;
    padding: 6px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.radio-label {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 6px 14px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
    transition: background 0.2s;
}
.radio-label:has(input:checked) {
    background: #e8f4fd;
    color: #1a73e8;
    font-weight: 600;
}
.radio-label input {
    display: none;
}

/* === 生成按钮 === */
.btn-generate {
    padding: 12px 24px;
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: #fff;
    border: none;
    border-radius: 10px;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    transition: transform 0.15s, box-shadow 0.15s, opacity 0.2s;
    white-space: nowrap;
}
.btn-generate:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(102,126,234,0.4);
}
.btn-generate:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

/* === 计数器 === */
.counter {
    font-size: 13px;
    color: #888;
    background: #fff;
    padding: 6px 12px;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

/* === 提示文字 === */
.hint {
    color: #999;
    font-size: 13px;
    margin-bottom: 16px;
    transition: opacity 0.3s;
}
.hint.hidden {
    display: none;
}
.hint:not(.hidden) {
    display: block;
}

/* === 全局消息 === */
.message {
    padding: 10px 16px;
    border-radius: 8px;
    margin-bottom: 16px;
    font-size: 14px;
}
.message.hidden {
    display: none;
}
.message.error {
    display: block;
    background: #fff0f0;
    color: #c0392b;
    border: 1px solid #f5c6cb;
}

/* === 帖子列表 === */
.post-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

/* === 帖子卡片 === */
.post-card {
    background: #fff;
    border-radius: 12px;
    padding: 16px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    transition: transform 0.2s, box-shadow 0.2s;
}
.post-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(0,0,0,0.1);
}
.post-card .post-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}
.post-card .post-time {
    font-size: 12px;
    color: #aaa;
}
.post-card .post-actions {
    display: flex;
    gap: 8px;
}
.post-card .btn-action {
    font-size: 12px;
    padding: 4px 12px;
    border-radius: 6px;
    border: 1px solid #ddd;
    background: #fff;
    cursor: pointer;
    transition: all 0.15s;
}
.post-card .btn-action:hover {
    background: #f0f0f0;
}
.post-card .btn-action.copied {
    color: #27ae60;
    border-color: #27ae60;
}
.post-card .btn-action.delete:hover {
    color: #e74c3c;
    border-color: #e74c3c;
    background: #fff5f5;
}
.post-card .post-content {
    font-size: 15px;
    line-height: 1.7;
    white-space: pre-wrap;
    word-break: break-word;
}

/* === 配图 === */
.post-card .post-image {
    margin-top: 12px;
    border-radius: 8px;
    overflow: hidden;
}
.post-card .post-image img {
    width: 100%;
    max-height: 240px;
    object-fit: cover;
    display: block;
    cursor: pointer;
}
.post-card .post-image figcaption {
    font-size: 11px;
    color: #bbb;
    text-align: right;
    padding: 4px 8px 0;
}

/* === 空状态 === */
.empty-state {
    text-align: center;
    color: #bbb;
    padding: 60px 20px;
    font-size: 15px;
}

/* === 确认对话框 === */
.dialog-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.4);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
}
.dialog-overlay.hidden {
    display: none;
}
.dialog-box {
    background: #fff;
    border-radius: 14px;
    padding: 24px;
    width: 300px;
    text-align: center;
}
.dialog-box p {
    font-size: 15px;
    margin-bottom: 20px;
    color: #555;
}
.dialog-actions {
    display: flex;
    gap: 10px;
    justify-content: center;
}
.btn-cancel, .btn-danger {
    padding: 8px 24px;
    border-radius: 8px;
    font-size: 14px;
    cursor: pointer;
    border: 1px solid #ddd;
    background: #fff;
}
.btn-danger {
    background: #e74c3c;
    color: #fff;
    border-color: #e74c3c;
}

/* === 响应式: 手机 === */
@media (max-width: 480px) {
    .container {
        padding: 12px 10px 32px;
    }
    .header h1 {
        font-size: 20px;
    }
    .controls {
        gap: 8px;
    }
    .btn-generate {
        padding: 10px 18px;
        font-size: 14px;
    }
    .post-card .post-content {
        font-size: 14px;
    }
}
```

- [ ] **步骤 2: 提交**

```bash
git add style.css
git commit -m "feat: add responsive CSS styles"
```

---

### 任务 6: 前端 JavaScript 逻辑

**文件:**
- 创建: `script.js`

- [ ] **步骤 1: 编写 script.js — 配置和初始化**

```javascript
// === 配置 ===
const REPO_OWNER = 'YOUR_USERNAME';    // 替换为 GitHub 用户名
const REPO_NAME = 'sohuxw';            // 替换为仓库名
const GH_PAT = 'YOUR_PAT_TOKEN';       // GitHub Fine-grained PAT (仅 actions:write 权限)
const WORKFLOW_ID = 'generate.yml';
const POSTS_URL = 'data/posts.json';
const POLL_INTERVAL = 5000;            // 轮询间隔 5 秒
const POLL_TIMEOUT = 60000;            // 总超时 60 秒

// === DOM 元素 ===
const generateBtn = document.getElementById('generate-btn');
const postList = document.getElementById('post-list');
const emptyState = document.getElementById('empty-state');
const hint = document.getElementById('hint');
const message = document.getElementById('message');
const todayCount = document.getElementById('today-count');
const confirmDialog = document.getElementById('confirm-dialog');
const confirmText = document.getElementById('confirm-text');
const confirmOk = document.getElementById('confirm-ok');
const confirmCancel = document.getElementById('confirm-cancel');

// === 状态 ===
let isGenerating = false;
let pollTimer = null;
let pendingDeleteId = null;
```

- [ ] **步骤 2: 工具函数 — localStorage 删除管理**

```javascript
function getDeletedIds() {
    try {
        return JSON.parse(localStorage.getItem('sohu_deleted_posts') || '[]');
    } catch {
        return [];
    }
}

function addDeletedId(id) {
    const ids = getDeletedIds();
    ids.push(id);
    // 只保留最近 500 条
    const trimmed = ids.slice(-500);
    localStorage.setItem('sohu_deleted_posts', JSON.stringify(trimmed));
}

function getStyle() {
    const checked = document.querySelector('input[name="style"]:checked');
    return checked ? checked.value : 'chatty';
}

function showMessage(text, type) {
    message.textContent = text;
    message.className = `message ${type}`;
}

function hideMessage() {
    message.className = 'message hidden';
}

function updateTodayCount() {
    const cards = postList.querySelectorAll('.post-card');
    const today = new Date().toDateString();
    let count = 0;
    cards.forEach(card => {
        if (card.dataset.date === today) count++;
    });
    todayCount.textContent = `今日: ${count}`;
}
```

- [ ] **步骤 3: 渲染帖子列表**

```javascript
async function loadAndRender() {
    try {
        const resp = await fetch(POSTS_URL);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const posts = await resp.json();

        const deletedIds = getDeletedIds();
        // 过滤已删除
        const visible = posts.filter(p => !deletedIds.includes(p.id));

        if (visible.length === 0) {
            postList.innerHTML = '';
            postList.appendChild(emptyState);
            emptyState.classList.remove('hidden');
        } else {
            emptyState.classList.add('hidden');
            postList.innerHTML = '';
            visible.forEach(post => {
                postList.appendChild(createPostCard(post));
            });
        }
        updateTodayCount();
        hideMessage();
    } catch (err) {
        if (postList.children.length === 0 || 
            (postList.children.length === 1 && postList.children[0] === emptyState)) {
            emptyState.textContent = '内容加载失败，请手动刷新页面';
            emptyState.classList.remove('hidden');
        }
    }
}

function createPostCard(post) {
    const card = document.createElement('div');
    card.className = 'post-card';
    card.dataset.id = post.id;
    card.dataset.date = new Date(post.created_at).toDateString();

    const timeStr = new Date(post.created_at).toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit'
    });

    let imageHTML = '';
    if (post.image_url) {
        imageHTML = `
            <figure class="post-image">
                <img src="${escapeHTML(post.image_url)}" 
                     alt="配图" 
                     loading="lazy"
                     onclick="window.open('${escapeHTML(post.image_url)}', '_blank')">
                <figcaption>${escapeHTML(post.image_credit || '')}</figcaption>
            </figure>`;
    }

    card.innerHTML = `
        <div class="post-header">
            <span class="post-time">🕐 ${timeStr}</span>
            <div class="post-actions">
                <button class="btn-action copy-btn">复制</button>
                <button class="btn-action delete-btn">删除</button>
            </div>
        </div>
        <div class="post-content">${escapeHTML(post.content)}</div>
        ${imageHTML}
    `;

    // 绑定复制
    card.querySelector('.copy-btn').addEventListener('click', () => {
        copyPost(post.content, card.querySelector('.copy-btn'));
    });

    // 绑定删除
    card.querySelector('.delete-btn').addEventListener('click', () => {
        showDeleteConfirm(post.id, card);
    });

    return card;
}

function escapeHTML(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
```

- [ ] **步骤 4: 复制功能**

```javascript
async function copyPost(text, btn) {
    try {
        await navigator.clipboard.writeText(text);
        btn.textContent = '✅ 已复制';
        btn.classList.add('copied');
        setTimeout(() => {
            btn.textContent = '复制';
            btn.classList.remove('copied');
        }, 1500);
    } catch {
        // 降级方案
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        btn.textContent = '✅ 已复制';
        btn.classList.add('copied');
        setTimeout(() => {
            btn.textContent = '复制';
            btn.classList.remove('copied');
        }, 1500);
    }
}
```

- [ ] **步骤 5: 删除功能**

```javascript
function showDeleteConfirm(id, card) {
    pendingDeleteId = id;
    // 保存 card 引用到对话框
    confirmDialog._targetCard = card;
    confirmDialog.classList.remove('hidden');
}

function hideDeleteConfirm() {
    confirmDialog.classList.add('hidden');
    pendingDeleteId = null;
    confirmDialog._targetCard = null;
}

function executeDelete() {
    if (!pendingDeleteId) return;
    addDeletedId(pendingDeleteId);
    if (confirmDialog._targetCard) {
        confirmDialog._targetCard.remove();
    }
    hideDeleteConfirm();
    updateTodayCount();

    // 如果列表变空，显示空状态
    if (postList.querySelectorAll('.post-card').length === 0) {
        postList.appendChild(emptyState);
        emptyState.classList.remove('hidden');
    }
}

confirmOk.addEventListener('click', executeDelete);
confirmCancel.addEventListener('click', hideDeleteConfirm);
```

- [ ] **步骤 6: 触发生成 — 调用 GitHub API**

```javascript
async function triggerWorkflow() {
    if (isGenerating) return;

    const style = getStyle();
    isGenerating = true;
    generateBtn.disabled = true;
    generateBtn.textContent = '生成中...';
    hint.classList.remove('hidden');
    hideMessage();

    try {
        // 记录触发生成前的最新帖子 ID，用于轮询检测新帖
        const beforeResp = await fetch(POSTS_URL);
        const beforePosts = beforeResp.ok ? await beforeResp.json() : [];
        const latestIdBefore = beforePosts.length > 0 ? beforePosts[0].id : null;

        const apiUrl = `https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/actions/workflows/${WORKFLOW_ID}/dispatches`;
        const resp = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${GH_PAT}`,
                'Accept': 'application/vnd.github+json',
            },
            body: JSON.stringify({ ref: 'main', inputs: { style: style } })
        });

        if (!resp.ok && resp.status !== 204) {
            throw new Error(`GitHub API 返回 ${resp.status}`);
        }

        // 开始轮询
        startPolling(latestIdBefore);
    } catch (err) {
        showMessage('生成失败，请稍后重试', 'error');
        resetGenerateButton();
    }
}

function resetGenerateButton() {
    isGenerating = false;
    generateBtn.disabled = false;
    generateBtn.textContent = '生成一篇 →';
    hint.classList.add('hidden');
    if (pollTimer) {
        clearTimeout(pollTimer);
        pollTimer = null;
    }
}

function startPolling(latestIdBefore) {
    const startTime = Date.now();

    async function poll() {
        // 超时检查
        if (Date.now() - startTime > POLL_TIMEOUT) {
            showMessage('响应超时，请重试', 'error');
            resetGenerateButton();
            return;
        }

        try {
            const resp = await fetch(POSTS_URL + '?t=' + Date.now()); // 破缓存
            if (resp.ok) {
                const posts = await resp.json();
                if (posts.length > 0 && posts[0].id !== latestIdBefore) {
                    // 检测到新帖子
                    await loadAndRender();
                    // 滚动到顶部看新帖
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                    resetGenerateButton();
                    return;
                }
            }
        } catch {
            // 网络错误，继续轮询
        }

        pollTimer = setTimeout(poll, POLL_INTERVAL);
    }

    poll();
}

generateBtn.addEventListener('click', triggerWorkflow);
```

- [ ] **步骤 7: 页面初始化**

```javascript
// 页面加载
loadAndRender();

// 定期刷新（每 30 秒检查是否有其他人/设备生成了新帖）
setInterval(loadAndRender, 30000);
```

- [ ] **步骤 8: 提交**

```bash
git add script.js
git commit -m "feat: add frontend JavaScript logic"
```

---

### 任务 7: README 文档

**文件:**
- 创建: `README.md`

- [ ] **步骤 1: 编写 README.md**

```markdown
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
- 名称: `ANTHROPIC_API_KEY`
- 值: 你的 Anthropic API Key

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
- Claude API (Haiku) 生成文字
- Unsplash API 搜索配图
```

- [ ] **步骤 2: 提交**

```bash
git add README.md
git commit -m "docs: add README"
```

---

### 任务 8: 推送到 GitHub 并配置

- [ ] **步骤 1: 创建 GitHub 仓库**

在 GitHub 上创建新仓库 `sohuxw`（Public）。

- [ ] **步骤 2: 推送代码**

```bash
git remote add origin https://github.com/YOUR_USERNAME/sohuxw.git
git branch -M main
git push -u origin main
```

- [ ] **步骤 3: 创建 GitHub Personal Access Token**

GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token:
- Repository access: `Only select repositories` → 选择 `sohuxw`
- Permissions: `Actions` → Access: `Read and write`
- 生成后复制 token（关闭页面后不可再见）

- [ ] **步骤 4: 更新 script.js 配置**

编辑 `script.js`，将顶部三个占位符替换为实际值：
```javascript
const REPO_OWNER = '你的GitHub用户名';
const REPO_NAME = 'sohuxw';
const GH_PAT = '步骤3生成的PAT';
```

提交并推送：
```bash
git add script.js
git commit -m "config: set repo info and PAT"
git push
```

> ⚠️ 注意：此 PAT 将出现在网页源码中（F12 可见）。已限定为仅 actions:write 权限 + 单仓库，他人顶多触发你的生成动作。这是公开仓库 + 免费 Pages 的权衡。介意可改为私有仓库（需付费）。

- [ ] **步骤 5: 配置 Secrets**

GitHub → 仓库 Settings → Secrets and variables → Actions → New repository secret:
- Name: `ANTHROPIC_API_KEY`
- Value: 你的 Anthropic API Key

- [ ] **步骤 6: 启用 Pages**

Settings → Pages → Source → "Deploy from a branch" → Branch: `main`, folder: `/ (root)` → Save.
等待 1-2 分钟，Pages 部署完成后显示网址。

- [ ] **步骤 7: 验证**

1. 打开 `https://YOUR_USERNAME.github.io/sohuxw/`
2. 确认页面正常加载，显示空状态
3. 点「生成一篇」，等待 Actions 完成
4. 确认新帖子出现在列表中
5. 测试复制按钮
6. 测试删除确认

---

## 验证清单

| 测试项 | 预期行为 |
|--------|---------|
| 页面初次加载 | 显示空状态"暂无帖子" |
| 点「生成一篇」(闲聊) | 按钮禁用 → 显示提示文字 → 15-60s 后新帖出现在顶部 |
| 点「生成一篇」(快讯) | 同上，风格为 newsflash |
| 生成中再次点击 | 按钮禁用，无法触发第二次 |
| 帖子带配图 | 帖子底部显示缩略图 + 署名 |
| 点「复制」 | 按钮变"✅ 已复制"，1.5s 后恢复 |
| 点「删除」 | 弹出确认框 → 确定后帖子消失 |
| 刷新页面后已删帖 | 不出现 |
| 手机端打开 | 布局自适应，卡片全宽 |
| posts.json 空数组 | 页面显示空状态 |
| GitHub Actions 执行失败 | 页面显示红色错误提示 |
| 无网络打开页面 | 显示加载失败提示 |
