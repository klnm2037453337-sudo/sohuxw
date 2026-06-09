// === 配置 ===
const REPO_OWNER = 'klnm2037453337-sudo';
const REPO_NAME = 'sohuxw';
const GH_PAT = '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';
const WORKFLOW_ID = 'generate.yml';
const POSTS_URL = 'data/posts.json';
const POLL_INTERVAL = 6000;
const POLL_TIMEOUT = 120000;

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

// === 工具函数 ===

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

function escapeHTML(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// === 帖子卡片渲染 ===

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

    card.querySelector('.copy-btn').addEventListener('click', () => {
        copyPost(post.content, card.querySelector('.copy-btn'));
    });

    card.querySelector('.delete-btn').addEventListener('click', () => {
        showDeleteConfirm(post.id, card);
    });

    return card;
}

async function loadAndRender() {
    try {
        const resp = await fetch(POSTS_URL);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const posts = await resp.json();

        const deletedIds = getDeletedIds();
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

// === 复制功能 ===

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

// === 删除功能 ===

function showDeleteConfirm(id, card) {
    pendingDeleteId = id;
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

    if (postList.querySelectorAll('.post-card').length === 0) {
        postList.appendChild(emptyState);
        emptyState.classList.remove('hidden');
    }
}

confirmOk.addEventListener('click', executeDelete);
confirmCancel.addEventListener('click', hideDeleteConfirm);

// === 触发生成（调用 GitHub API） ===

async function triggerWorkflow() {
    if (isGenerating) return;

    const style = getStyle();
    isGenerating = true;
    generateBtn.disabled = true;
    generateBtn.textContent = '生成中...';
    hint.classList.remove('hidden');
    hideMessage();

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
            body: JSON.stringify({ ref: 'main', inputs: { style: style } })
        });

        if (resp.status !== 204) {
            const errBody = await resp.text();
            throw new Error(`${resp.status}: ${errBody}`);
        }

        startPolling(latestIdBefore);
    } catch (err) {
        console.error('Workflow trigger error:', err);
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
        if (Date.now() - startTime > POLL_TIMEOUT) {
            showMessage('响应超时，请手动刷新页面查看', 'error');
            resetGenerateButton();
            return;
        }

        try {
            const resp = await fetch(POSTS_URL + '?t=' + Date.now());
            if (resp.ok) {
                const posts = await resp.json();
                if (posts.length > 0 && posts[0].id !== latestIdBefore) {
                    await loadAndRender();
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                    resetGenerateButton();
                    return;
                }
            }
        } catch {
            // 继续轮询
        }

        pollTimer = setTimeout(poll, POLL_INTERVAL);
    }

    poll();
}

generateBtn.addEventListener('click', triggerWorkflow);

// === 页面初始化 ===
loadAndRender();

// 定期刷新（每 30 秒检查是否有新帖）
setInterval(loadAndRender, 30000);
