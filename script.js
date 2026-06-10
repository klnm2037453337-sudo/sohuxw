// === 配置 ===
const WORKFLOW_PAGE = 'https://github.com/klnm2037453337-sudo/sohuxw/actions/workflows/generate.yml';
const POSTS_URL = 'data/posts.json';
const POLL_INTERVAL = 6000;
const POLL_TIMEOUT = 120000;

// === 内容类型数据 ===
const CATEGORIES = [
    {
        id: 'opinion',
        label: '📰 观点态度',
        genres: [
            { id: '时事短评', tip: '热门事件小篇幅评论，有观点但不偏激' },
            { id: '国家政策', tip: '政策解读 / 民生新规 / 福利提醒' },
            { id: '历史感悟', tip: '历史故事解读与启发' }
        ]
    },
    {
        id: 'knowledge',
        label: '🔬 知识科普',
        genres: [
            { id: '认知笔记', tip: '思维模型 / 心理学效应 / 认知偏误' },
            { id: '医学健康科普', tip: '养生 / 疾病防治 / 用药 / 急救 / 心理' },
            { id: '生活常识科普', tip: '饮食 / 家居 / 安全 / 礼仪 / 消费' },
            { id: '人文社科科普', tip: '历史 / 考古 / 语言 / 法律 / 民俗 / 哲学' },
            { id: '冷知识', tip: '有趣的反常识知识点' }
        ]
    },
    {
        id: 'life',
        label: '💡 实用生活',
        genres: [
            { id: '财经小课', tip: '个人理财 / 经济概念 / 消费避坑' },
            { id: '科技新知', tip: '新产品 / AI工具 / 数码技巧' },
            { id: '好物安利', tip: '书籍 / 电影 / 播客 / 工具推荐' },
            { id: '美食札记', tip: '美食科普 / 食谱' }
        ]
    }
];

const WORD_COUNTS = [
    { id: '极短', label: '⚡ 极短' },
    { id: '短', label: '📝 短' },
    { id: '中', label: '📄 中' },
    { id: '长', label: '📰 长' },
    { id: '超长', label: '📚 超长' }
];

// === 状态 ===
const state = {
    activeCategoryIdx: 0,
    activeGenre: '时事短评',
    activeWordCount: '中',
    isGenerating: false,
    pollTimer: null,
    pendingDeleteId: null,
    currentPreviewContent: null
};

// === DOM 引用 ===
const $ = (sel) => document.querySelector(sel);

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

// ========================================
// UI 渲染
// ========================================

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

function initUI() {
    renderCategoryTabs();
    renderGenrePills();
    renderWordCountPills();
}

// ========================================
// Toast
// ========================================

function showToast(text) {
    toast.textContent = text;
    toast.classList.remove('hidden');
    setTimeout(() => toast.classList.add('hidden'), 2500);
}

// ========================================
// 触发生成
// ========================================

function triggerWorkflow() {
    if (state.isGenerating) return;

    state.isGenerating = true;
    generateBtn.disabled = true;
    generateBtn.textContent = '⏳ 等待触发...';

    // 记录当前最新帖子 ID，用于轮询检测
    fetch(POSTS_URL)
        .then(r => r.ok ? r.json() : [])
        .then(posts => {
            const latestIdBefore = posts.length > 0 ? posts[0].id : null;
            // 打开 GitHub Actions 触发页面（新标签页）
            window.open(WORKFLOW_PAGE, '_blank');
            showToast('请在打开的页面点击「Run workflow」→ 绿色「Run workflow」按钮');
            startPolling(latestIdBefore);
        })
        .catch(() => {
            // 即使获取失败也继续
            window.open(WORKFLOW_PAGE, '_blank');
            showToast('请在打开的页面点击「Run workflow」→ 绿色「Run workflow」按钮');
            startPolling(null);
        });
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
                    updatePreview(posts[0]);
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

generateBtn.addEventListener('click', triggerWorkflow);

// ========================================
// 预览面板
// ========================================

function updatePreview(post) {
    state.currentPreviewContent = post.content;
    previewBody.innerHTML = `<div class="preview-content">${escapeHTML(post.content)}</div>`;
    btnCopyPreview.disabled = false;

    // 显示参考来源
    const sourceEl = $('#preview-source');
    const sourceLink = $('#preview-source-link');
    if (post.source_url && post.source_title) {
        sourceEl.classList.remove('hidden');
        sourceLink.href = post.source_url;
        sourceLink.textContent = post.source_title;
    } else if (post.source_url) {
        sourceEl.classList.remove('hidden');
        sourceLink.href = post.source_url;
        sourceLink.textContent = post.source_url;
    } else {
        sourceEl.classList.add('hidden');
    }
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

// ========================================
// 底部滚动栏
// ========================================

scrollLeft.addEventListener('click', () => {
    scrollTrack.scrollBy({ left: -300, behavior: 'smooth' });
});
scrollRight.addEventListener('click', () => {
    scrollTrack.scrollBy({ left: 300, behavior: 'smooth' });
});

// ========================================
// 工具函数
// ========================================

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

// ========================================
// 帖子卡片 DOM
// ========================================

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
        ${post.source_url ? `<div class="post-source">📎 参考：<a href="${escapeHTML(post.source_url)}" target="_blank" rel="noopener">${escapeHTML(post.source_title || post.source_url)}</a></div>` : ''}
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

// ========================================
// 加载与渲染
// ========================================

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

// ========================================
// 弹窗
// ========================================

function openModal(post) {
    modalBox.innerHTML = `
        <div class="modal-time">🕐 ${new Date(post.created_at).toLocaleString('zh-CN')}</div>
        <div class="modal-genre">${escapeHTML(post.genre || post.style || '')}</div>
        <div class="modal-content">${escapeHTML(post.content)}</div>
        ${post.source_url ? `<div class="modal-source">📎 参考来源：<a href="${escapeHTML(post.source_url)}" target="_blank" rel="noopener">${escapeHTML(post.source_title || post.source_url)}</a></div>` : ''}
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

// ========================================
// 复制
// ========================================

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

// ========================================
// 删除
// ========================================

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
    loadAndRender();
}

confirmOk.addEventListener('click', executeDelete);
confirmCancel.addEventListener('click', hideDeleteConfirm);

// ========================================
// 初始化
// ========================================

initUI();
loadAndRender();
setInterval(loadAndRender, 30000);
