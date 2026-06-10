# 搜狐热帖助手 — 内容与视觉重设计 实现计划

> **For agentic workers:** 按任务顺序实现，每步完成后验证。Steps 使用 checkbox (`- [ ]`) 语法追踪。

**Goal:** 将页面从 2 种风格的简单表单重设计为 12 种类型 × 5 档字数的云海场景页面，含实时预览和横向滚动栏。

**Architecture:** 纯静态前端（HTML+CSS+JS）+ GitHub Actions 后端触发。前端单页应用，CSS 绘制场景背景，JS 管理交互状态。后端 Python 脚本接收新参数调用 DeepSeek API。

**Tech Stack:** HTML5, CSS3, Vanilla JS, GitHub Actions, Python 3.11, DeepSeek API, trafilatura

**优先级:** 前端（Task 1-7）先做，后端（Task 8-9）后做，内容质量（Task 10）最后。

---

## 文件结构

| 文件 | 操作 | 职责 |
|------|------|------|
| index.html | 重写 | 页面结构：场景容器 + 操作面板 + 预览面板 + 滚动栏 + 帖子列表 + 弹窗 |
| style.css | 重写 | 所有样式：场景背景、毛玻璃面板、组件、响应式、动画 |
| script.js | 重写 | 所有交互：分类切换、选择状态、API 触发、轮询、预览、滚动、复制/删除 |
| .github/workflows/generate.yml | 修改 | 新增 genre / word_count / source_url 参数 |
| scripts/generate.py | 修改 | 新 System Prompt + trafilatura + 新参数解析 |

---

### Task 1: 重写 index.html 页面结构

**Files:**
- Rewrite: `index.html`

- [ ] **Step 1: 写入新 HTML 结构**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>内容助手</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <!-- 场景背景层 -->
    <div class="scene">
        <div class="scene-sky"></div>
        <div class="scene-sun"></div>
        <div class="clouds">
            <div class="cloud c1"></div>
            <div class="cloud c2"></div>
            <div class="cloud c3"></div>
            <div class="cloud c4"></div>
            <div class="cloud c5"></div>
            <div class="cloud c6"></div>
            <div class="cloud c7"></div>
        </div>
        <div class="scene-horizon"></div>
        <div class="scene-island">
            <div class="island-hill"></div>
            <div class="island-highlight"></div>
            <div class="cabin">
                <div class="cabin-roof"></div>
                <div class="cabin-body"><div class="cabin-window"></div></div>
            </div>
            <div class="pole p1"></div>
            <div class="pole p2"></div>
            <div class="wire"></div>
            <div class="grass g1"></div>
            <div class="grass g2"></div>
            <div class="grass g3"></div>
        </div>
    </div>

    <!-- 主内容 -->
    <div class="main-content">
        <!-- 首屏：操作面板 + 预览 + 滚动栏 -->
        <section class="hero">
            <div class="hero-inner">
                <!-- 左：操作面板 -->
                <div class="panel">
                    <div class="panel-header">
                        <h1 class="panel-title">内容助手</h1>
                        <p class="panel-subtitle">选个方向，江帮你写</p>
                    </div>

                    <!-- 分类标签 -->
                    <div class="category-tabs" id="category-tabs">
                        <!-- JS 动态生成 -->
                    </div>

                    <!-- 子类型标签 -->
                    <div class="genre-pills" id="genre-pills">
                        <!-- JS 动态生成 -->
                    </div>

                    <div class="panel-divider"></div>

                    <!-- 字数选择 -->
                    <div class="wordcount-row">
                        <span class="row-label">字数</span>
                        <div class="wordcount-pills" id="wordcount-pills">
                            <!-- JS 动态生成 -->
                        </div>
                    </div>

                    <!-- 链接输入 + 生成按钮 -->
                    <div class="input-row">
                        <input type="url" id="source-url"
                               placeholder="🔗 粘贴新闻链接（选填，留空则AI自由选题）"
                               class="url-input">
                        <button id="generate-btn" class="btn-generate">生成 →</button>
                    </div>
                </div>

                <!-- 右：预览面板 -->
                <div class="preview" id="preview-panel">
                    <div class="preview-header">✨ 本次生成预览</div>
                    <div class="preview-body" id="preview-body">
                        <div class="preview-placeholder">
                            <div class="preview-icon">📝</div>
                            <p>点击左侧「生成」按钮<br/>内容将在这里显示</p>
                        </div>
                    </div>
                    <div class="preview-footer">
                        <button class="btn-copy-preview" id="btn-copy-preview" disabled>一键复制</button>
                    </div>
                </div>
            </div>

            <!-- 底部横向滚动栏 -->
            <div class="scroll-strip">
                <div class="scroll-strip-title">过去生成</div>
                <div class="scroll-strip-row">
                    <button class="scroll-btn scroll-left" id="scroll-left" aria-label="向左滚动">◂</button>
                    <div class="scroll-track" id="scroll-track">
                        <!-- JS 动态填充缩略卡片 -->
                    </div>
                    <button class="scroll-btn scroll-right" id="scroll-right" aria-label="向右滚动">▸</button>
                </div>
            </div>
        </section>

        <!-- 首屏以下：帖子网格 -->
        <section class="post-grid-section">
            <div class="section-divider">
                <span>全部帖子</span>
            </div>
            <div class="post-grid" id="post-grid">
                <!-- JS 动态填充 -->
            </div>
            <div id="empty-state" class="empty-state hidden">
                暂无帖子，点击上方按钮生成第一条吧~
            </div>
        </section>

        <!-- 页脚 -->
        <footer class="page-footer">
            江 正在为你写稿 ✍️
        </footer>
    </div>

    <!-- 帖子详情弹窗 -->
    <div class="modal-overlay hidden" id="modal-overlay">
        <div class="modal-box" id="modal-box">
            <!-- JS 动态填充 -->
        </div>
    </div>

    <!-- 确认删除对话框 -->
    <div class="dialog-overlay hidden" id="confirm-dialog">
        <div class="dialog-box">
            <p>确认删除这条帖子吗？</p>
            <div class="dialog-actions">
                <button id="confirm-cancel" class="btn-cancel">取消</button>
                <button id="confirm-ok" class="btn-danger">确定</button>
            </div>
        </div>
    </div>

    <!-- 生成中状态提示 -->
    <div class="toast hidden" id="toast"></div>

    <script src="script.js"></script>
</body>
</html>
```

- [ ] **Step 2: 验证 HTML 结构完整**

在浏览器中打开 index.html，确认无 JS 错误，元素齐全。

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "feat: rewrite HTML with new scene+panel+preview+scrollstrip structure"
```

---

### Task 2: 重写 style.css — 场景背景

**Files:**
- Rewrite: `style.css`

- [ ] **Step 1: 写入 CSS Reset + 场景背景样式**

```css
/* === Reset === */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
                 "Microsoft YaHei", sans-serif;
    color: #5c4a3a;
    line-height: 1.6;
    min-height: 100vh;
    overflow-x: hidden;
}

/* === 场景容器 === */
.scene {
    position: fixed;
    inset: 0;
    z-index: 0;
    pointer-events: none;
    overflow: hidden;
}

/* 天空渐变 */
.scene-sky {
    position: absolute;
    inset: 0;
    background: linear-gradient(180deg,
        #b8d4e3 0%, #dce8f0 15%, #f0e8d8 40%,
        #e8dcc8 55%, #d5c4a8 70%, #c4b090 100%);
}

/* 太阳光晕 */
.scene-sun {
    position: absolute;
    top: 30px;
    left: 50%;
    transform: translateX(-50%);
    width: 350px;
    height: 350px;
    background: radial-gradient(ellipse,
        rgba(255,240,220,0.7), rgba(255,220,180,0.3), transparent 70%);
    border-radius: 50%;
}

/* 云层 */
.cloud {
    position: absolute;
    background: rgba(255,255,255,0.45);
    border-radius: 50%;
}
.cloud.c1 { top: 40px; left: 8%; width: 220px; height: 50px; filter: blur(8px); background: rgba(255,255,255,0.5); }
.cloud.c2 { top: 55px; left: 28%; width: 300px; height: 48px; filter: blur(10px); }
.cloud.c3 { top: 35px; left: 52%; width: 260px; height: 55px; filter: blur(8px); background: rgba(255,255,255,0.5); }
.cloud.c4 { top: 50px; left: 75%; width: 200px; height: 45px; filter: blur(10px); background: rgba(255,255,255,0.4); }
.cloud.c5 { top: 100px; left: 12%; width: 320px; height: 50px; filter: blur(12px); background: rgba(255,255,255,0.35); }
.cloud.c6 { top: 110px; left: 45%; width: 340px; height: 48px; filter: blur(10px); background: rgba(255,255,255,0.35); }
.cloud.c7 { top: 95px; left: 72%; width: 240px; height: 42px; filter: blur(12px); background: rgba(255,255,255,0.3); }

/* 远景树线 */
.scene-horizon {
    position: absolute;
    top: 210px;
    left: 0;
    right: 0;
    height: 60px;
    background: linear-gradient(180deg,
        transparent, rgba(150,170,150,0.18), rgba(160,150,130,0.22));
}

/* 草坡岛屿 */
.scene-island {
    position: absolute;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 88%;
    max-width: 850px;
    height: 170px;
}
.island-hill {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 150px;
    background: linear-gradient(180deg,
        rgba(160,190,140,0.48), rgba(120,150,100,0.58));
    border-radius: 50% 50% 0 0 / 70% 70% 0 0;
}
.island-highlight {
    position: absolute;
    bottom: 15px;
    left: 10%;
    width: 50%;
    height: 110px;
    background: linear-gradient(180deg, rgba(180,210,150,0.28), transparent);
    border-radius: 40% 0 0 0;
}

/* 小木屋 */
.cabin {
    position: absolute;
    bottom: 108px;
    left: 50%;
    transform: translateX(-50%);
    margin-left: -80px;
}
.cabin-roof {
    width: 36px;
    height: 18px;
    background: #8b5a3b;
    clip-path: polygon(50% 0%, 0% 100%, 100% 100%);
    margin: 0 auto;
}
.cabin-body {
    width: 30px;
    height: 22px;
    background: #c4956b;
    border-radius: 0 0 3px 3px;
    margin: 0 auto;
    position: relative;
}
.cabin-window {
    position: absolute;
    top: 5px;
    left: 50%;
    transform: translateX(-50%);
    width: 7px;
    height: 7px;
    background: #f5e6d0;
    border-radius: 1px;
}

/* 电线杆 */
.pole {
    position: absolute;
    width: 3px;
    background: #6b5b4b;
    bottom: 105px;
}
.pole.p1 { left: 50%; margin-left: -145px; height: 55px; }
.pole.p2 { left: 50%; margin-left: -40px; height: 42px; }

/* 电线 */
.wire {
    position: absolute;
    bottom: 155px;
    left: 50%;
    margin-left: -143px;
    width: 106px;
    height: 1px;
    background: rgba(80,70,60,0.32);
    transform: rotate(-2.5deg);
    transform-origin: left;
}

/* 小草 */
.grass {
    position: absolute;
    font-size: 8px;
    color: #7a9a5a;
    bottom: 130px;
}
.grass.g1 { left: 50%; margin-left: -40px; }
.grass.g2 { left: 50%; margin-left: 50px; font-size: 6px; color: #8aaa6a; }
.grass.g3 { left: 50%; margin-left: -105px; font-size: 7px; }
.grass::before { content: "⸻"; }
```

- [ ] **Step 2: 验证场景渲染**

在浏览器中打开 index.html，确认场景背景完整显示（天空、云层、草坡、木屋、电线杆）。

- [ ] **Step 3: Commit**

```bash
git add style.css
git commit -m "style: add scene background with cloud sea and grass island"
```

---

### Task 3: 重写 style.css — 面板与组件样式

**Files:**
- Modify: `style.css` (追加内容)

- [ ] **Step 1: 追加主布局和面板样式**

在 style.css 末尾追加：

```css
/* === 主内容层 === */
.main-content {
    position: relative;
    z-index: 10;
    max-width: 1200px;
    margin: 0 auto;
    padding: 24px 32px;
    pointer-events: auto;
}

/* === 首屏 === */
.hero {
    min-height: calc(100vh - 48px);
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding-bottom: 80px;
}

.hero-inner {
    display: flex;
    gap: 16px;
    align-items: stretch;
    flex: 1;
    margin-bottom: 20px;
}

/* === 操作面板 === */
.panel {
    width: 440px;
    flex-shrink: 0;
    background: rgba(255,255,255,0.5);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border-radius: 20px;
    padding: 28px 26px 24px;
    border: 1px solid rgba(255,255,255,0.55);
    box-shadow: 0 8px 50px rgba(100,80,60,0.08);
    align-self: flex-start;
}

.panel-header {
    text-align: center;
    margin-bottom: 20px;
}
.panel-title {
    font-size: 18px;
    font-weight: 700;
    letter-spacing: 2px;
    color: #5c4a3a;
}
.panel-subtitle {
    font-size: 10px;
    color: #a08870;
    letter-spacing: 1px;
    margin-top: 4px;
}

.panel-divider {
    border-top: 1px solid rgba(180,140,100,0.15);
    margin: 12px 0;
}

/* === 分类标签 === */
.category-tabs {
    display: flex;
    gap: 5px;
    justify-content: center;
    margin-bottom: 10px;
}
.cat-tab {
    padding: 5px 16px;
    border-radius: 14px;
    font-size: 10px;
    cursor: pointer;
    transition: all 0.2s;
    background: rgba(255,255,255,0.35);
    color: #8b7355;
    border: none;
    user-select: none;
}
.cat-tab.active {
    background: rgba(180,140,100,0.25);
    color: #6b4e2a;
    font-weight: 600;
}

/* === 子类型 pills === */
.genre-pills {
    display: flex;
    gap: 5px;
    flex-wrap: wrap;
    justify-content: center;
    margin-bottom: 10px;
}
.genre-pill {
    padding: 5px 16px;
    border-radius: 14px;
    font-size: 10px;
    cursor: pointer;
    transition: all 0.2s;
    background: rgba(255,255,255,0.3);
    color: #8b7355;
    border: 1px solid transparent;
    position: relative;
    user-select: none;
}
.genre-pill.active {
    background: rgba(180,140,100,0.3);
    color: #5c3a1a;
    font-weight: 600;
    border-color: rgba(180,140,100,0.35);
}
.genre-pill:hover:not(.active) {
    background: rgba(255,255,255,0.45);
}

/* Hover 提示气泡 */
.genre-pill::after {
    content: attr(data-tip);
    position: absolute;
    bottom: calc(100% + 8px);
    left: 50%;
    transform: translateX(-50%);
    background: rgba(60,45,30,0.85);
    color: #f0e8d8;
    padding: 6px 12px;
    border-radius: 8px;
    font-size: 9px;
    white-space: nowrap;
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.2s;
    z-index: 20;
}
.genre-pill:hover::after {
    opacity: 1;
}

/* === 字数 pills === */
.wordcount-row {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
    justify-content: center;
}
.row-label {
    font-size: 9px;
    color: #8b7355;
    letter-spacing: 2px;
}
.wordcount-pills {
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
}
.wc-pill {
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 9px;
    cursor: pointer;
    transition: all 0.2s;
    background: rgba(255,255,255,0.3);
    color: #8b7355;
    border: none;
    user-select: none;
}
.wc-pill.active {
    background: rgba(180,140,100,0.3);
    color: #5c3a1a;
    font-weight: 600;
}

/* === 链接输入 + 按钮行 === */
.input-row {
    display: flex;
    gap: 8px;
    align-items: center;
}
.url-input {
    flex: 1;
    background: rgba(255,255,255,0.45);
    color: #5c4a3a;
    border: 1px solid rgba(180,140,100,0.2);
    padding: 10px 14px;
    border-radius: 12px;
    font-size: 10px;
    outline: none;
    transition: border-color 0.2s;
}
.url-input:focus {
    border-color: rgba(180,140,100,0.4);
}
.url-input::placeholder {
    color: #c4b5a5;
}

.btn-generate {
    padding: 10px 22px;
    background: linear-gradient(135deg, rgba(180,140,100,0.7), rgba(140,100,60,0.7));
    color: #fff;
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 12px;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 2px;
    cursor: pointer;
    white-space: nowrap;
    transition: all 0.2s;
    backdrop-filter: blur(10px);
}
.btn-generate:hover:not(:disabled) {
    background: linear-gradient(135deg, rgba(180,140,100,0.85), rgba(140,100,60,0.85));
    box-shadow: 0 4px 16px rgba(139,105,20,0.2);
}
.btn-generate:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}
```

- [ ] **Step 2: Commit**

```bash
git add style.css
git commit -m "style: add panel, pills, input and button component styles"
```

---

### Task 4: 重写 style.css — 预览面板 + 滚动栏 + 帖子网格 + 弹窗 + 响应式

**Files:**
- Modify: `style.css` (追加内容)

- [ ] **Step 1: 追加预览面板、滚动栏、帖子、弹窗、响应式样式**

在 style.css 末尾追加：

```css
/* === 预览面板 === */
.preview {
    flex: 1;
    min-width: 0;
    background: rgba(255,255,255,0.4);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    border-radius: 20px;
    padding: 22px 18px;
    border: 1px solid rgba(255,255,255,0.45);
    box-shadow: 0 4px 30px rgba(100,80,60,0.06);
    display: flex;
    flex-direction: column;
    align-self: flex-start;
    min-height: 380px;
}
.preview-header {
    text-align: center;
    font-size: 10px;
    color: #a08870;
    letter-spacing: 1px;
    margin-bottom: 10px;
}
.preview-body {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
}
.preview-placeholder {
    text-align: center;
    color: #c4b5a5;
}
.preview-icon { font-size: 28px; margin-bottom: 8px; }
.preview-placeholder p { font-size: 11px; line-height: 1.6; }
.preview-content {
    font-size: 14px;
    line-height: 1.8;
    color: #5c4a3a;
    white-space: pre-wrap;
    word-break: break-word;
    width: 100%;
    max-height: 260px;
    overflow-y: auto;
}
.preview-footer {
    text-align: center;
    margin-top: 8px;
}
.btn-copy-preview {
    padding: 4px 18px;
    border-radius: 10px;
    font-size: 9px;
    cursor: pointer;
    background: rgba(180,140,100,0.12);
    color: #8b7355;
    border: 1px solid rgba(180,140,100,0.2);
    transition: all 0.2s;
}
.btn-copy-preview:hover:not(:disabled) {
    background: rgba(180,140,100,0.25);
}
.btn-copy-preview:disabled {
    opacity: 0.4;
    cursor: not-allowed;
}

/* === 底部横向滚动栏 === */
.scroll-strip {
    margin-top: auto;
}
.scroll-strip-title {
    text-align: center;
    font-size: 9px;
    color: rgba(100,80,60,0.45);
    letter-spacing: 2px;
    margin-bottom: 8px;
}
.scroll-strip-row {
    display: flex;
    align-items: center;
    gap: 8px;
}
.scroll-btn {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    background: rgba(255,255,255,0.45);
    border: 1px solid rgba(255,255,255,0.5);
    cursor: pointer;
    color: #8b7355;
    font-size: 12px;
    backdrop-filter: blur(8px);
    transition: background 0.2s;
}
.scroll-btn:hover {
    background: rgba(255,255,255,0.6);
}
.scroll-track {
    flex: 1;
    display: flex;
    gap: 10px;
    overflow-x: auto;
    padding-bottom: 6px;
    scroll-snap-type: x mandatory;
    scroll-behavior: smooth;
    -webkit-overflow-scrolling: touch;
}
.scroll-track::-webkit-scrollbar { display: none; }

/* 缩略卡片 */
.thumb-card {
    min-width: 145px;
    height: 82px;
    background: rgba(255,255,255,0.4);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border-radius: 12px;
    padding: 10px;
    scroll-snap-align: start;
    border: 1px solid rgba(255,255,255,0.45);
    flex-shrink: 0;
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
}
.thumb-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(100,80,60,0.1);
}
.thumb-card .thumb-time {
    font-size: 8px;
    color: #a08870;
}
.thumb-card .thumb-text {
    font-size: 9px;
    color: #5c4a3a;
    line-height: 1.5;
    margin-top: 5px;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

/* === 帖子网格 === */
.post-grid-section {
    margin-top: 40px;
}
.section-divider {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 20px;
}
.section-divider::before,
.section-divider::after {
    content: "";
    flex: 1;
    border-top: 1px solid rgba(180,140,100,0.2);
}
.section-divider span {
    font-size: 10px;
    color: #a08870;
    letter-spacing: 2px;
}
.post-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 12px;
}
.post-card {
    background: linear-gradient(135deg, rgba(253,250,245,0.9), rgba(249,244,236,0.9));
    backdrop-filter: blur(10px);
    border-radius: 12px;
    padding: 18px;
    border: 1px solid rgba(180,140,100,0.15);
    transition: transform 0.2s, box-shadow 0.2s;
}
.post-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(100,80,60,0.08);
}
.post-card .post-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}
.post-card .post-meta {
    display: flex;
    align-items: center;
    gap: 8px;
}
.post-card .post-time {
    font-size: 9px;
    color: #a08870;
}
.post-card .post-genre {
    font-size: 8px;
    background: rgba(180,140,100,0.1);
    color: #8b6914;
    padding: 2px 8px;
    border-radius: 8px;
}
.post-card .post-content {
    font-size: 13px;
    line-height: 1.8;
    color: #5c4a3a;
    white-space: pre-wrap;
    word-break: break-word;
    margin-bottom: 12px;
}
.post-card .post-actions {
    display: flex;
    gap: 6px;
}
.post-card .btn-action {
    font-size: 9px;
    padding: 4px 12px;
    border-radius: 6px;
    border: 1px solid #ddd0bf;
    background: rgba(180,140,100,0.06);
    color: #8b7355;
    cursor: pointer;
    transition: all 0.15s;
}
.post-card .btn-action:hover { background: rgba(180,140,100,0.15); }
.post-card .btn-action.copied { color: #5a9a5a; border-color: #8cc08c; }
.post-card .btn-action.delete:hover { color: #b06060; border-color: #e8d0d0; background: rgba(200,100,100,0.06); }

/* === 空状态 === */
.empty-state {
    text-align: center;
    color: #c4b5a5;
    padding: 60px 20px;
    font-size: 14px;
    letter-spacing: 1px;
}
.empty-state.hidden { display: none; }

/* === 页脚 === */
.page-footer {
    text-align: center;
    margin-top: 30px;
    padding: 20px 0;
    font-size: 10px;
    color: #c4b5a5;
    letter-spacing: 2px;
}

/* === 弹窗 === */
.modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.3);
    z-index: 100;
    display: flex;
    align-items: center;
    justify-content: center;
    backdrop-filter: blur(4px);
}
.modal-overlay.hidden { display: none; }
.modal-box {
    background: rgba(255,255,255,0.9);
    backdrop-filter: blur(20px);
    border-radius: 16px;
    padding: 28px;
    max-width: 500px;
    width: 90%;
    max-height: 80vh;
    overflow-y: auto;
    border: 1px solid rgba(180,140,100,0.2);
}
.modal-box .modal-time {
    font-size: 10px;
    color: #a08870;
    margin-bottom: 6px;
}
.modal-box .modal-genre {
    display: inline-block;
    font-size: 9px;
    background: rgba(180,140,100,0.12);
    color: #8b6914;
    padding: 2px 10px;
    border-radius: 8px;
    margin-bottom: 14px;
}
.modal-box .modal-content {
    font-size: 15px;
    line-height: 1.9;
    color: #5c4a3a;
    white-space: pre-wrap;
    word-break: break-word;
    margin-bottom: 16px;
}
.modal-box .modal-actions {
    display: flex;
    gap: 8px;
    justify-content: flex-end;
}
.modal-box .btn-modal {
    font-size: 11px;
    padding: 6px 18px;
    border-radius: 8px;
    cursor: pointer;
    border: 1px solid #ddd0bf;
    background: rgba(180,140,100,0.06);
    color: #8b7355;
    transition: all 0.15s;
}
.modal-box .btn-modal:hover { background: rgba(180,140,100,0.15); }

/* === 删除确认对话框 === */
.dialog-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.3);
    z-index: 200;
    display: flex;
    align-items: center;
    justify-content: center;
    backdrop-filter: blur(4px);
}
.dialog-overlay.hidden { display: none; }
.dialog-box {
    background: rgba(255,255,255,0.9);
    backdrop-filter: blur(20px);
    border-radius: 16px;
    padding: 28px;
    width: 300px;
    text-align: center;
    border: 1px solid rgba(180,140,100,0.2);
}
.dialog-box p {
    font-size: 14px;
    color: #5c4a3a;
    margin-bottom: 20px;
}
.dialog-actions { display: flex; gap: 10px; justify-content: center; }
.btn-cancel, .btn-danger {
    padding: 8px 24px;
    border-radius: 8px;
    font-size: 13px;
    cursor: pointer;
    border: 1px solid #ddd0bf;
    background: rgba(180,140,100,0.06);
    color: #8b7355;
}
.btn-danger { background: #b06060; color: #fff; border-color: #b06060; }

/* === Toast === */
.toast {
    position: fixed;
    bottom: 30px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(60,45,30,0.85);
    color: #f0e8d8;
    padding: 10px 24px;
    border-radius: 20px;
    font-size: 12px;
    z-index: 300;
    transition: opacity 0.3s;
    letter-spacing: 1px;
}
.toast.hidden { opacity: 0; pointer-events: none; }

/* === 响应式 === */
@media (max-width: 900px) {
    .hero-inner {
        flex-direction: column;
    }
    .panel {
        width: 100%;
    }
    .preview {
        min-height: 200px;
    }
    .main-content {
        padding: 12px 16px;
    }
    .post-grid {
        grid-template-columns: 1fr;
    }
}

@media (max-width: 480px) {
    .panel {
        padding: 18px 14px;
    }
    .panel-title { font-size: 16px; }
    .input-row { flex-direction: column; }
    .btn-generate { width: 100%; }
    .thumb-card { min-width: 120px; height: 72px; }
}
```

- [ ] **Step 2: Commit**

```bash
git add style.css
git commit -m "style: add preview panel, scroll strip, post grid, modal, and responsive styles"
```

---

### Task 5: 重写 script.js — 配置与数据模型

**Files:**
- Rewrite: `script.js`

- [ ] **Step 1: 写入配置常量与类型数据**

```javascript
// === 配置 ===
const REPO_OWNER = 'klnm2037453337-sudo';
const REPO_NAME = 'sohuxw';
const GH_PAT = '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';
const WORKFLOW_ID = 'generate.yml';
const POSTS_URL = 'data/posts.json';
const POLL_INTERVAL = 6000;
const POLL_TIMEOUT = 120000;

// === 内容类型数据 ===
const CATEGORIES = [
    {
        id: 'opinion',
        label: '📰 观点态度',
        genres: [
            { id: '时事短评', tip: '热门事件小篇幅评论，有观点但不偏激', words: '100-150字' },
            { id: '国家政策', tip: '政策解读 / 民生新规 / 福利提醒', words: '120-180字' },
            { id: '历史感悟', tip: '历史故事解读与启发', words: '100-150字' }
        ]
    },
    {
        id: 'knowledge',
        label: '🔬 知识科普',
        genres: [
            { id: '认知笔记', tip: '思维模型 / 心理学效应 / 认知偏误', words: '100-150字' },
            { id: '医学健康科普', tip: '养生 / 疾病防治 / 用药 / 急救 / 心理', words: '150-200字' },
            { id: '生活常识科普', tip: '饮食 / 家居 / 安全 / 礼仪 / 消费', words: '150-200字' },
            { id: '人文社科科普', tip: '历史 / 考古 / 语言 / 法律 / 民俗 / 哲学', words: '150-200字' },
            { id: '冷知识', tip: '有趣的反常识知识点', words: '50-100字' }
        ]
    },
    {
        id: 'life',
        label: '💡 实用生活',
        genres: [
            { id: '财经小课', tip: '个人理财 / 经济概念 / 消费避坑', words: '100-150字' },
            { id: '科技新知', tip: '新产品 / AI工具 / 数码技巧', words: '80-130字' },
            { id: '好物安利', tip: '书籍 / 电影 / 播客 / 工具推荐', words: '100-150字' },
            { id: '美食札记', tip: '美食科普 / 食谱', words: '80-120字' }
        ]
    }
];

const WORD_COUNTS = [
    { id: '极短', label: '⚡ 极短', range: '30-60字' },
    { id: '短', label: '📝 短', range: '60-120字' },
    { id: '中', label: '📄 中', range: '120-200字' },
    { id: '长', label: '📰 长', range: '200-300字' },
    { id: '超长', label: '📚 超长', range: '300-450字' }
];

// === 状态 ===
let state = {
    activeCategoryIdx: 0,
    activeGenre: '时事短评',
    activeWordCount: '中',
    isGenerating: false,
    pollTimer: null,
    pendingDeleteId: null,
    currentPreviewContent: null
};
```

- [ ] **Step 2: Commit**

```bash
git add script.js
git commit -m "feat: add config constants and content type data model"
```

---

### Task 6: 重写 script.js — UI 渲染与分类切换

**Files:**
- Modify: `script.js` (追加内容)

- [ ] **Step 1: 追加 DOM 渲染与分类切换逻辑**

在 script.js 末尾追加：

```javascript
// === DOM 引用 ===
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const categoryTabs = $('#category-tabs');
const genrePills = $('#genre-pills');
const wordcountPills = $('#wordcount-pills');
const generateBtn = $('#generate-btn');
const sourceUrl = $('#source-url');
const previewBody = $('#preview-body');
const btnCopyPreview = $('#btn-copy-preview');
const scrollTrack = $('#scroll-track');
const scrollLeft = $('#scroll-left');
const scrollRight = $('#scroll-right');
const postGrid = $('#post-grid');
const emptyState = $('#empty-state');
const modalOverlay = $('#modal-overlay');
const modalBox = $('#modal-box');
const confirmDialog = $('#confirm-dialog');
const confirmOk = $('#confirm-ok');
const confirmCancel = $('#confirm-cancel');
const toast = $('#toast');

// === 渲染分类标签 ===
function renderCategoryTabs() {
    categoryTabs.innerHTML = CATEGORIES.map((cat, i) =>
        `<button class="cat-tab${i === state.activeCategoryIdx ? ' active' : ''}"
                 data-idx="${i}">${cat.label}</button>`
    ).join('');
    categoryTabs.querySelectorAll('.cat-tab').forEach(btn => {
        btn.addEventListener('click', () => {
            state.activeCategoryIdx = parseInt(btn.dataset.idx);
            const cat = CATEGORIES[state.activeCategoryIdx];
            state.activeGenre = cat.genres[0].id;
            renderCategoryTabs();
            renderGenrePills();
        });
    });
}

// === 渲染子类型 pills ===
function renderGenrePills() {
    const cat = CATEGORIES[state.activeCategoryIdx];
    genrePills.innerHTML = cat.genres.map(g =>
        `<button class="genre-pill${g.id === state.activeGenre ? ' active' : ''}"
                 data-genre="${g.id}" data-tip="${g.tip}">${g.id}</button>`
    ).join('');
    genrePills.querySelectorAll('.genre-pill').forEach(btn => {
        btn.addEventListener('click', () => {
            state.activeGenre = btn.dataset.genre;
            renderGenrePills();
        });
    });
}

// === 渲染字数 pills ===
function renderWordCountPills() {
    wordcountPills.innerHTML = WORD_COUNTS.map(wc =>
        `<button class="wc-pill${wc.id === state.activeWordCount ? ' active' : ''}"
                 data-wc="${wc.id}">${wc.label}</button>`
    ).join('');
    wordcountPills.querySelectorAll('.wc-pill').forEach(btn => {
        btn.addEventListener('click', () => {
            state.activeWordCount = btn.dataset.wc;
            renderWordCountPills();
        });
    });
}

// === 初始化 UI ===
function initUI() {
    renderCategoryTabs();
    renderGenrePills();
    renderWordCountPills();
}
```

- [ ] **Step 2: Commit**

```bash
git add script.js
git commit -m "feat: add category/genre/wordcount pill rendering and selection logic"
```

---

### Task 7: 重写 script.js — 生成触发、预览面板、轮询、滚动栏、帖子渲染

**Files:**
- Modify: `script.js` (追加内容)

- [ ] **Step 1: 追加生成触发、预览更新、轮询逻辑**

```javascript
// === Toast ===
function showToast(text) {
    toast.textContent = text;
    toast.classList.remove('hidden');
    setTimeout(() => toast.classList.add('hidden'), 2500);
}

// === 触发生成 ===
async function triggerWorkflow() {
    if (state.isGenerating) return;

    state.isGenerating = true;
    generateBtn.disabled = true;
    generateBtn.textContent = '生成中...';

    try {
        const beforeResp = await fetch(POSTS_URL);
        const beforePosts = beforeResp.ok ? await beforeResp.json() : [];
        const latestIdBefore = beforePosts.length > 0 ? beforePosts[0].id : null;

        const apiUrl = `https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/actions/workflows/${WORKFLOW_ID}/dispatches`;
        const resp = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Accept': 'application/vnd.github+json',
                'Authorization': `token ${GH_PAT}`,
            },
            body: JSON.stringify({
                ref: 'main',
                inputs: {
                    genre: state.activeGenre,
                    word_count: state.activeWordCount,
                    source_url: sourceUrl.value.trim()
                }
            })
        });

        if (resp.status !== 204) {
            const errBody = await resp.text();
            throw new Error(`${resp.status}: ${errBody}`);
        }

        showToast('已触发生成，正在等待 AI 写稿...');
        startPolling(latestIdBefore);
    } catch (err) {
        console.error('Workflow trigger error:', err);
        showToast('生成失败，请稍后重试');
        resetGenerateButton();
    }
}

function resetGenerateButton() {
    state.isGenerating = false;
    generateBtn.disabled = false;
    generateBtn.textContent = '生成 →';
    if (state.pollTimer) {
        clearTimeout(state.pollTimer);
        state.pollTimer = null;
    }
}

function startPolling(latestIdBefore) {
    const startTime = Date.now();

    async function poll() {
        if (Date.now() - startTime > POLL_TIMEOUT) {
            showToast('响应超时，请手动刷新页面查看');
            resetGenerateButton();
            return;
        }

        try {
            const resp = await fetch(POSTS_URL + '?t=' + Date.now());
            if (resp.ok) {
                const posts = await resp.json();
                if (posts.length > 0 && posts[0].id !== latestIdBefore) {
                    // 更新预览面板
                    updatePreview(posts[0]);
                    // 重新渲染全部
                    await loadAndRender();
                    resetGenerateButton();
                    return;
                }
            }
        } catch { /* continue polling */ }

        state.pollTimer = setTimeout(poll, POLL_INTERVAL);
    }

    poll();
}

// === 预览面板 ===
function updatePreview(post) {
    state.currentPreviewContent = post.content;
    previewBody.innerHTML = `<div class="preview-content">${escapeHTML(post.content)}</div>`;
    btnCopyPreview.disabled = false;
}

btnCopyPreview.addEventListener('click', async () => {
    if (!state.currentPreviewContent) return;
    try {
        await navigator.clipboard.writeText(state.currentPreviewContent);
        btnCopyPreview.textContent = '✅ 已复制';
        setTimeout(() => { btnCopyPreview.textContent = '一键复制'; }, 1500);
    } catch {
        const ta = document.createElement('textarea');
        ta.value = state.currentPreviewContent;
        ta.style.position = 'fixed'; ta.style.opacity = '0';
        document.body.appendChild(ta); ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        btnCopyPreview.textContent = '✅ 已复制';
        setTimeout(() => { btnCopyPreview.textContent = '一键复制'; }, 1500);
    }
});

generateBtn.addEventListener('click', triggerWorkflow);
```

- [ ] **Step 2: 追加滚动栏逻辑**

```javascript
// === 底部滚动栏 ===
scrollLeft.addEventListener('click', () => {
    scrollTrack.scrollBy({ left: -300, behavior: 'smooth' });
});
scrollRight.addEventListener('click', () => {
    scrollTrack.scrollBy({ left: 300, behavior: 'smooth' });
});

// 触摸设备上隐藏按钮（可选）
if ('ontouchstart' in window) {
    scrollLeft.style.opacity = '0.5';
    scrollRight.style.opacity = '0.5';
}
```

- [ ] **Step 3: 追加帖子渲染逻辑**

```javascript
// === 工具函数 ===
function escapeHTML(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function getDeletedIds() {
    try { return JSON.parse(localStorage.getItem('sohu_deleted_posts') || '[]'); }
    catch { return []; }
}

function addDeletedId(id) {
    const ids = getDeletedIds();
    ids.push(id);
    localStorage.setItem('sohu_deleted_posts', JSON.stringify(ids.slice(-500)));
}

function formatTime(isoStr) {
    return new Date(isoStr).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
}

// === 创建帖子卡片 DOM ===
function createPostCard(post) {
    const card = document.createElement('div');
    card.className = 'post-card';
    card.dataset.id = post.id;

    card.innerHTML = `
        <div class="post-header">
            <div class="post-meta">
                <span class="post-time">🕐 ${formatTime(post.created_at)}</span>
                <span class="post-genre">${escapeHTML(post.genre || post.style || '')}</span>
            </div>
            <div class="post-actions">
                <button class="btn-action copy-btn">复制</button>
                <button class="btn-action delete-btn">删除</button>
            </div>
        </div>
        <div class="post-content">${escapeHTML(post.content)}</div>
    `;

    card.querySelector('.copy-btn').addEventListener('click', (e) => {
        e.stopPropagation();
        copyPostContent(post.content, card.querySelector('.copy-btn'));
    });
    card.querySelector('.delete-btn').addEventListener('click', (e) => {
        e.stopPropagation();
        showDeleteConfirm(post.id, card);
    });

    return card;
}

// === 创建缩略卡片 DOM ===
function createThumbCard(post) {
    const card = document.createElement('div');
    card.className = 'thumb-card';
    card.innerHTML = `
        <div class="thumb-time">🕐 ${formatTime(post.created_at)} · ${escapeHTML(post.genre || post.style || '')}</div>
        <div class="thumb-text">${escapeHTML(post.content)}</div>
    `;
    card.addEventListener('click', () => openModal(post));
    return card;
}

// === 加载并渲染全部 ===
async function loadAndRender() {
    try {
        const resp = await fetch(POSTS_URL);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const posts = await resp.json();
        const deletedIds = getDeletedIds();
        const visible = posts.filter(p => !deletedIds.includes(p.id));

        // 帖子网格
        if (visible.length === 0) {
            postGrid.innerHTML = '';
            emptyState.classList.remove('hidden');
        } else {
            emptyState.classList.add('hidden');
            postGrid.innerHTML = '';
            visible.forEach(post => postGrid.appendChild(createPostCard(post)));
        }

        // 缩略滚动栏
        scrollTrack.innerHTML = '';
        visible.slice(0, 20).forEach(post => scrollTrack.appendChild(createThumbCard(post)));

    } catch (err) {
        if (postGrid.children.length === 0) {
            emptyState.classList.remove('hidden');
        }
    }
}

// === 弹窗 ===
function openModal(post) {
    modalBox.innerHTML = `
        <div class="modal-time">🕐 ${new Date(post.created_at).toLocaleString('zh-CN')}</div>
        <div class="modal-genre">${escapeHTML(post.genre || post.style || '')}</div>
        <div class="modal-content">${escapeHTML(post.content)}</div>
        <div class="modal-actions">
            <button class="btn-modal copy-modal-btn">复制</button>
            <button class="btn-modal close-modal-btn">关闭</button>
        </div>
    `;
    modalOverlay.classList.remove('hidden');

    modalBox.querySelector('.copy-modal-btn').addEventListener('click', () => {
        copyPostContent(post.content, modalBox.querySelector('.copy-modal-btn'));
    });
    modalBox.querySelector('.close-modal-btn').addEventListener('click', closeModal);
    modalOverlay.addEventListener('click', (e) => {
        if (e.target === modalOverlay) closeModal();
    });
}

function closeModal() {
    modalOverlay.classList.add('hidden');
}

// === 复制 ===
async function copyPostContent(text, btn) {
    try {
        await navigator.clipboard.writeText(text);
        btn.textContent = '✅ 已复制';
        btn.classList.add('copied');
        setTimeout(() => { btn.textContent = '复制'; btn.classList.remove('copied'); }, 1500);
    } catch {
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed'; ta.style.opacity = '0';
        document.body.appendChild(ta); ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        btn.textContent = '✅ 已复制';
        btn.classList.add('copied');
        setTimeout(() => { btn.textContent = '复制'; btn.classList.remove('copied'); }, 1500);
    }
}

// === 删除 ===
function showDeleteConfirm(id, card) {
    state.pendingDeleteId = id;
    confirmDialog._targetCard = card;
    confirmDialog.classList.remove('hidden');
}

function hideDeleteConfirm() {
    confirmDialog.classList.add('hidden');
    state.pendingDeleteId = null;
    confirmDialog._targetCard = null;
}

function executeDelete() {
    if (!state.pendingDeleteId) return;
    addDeletedId(state.pendingDeleteId);
    if (confirmDialog._targetCard) confirmDialog._targetCard.remove();
    hideDeleteConfirm();
    if (postGrid.querySelectorAll('.post-card').length === 0) {
        emptyState.classList.remove('hidden');
    }
    // 同步更新滚动栏
    const visible = getDeletedIds();
    scrollTrack.querySelectorAll('.thumb-card').forEach(card => {
        // thumb cards don't have data-id, rebuild instead
    });
    loadAndRender(); // simpler: just reload
}

confirmOk.addEventListener('click', executeDelete);
confirmCancel.addEventListener('click', hideDeleteConfirm);

// === 初始化 ===
initUI();
loadAndRender();
setInterval(loadAndRender, 30000);
```

- [ ] **Step 2: Commit**

```bash
git add script.js
git commit -m "feat: add generate trigger, preview panel, polling, scroll bar, post rendering"
```

---

### Task 8: 更新 GitHub Actions 工作流

**Files:**
- Modify: `.github/workflows/generate.yml`

- [ ] **Step 1: 新增 genre / word_count / source_url 参数**

将 generate.yml 完整替换为：

```yaml
name: Generate Post

on:
  workflow_dispatch:
    inputs:
      genre:
        description: '内容类型'
        required: true
        type: string
        default: '时事短评'
      word_count:
        description: '字数档位'
        required: true
        type: string
        default: '中'
      source_url:
        description: '参考链接（可选）'
        required: false
        type: string
        default: ''

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
        run: pip install openai requests trafilatura

      - name: Generate post
        env:
          DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}
        run: |
          python scripts/generate.py \
            --genre "${{ inputs.genre }}" \
            --word-count "${{ inputs.word_count }}" \
            --source-url "${{ inputs.source_url }}"

      - name: Commit and push
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add data/posts.json
          git diff --staged --quiet || git commit -m "feat: add new post [skip ci]"
          git push
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/generate.yml
git commit -m "feat: add genre, word_count, source_url workflow inputs"
```

---

### Task 9: 更新 Python 生成脚本

**Files:**
- Rewrite: `scripts/generate.py`

- [ ] **Step 1: 重写 generate.py 支持新参数 + trafilatura**

```python
"""搜狐热帖生成器 — AI 生成短文 + URL 参考"""
import argparse
import json
import os
import random
import string
from datetime import datetime, timezone, timedelta

from openai import OpenAI
import trafilatura

CST = timezone(timedelta(hours=8))

GENRE_PROMPTS = {
    "时事短评": "你是自媒体作者"江"。针对参考新闻写一篇小篇幅评论（无参考链接时自行选题）。有观点但不偏激，不标题党。口语化、自然、有个人感受。字数：{word_count}。",
    "国家政策": "你是自媒体作者"江"。用通俗易懂的语言解读一项国家政策或民生新规，让普通人能看懂。说人话，不念文件。字数：{word_count}。",
    "历史感悟": "你是自媒体作者"江"。讲一个历史故事，并从中提炼出对现代生活的启发。故事要生动，启发要有共鸣。字数：{word_count}。",
    "认知笔记": "你是自媒体作者"江"。介绍一个思维模型、心理学效应或认知偏误，用生活化的例子解释它。字数：{word_count}。",
    "医学健康科普": "你是自媒体作者"江"。科普一个医学健康知识（养生/疾病防治/用药/急救/心理）。科学准确但语言通俗。字数：{word_count}。",
    "生活常识科普": "你是自媒体作者"江"。科普一个日常生活实用知识（饮食/家居/安全/礼仪/消费）。实用、接地气。字数：{word_count}。",
    "人文社科科普": "你是自媒体作者"江"。科普一个人文社科知识点（历史/考古/语言/法律/经济/民俗/哲学）。有趣有料。字数：{word_count}。",
    "冷知识": "你是自媒体作者"江"。分享一个有趣的反常识冷知识，让人看完觉得"原来如此"。简短有力。字数：{word_count}。",
    "财经小课": "你是自媒体作者"江"。用通俗语言讲一个个人理财知识或经济概念，帮助读者避坑或省钱。字数：{word_count}。",
    "科技新知": "你是自媒体作者"江"。介绍一个新产品、AI工具或数码技巧，让读者了解科技前沿。字数：{word_count}。",
    "好物安利": "你是自媒体作者"江"。推荐一本书/电影/播客/工具，说明推荐理由和个人感受。真诚不浮夸。字数：{word_count}。",
    "美食札记": "你是自媒体作者"江"。介绍一道美食的做法或科普一个食材知识。让人看了有食欲或学到东西。字数：{word_count}。",
}

WORD_COUNT_MAP = {
    "极短": "30-60字",
    "短": "60-120字",
    "中": "120-200字",
    "长": "200-300字",
    "超长": "300-450字",
}

SYSTEM_PROMPT_TEMPLATE = """你是搜狐新闻自媒体作者"江"，每天发布有营养的原创短内容。

{genre_instruction}

输出格式必须是严格的 JSON：
{{"content": "帖子正文（纯文本，不包含标题）"}}

注意：
- 输出纯文本正文，不要加"标题："等前缀
- 不要使用 markdown 格式
- 如果有参考链接内容，基于它来写，但不要直接复制
- 如果没有参考链接，自行选择一个相关话题"""


def fetch_url_content(url: str) -> str | None:
    """抓取网页正文，失败返回 None"""
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded, include_links=False,
                                       include_images=False, include_tables=False)
            if text:
                # 限制长度避免超出 token
                return text[:3000]
    except Exception:
        pass
    return None


def generate_post_text(genre: str, word_count: str, source_url: str) -> dict:
    """调用 DeepSeek API 生成帖子"""
    client = OpenAI(
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url="https://api.deepseek.com"
    )

    word_range = WORD_COUNT_MAP.get(word_count, "120-200字")
    genre_instruction = GENRE_PROMPTS.get(genre, GENRE_PROMPTS["时事短评"]).format(word_count=word_range)

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(genre_instruction=genre_instruction)

    # 构建用户消息
    user_message = ""
    if source_url:
        article_text = fetch_url_content(source_url)
        if article_text:
            user_message = f"请基于以下参考文章的内容写一篇帖子：\n\n{article_text}"
        else:
            user_message = f"请自行选择一个与「{genre}」相关的热点话题写一篇帖子。（参考链接抓取失败，请自由选题）"
    else:
        user_message = f"请自行选择一个与「{genre}」相关的热门话题写一篇帖子。"

    message = client.chat.completions.create(
        model="deepseek-chat",
        max_tokens=800,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    )

    raw = message.choices[0].message.content.strip()
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()

    return json.loads(raw)


POSTS_FILE = "data/posts.json"
MAX_POSTS = 200


def load_posts() -> list[dict]:
    with open(POSTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_posts(posts: list[dict]):
    trimmed = posts[:MAX_POSTS]
    with open(POSTS_FILE, "w", encoding="utf-8") as f:
        json.dump(trimmed, f, ensure_ascii=False, indent=2)


def append_post(post: dict):
    posts = load_posts()
    posts.insert(0, post)
    save_posts(posts)


def make_post_id() -> str:
    now = datetime.now(CST)
    ts = now.strftime("%Y%m%d-%H%M%S")
    rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{ts}-{rand}"


def main():
    parser = argparse.ArgumentParser(description="生成一篇搜狐热帖")
    parser.add_argument("--genre", default="时事短评", help="内容类型")
    parser.add_argument("--word-count", default="中", help="字数档位")
    parser.add_argument("--source-url", default="", help="参考链接（可选）")
    args = parser.parse_args()

    result = generate_post_text(args.genre, args.word_count, args.source_url)

    post = {
        "id": make_post_id(),
        "content": result["content"],
        "genre": args.genre,
        "word_count": args.word_count,
        "created_at": datetime.now(CST).isoformat()
    }

    append_post(post)
    print(f"Generated post: {post['id']}")
    print(f"  genre: {args.genre}")
    print(f"  word_count: {args.word_count}")
    print(f"  source_url: {args.source_url or 'none'}")
    print(f"  content: {post['content'][:80]}...")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add scripts/generate.py
git commit -m "feat: rewrite generate.py with genre/wordcount/source_url support and trafilatura"
```

---

### Task 10: 端到端验证

- [ ] **Step 1: 本地验证前端**

在浏览器打开 `index.html`，验证：
- 场景背景渲染（天空、云、草坡、木屋、电线杆）
- 分类标签切换
- 子类型 pills 选择（带 hover 提示）
- 字数 pills 选择
- 链接输入框
- 预览面板占位状态
- 响应式（缩放浏览器窗口到 480px）

- [ ] **Step 2: 提交并推送**

```bash
git add -A
git commit -m "chore: finalize frontend redesign implementation"
git push origin main
```

- [ ] **Step 3: 等待 GitHub Pages 部署后访问验证**

打开 `https://klnm2037453337-sudo.github.io/sohuxw/`，验证生产环境。

- [ ] **Step 4: 测试生成流程**

点击生成按钮 → 等待轮询 → 确认预览面板显示新内容 → 确认帖子列表更新 → 确认滚动栏缩略卡片更新。

---

## 验证清单

- [ ] 场景背景在所有主流分辨率下完整显示
- [ ] 12 种内容类型可正常切换和选择
- [ ] 5 档字数可正常切换和选择
- [ ] Hover 提示气泡正常弹出
- [ ] 生成按钮触发 GitHub Actions 成功
- [ ] 轮询检测到新帖子后预览面板更新
- [ ] 预览面板一键复制可用
- [ ] 底部滚动栏左右按钮正常滚动
- [ ] 缩略卡片点击弹窗查看完整内容
- [ ] 帖子网格自适应列数
- [ ] 帖子复制/删除功能正常
- [ ] 弹窗关闭正常
- [ ] 移动端布局（<900px 上下堆叠，<480px 全宽）
- [ ] 已删除帖子在 localStorage 记录，刷新后不显示
- [ ] GitHub Actions 正常接收 genre/word_count/source_url 参数
- [ ] Python 脚本正确解析参数并生成内容
- [ ] trafilatura URL 抓取正常（提供有效 URL 时）
- [ ] trafilatura 抓取失败时优雅降级（自由选题）
