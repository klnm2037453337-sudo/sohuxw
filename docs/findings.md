# 对话核心摘要 — 2026-06-10 搜狐热帖助手前端重设计

> 新对话时读此文件即可无缝接续。

---

## 1. 项目本质

搜狐新闻自媒体内容生成工具。网页选类型→点按钮→GitHub Actions 调 DeepSeek API 生成帖子→结果显示在网页上→复制发布。

- 网站: https://klnm2037453337-sudo.github.io/sohuxw/
- 仓库: klnm2037453337-sudo/sohuxw
- PAT: `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` (repo+workflow)
- DeepSeek Key: 已存 GitHub Secrets → DEEPSEEK_API_KEY

---

## 2. 本次对话成果：前端重设计已完成

### 视觉
- **场景背景**：纯 CSS 绘制云海天空 + 草坡岛屿 + 小木屋 + 电线杆，日出暖光氛围
- **面板**：毛玻璃半透明（`backdrop-filter: blur(24px)`），淡彩水墨配色（赭石棕 #b48c64 + 宣纸暖白）
- **布局**：首屏左右双栏（440px 操作面板 + 自适应预览面板，等高等宽居中），底部横向正方形缩略卡片滚动栏（110×110px，圆角16px，等大等字号，超长省略号），首屏以下帖子自适应网格

### 内容体系：3 大类 × 12 种类型

| 分类 | 类型 |
|------|------|
| 📰 观点态度 | 时事短评、国家政策、历史感悟 |
| 🔬 知识科普 | 认知笔记、医学健康科普、生活常识科普、人文社科科普、冷知识 |
| 💡 实用生活 | 财经小课、科技新知、好物安利、美食札记 |

### 字数五档
⚡极短(30-60) / 📝短(60-120) / 📄中(120-200,默认) / 📰长(200-300) / 📚超长(300-450)

### 功能交互
- 分类标签切换（3 个 tab），下方子类型 pills 联动
- 子类型 pills hover 弹出描述气泡（`::after` + `data-tip`）
- 字数 pills 独立选择，默认"中"
- 链接输入框（选填），留空 AI 自由选题
- 生成按钮触发 GitHub Actions workflow_dispatch（传 genre/word_count/source_url）
- 右侧实时预览面板：生成前占位引导，生成后显示内容 + 一键复制
- 底部横向滚动栏：scroll-snap + ◂▸ 圆形按钮
- 缩略卡片点击弹窗查看完整内容
- 帖子卡片复制/删除（localStorage 记录已删 ID）
- 响应式：<900px 上下堆叠，<480px 全宽

---

## 3. 已完成修改的文件

| 文件 | 状态 |
|------|------|
| `index.html` | ✅ 重写 — 新结构 |
| `style.css` | ✅ 重写 — 场景+组件+响应式 |
| `script.js` | ✅ 重写 — 430行完整逻辑 |
| `.github/workflows/generate.yml` | ✅ 更新 — genre/word_count/source_url 参数 |
| `scripts/generate.py` | ✅ 重写 — 12种System Prompt + trafilatura |

---

## 4. 待解决问题（下次对话做）

1. **内容质量精调** — System Prompt 需根据实际生成效果调优（12 种类型的 prompt 在 generate.py 的 `GENRE_PROMPTS` 字典中）
2. **配图功能** — 暂无配图方案（Unsplash 注册不了，Pexels 待尝试，或 Pollinations.AI 免费 AI 生成图片）
3. **README 更新** — 还是旧的使用说明
4. **旧帖子兼容** — data/posts.json 中 2 篇旧帖子字段为 `style: "chatty"` 和 `style: "newsflash"`，JS 渲染时用 `post.genre || post.style` 兼容

---

## 5. 关键约束

- GitHub Pages 纯静态托管，不能有服务端代码
- 场景背景纯 CSS 实现，不依赖外部图片
- DeepSeek API 调用 60 秒内完成
- GitHub API Authorization header 必须用 `token` 前缀，不是 `Bearer`
- PAT 需 repo + workflow 权限
- GH Pages 部署有 1-2 分钟延迟
- trafilatura URL 抓取需处理超时和失败

---

## 6. 关键代码路径

- 内容类型配置: `script.js` → `CATEGORIES` 数组
- AI Prompt: `scripts/generate.py` → `GENRE_PROMPTS` 字典
- 工作流参数: `.github/workflows/generate.yml` → `inputs`
- API 触发: `script.js` → `triggerWorkflow()` 函数
- 配色变量: `style.css` → 色值 #b48c64(赭石) / #5c4a3a(深棕) / #8b7355(中棕)
- 缩略卡片: `style.css` → `.thumb-card` (110×110px, border-radius:16px)
- 预览面板: `script.js` → `updatePreview()` 函数
