const API_BASE = '';

// ── DOM Elements ──
const sidebar = document.getElementById('sidebar');
const sidebarToggle = document.getElementById('sidebarToggle');
const sidebarClose = document.getElementById('sidebarClose');
const themeToggle = document.getElementById('themeToggle');
const uploadZone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');
const docName = document.getElementById('docName');
const rawText = document.getElementById('rawText');
const ingestTextBtn = document.getElementById('ingestTextBtn');
const refreshDocs = document.getElementById('refreshDocs');
const docList = document.getElementById('docList');
const chatArea = document.getElementById('chatArea');
const welcome = document.getElementById('welcome');
const messages = document.getElementById('messages');
const queryInput = document.getElementById('queryInput');
const sendBtn = document.getElementById('sendBtn');
const toastContainer = document.getElementById('toastContainer');

// ── Theme ──
function initTheme() {
  const saved = localStorage.getItem('theme');
  if (saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    document.documentElement.setAttribute('data-theme', 'dark');
  }
}

themeToggle.addEventListener('click', () => {
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  document.documentElement.setAttribute('data-theme', isDark ? 'light' : 'dark');
  localStorage.setItem('theme', isDark ? 'light' : 'dark');
});

// ── Sidebar Toggle ──
sidebarToggle.addEventListener('click', () => sidebar.classList.toggle('collapsed'));
sidebarClose.addEventListener('click', () => sidebar.classList.add('collapsed'));

// ── Toast Notifications ──
function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(20px)';
    toast.style.transition = '0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// ── File Upload ──
uploadZone.addEventListener('click', () => fileInput.click());

uploadZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  uploadZone.classList.add('dragover');
});

uploadZone.addEventListener('dragleave', () => {
  uploadZone.classList.remove('dragover');
});

uploadZone.addEventListener('drop', (e) => {
  e.preventDefault();
  uploadZone.classList.remove('dragover');
  handleFiles(e.dataTransfer.files);
});

fileInput.addEventListener('change', () => {
  handleFiles(fileInput.files);
  fileInput.value = '';
});

async function handleFiles(files) {
  for (const file of files) {
    const formData = new FormData();
    formData.append('file', file);

    try {
      showToast(`Uploading ${file.name}...`, 'info');
      const res = await fetch(`${API_BASE}/ingest`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (res.ok) {
        showToast(`${file.name} added successfully`, 'success');
        loadDocuments();
      } else {
        showToast(data.detail || 'Upload failed', 'error');
      }
    } catch (err) {
      showToast(`Failed to upload ${file.name}`, 'error');
    }
  }
}

// ── Text Ingestion ──
ingestTextBtn.addEventListener('click', async () => {
  const name = docName.value.trim();
  const text = rawText.value.trim();

  if (!text) {
    showToast('Please enter some text', 'error');
    return;
  }

  ingestTextBtn.disabled = true;
  try {
    const res = await fetch(`${API_BASE}/ingest_text`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: text,
        document_name: name || 'Untitled Document',
      }),
    });
    const data = await res.json();
    if (res.ok) {
      showToast('Document added successfully', 'success');
      docName.value = '';
      rawText.value = '';
      loadDocuments();
    } else {
      showToast(data.detail || 'Ingestion failed', 'error');
    }
  } catch (err) {
    showToast('Failed to add document', 'error');
  } finally {
    ingestTextBtn.disabled = false;
  }
});

// ── Load Documents ──
async function loadDocuments() {
  try {
    const res = await fetch(`${API_BASE}/documents`);
    const data = await res.json();
    renderDocuments(data.documents || []);
  } catch {
    // Server might not be running yet
  }
}

function renderDocuments(docs) {
  if (!docs.length) {
    docList.innerHTML = `
      <div class="empty-state">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.4">
          <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><polyline points="13 2 13 9 20 9"/>
        </svg>
        <p>No documents yet</p>
      </div>`;
    return;
  }

  docList.innerHTML = docs.map(doc => `
    <div class="doc-item" data-doc-id="${escapeHtml(doc.doc_id)}">
      <div class="doc-item-icon">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/>
          <polyline points="13 2 13 9 20 9"/>
        </svg>
      </div>
      <div class="doc-item-info">
        <div class="doc-item-name" title="${escapeHtml(doc.name)}">${escapeHtml(doc.name)}</div>
        <div class="doc-item-meta">${doc.chunks} chunks</div>
      </div>
      <button class="doc-delete-btn" title="Remove from knowledge base" onclick="deleteDocument('${escapeHtml(doc.doc_id)}', '${escapeHtml(doc.name)}')">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="3 6 5 6 21 6"/>
          <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
          <path d="M10 11v6M14 11v6"/>
          <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
        </svg>
      </button>
    </div>
  `).join('');
}

async function deleteDocument(docId, docName) {
  if (!confirm(`Remove "${docName}" from the knowledge base?`)) return;

  try {
    const res = await fetch(`${API_BASE}/documents/${encodeURIComponent(docId)}`, {
      method: 'DELETE',
    });
    if (res.ok) {
      showToast(`"${docName}" removed`, 'success');
      loadDocuments();
    } else {
      const data = await res.json();
      showToast(data.detail || 'Failed to delete document', 'error');
    }
  } catch {
    showToast('Could not connect to the server', 'error');
  }
}

refreshDocs.addEventListener('click', loadDocuments);

// ── Query Input ──
queryInput.addEventListener('input', () => {
  sendBtn.disabled = !queryInput.value.trim();
  queryInput.style.height = 'auto';
  queryInput.style.height = Math.min(queryInput.scrollHeight, 120) + 'px';
});

queryInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    if (queryInput.value.trim()) sendQuery();
  }
});

sendBtn.addEventListener('click', () => {
  if (queryInput.value.trim()) sendQuery();
});

// Suggestion chips
document.querySelectorAll('.chip').forEach(chip => {
  chip.addEventListener('click', () => {
    queryInput.value = chip.dataset.query;
    sendBtn.disabled = false;
    sendQuery();
  });
});

// ── Send Query ──
async function sendQuery() {
  const question = queryInput.value.trim();
  if (!question) return;

  welcome.classList.add('hidden');
  addMessage('user', question);
  queryInput.value = '';
  queryInput.style.height = 'auto';
  sendBtn.disabled = true;

  const loadingId = addLoadingMessage();

  try {
    const res = await fetch(`${API_BASE}/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    });
    const data = await res.json();
    removeMessage(loadingId);

    if (res.ok) {
      addMessage('assistant', data.answer, data.sources);
    } else {
      addMessage('assistant', data.detail || 'Something went wrong. Please try again.');
    }
  } catch (err) {
    removeMessage(loadingId);
    addMessage('assistant', 'Could not connect to the server. Make sure the backend is running.');
  }
}

// ── Message Rendering ──
let messageCounter = 0;

function addMessage(role, content, sources) {
  const id = `msg-${++messageCounter}`;
  const div = document.createElement('div');
  div.className = `message ${role}`;
  div.id = id;

  const avatar = role === 'user' ? 'You' : 'AI';
  const sender = role === 'user' ? 'You' : 'Assistant';

  let sourcesHtml = '';
  if (sources && sources.length) {
    sourcesHtml = `
      <div class="sources">
        <div class="sources-title">Sources</div>
        <div class="source-list">
          ${sources.map(s => {
            const scoreBadge = s.rerank_score != null ? scoreHtml(s.rerank_score) : '';
            return `
            <div class="source-item">
              <div class="source-header">
                <span class="source-badge">Chunk ${s.chunk_id}</span>
                <span class="source-name">${escapeHtml(s.document_name)}</span>
                ${scoreBadge}
              </div>
              <div class="source-text">${escapeHtml(s.chunk_text || '')}</div>
            </div>`;
          }).join('')}
        </div>
      </div>`;
  }

  div.innerHTML = `
    <div class="msg-header">
      <div class="msg-avatar">${avatar.charAt(0)}</div>
      <span class="msg-sender">${sender}</span>
    </div>
    <div class="msg-body">${formatText(content)}</div>
    ${sourcesHtml}`;

  messages.appendChild(div);
  scrollToBottom();
  return id;
}

function addLoadingMessage() {
  const id = `msg-${++messageCounter}`;
  const div = document.createElement('div');
  div.className = 'message assistant';
  div.id = id;
  div.innerHTML = `
    <div class="msg-header">
      <div class="msg-avatar">A</div>
      <span class="msg-sender">Assistant</span>
    </div>
    <div class="msg-body">
      <div class="loading-dots"><span></span><span></span><span></span></div>
    </div>`;
  messages.appendChild(div);
  scrollToBottom();
  return id;
}

function removeMessage(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

function scrollToBottom() {
  chatArea.scrollTop = chatArea.scrollHeight;
}

function scoreHtml(logit) {
  // Convert cross-encoder logit to 0–100% via sigmoid
  const pct = Math.round(100 / (1 + Math.exp(-logit)));
  const cls = pct >= 70 ? 'score-high' : pct >= 40 ? 'score-mid' : 'score-low';
  return `<span class="score-badge ${cls}" title="Reranker relevance score">${pct}%</span>`;
}

function detectDir(text) {
  const rtlCount = (text.match(/[\u0590-\u05FF\u0600-\u06FF\uFB1D-\uFDFF\uFE70-\uFEFF]/g) || []).length;
  const ltrCount = (text.match(/[A-Za-z\u00C0-\u024F]/g) || []).length;
  return rtlCount > ltrCount ? 'rtl' : 'ltr';
}

function formatText(text) {
  return text
    .split('\n\n')
    .map(p => {
      const dir = detectDir(p);
      return `<p dir="${dir}">${escapeHtml(p).replace(/\n/g, '<br>')}</p>`;
    })
    .join('');
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// ── Tab Switching ──
const viewChat = document.getElementById('viewChat');
const viewInspector = document.getElementById('viewInspector');
const tabChat = document.getElementById('tabChat');
const tabInspector = document.getElementById('tabInspector');

tabChat.addEventListener('click', () => switchTab('chat'));
tabInspector.addEventListener('click', () => {
  switchTab('inspector');
  loadInspector();
});

function switchTab(tab) {
  const isChat = tab === 'chat';
  viewChat.classList.toggle('hidden', !isChat);
  viewInspector.classList.toggle('hidden', isChat);
  tabChat.classList.toggle('active', isChat);
  tabInspector.classList.toggle('active', !isChat);
}

// ── Inspector ──
const liveSearchInput = document.getElementById('liveSearchInput');
const liveSearchBtn = document.getElementById('liveSearchBtn');
const liveSearchResults = document.getElementById('liveSearchResults');
const chunkTree = document.getElementById('chunkTree');
const refreshInspector = document.getElementById('refreshInspector');

liveSearchBtn.addEventListener('click', runLiveSearch);
liveSearchInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') runLiveSearch();
});
refreshInspector.addEventListener('click', loadInspector);

async function loadInspector() {
  await Promise.all([loadStats(), loadChunkTree()]);
}

async function loadStats() {
  try {
    const res = await fetch(`${API_BASE}/stats`);
    if (!res.ok) return;
    const s = await res.json();

    document.getElementById('statDocs').textContent = s.total_documents;
    document.getElementById('statChunks').textContent = s.total_chunks.toLocaleString();
    document.getElementById('statDim').textContent = s.dimension;
    document.getElementById('statReranker').textContent = s.reranker_enabled ? 'On' : 'Off';

    const modelRow = document.getElementById('statModelRow');
    modelRow.innerHTML = `
      <span class="model-pill">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        Embedding model: <strong>${escapeHtml(s.embedding_model)}</strong>
      </span>
      <span class="model-pill">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg>
        Index: <strong>${escapeHtml(s.index_type)}</strong> &nbsp;·&nbsp; ${s.total_vectors.toLocaleString()} vectors
      </span>`;
  } catch {
    // server not running
  }
}

async function loadChunkTree() {
  try {
    const [docsRes, chunksRes] = await Promise.all([
      fetch(`${API_BASE}/documents`),
      fetch(`${API_BASE}/chunks`),
    ]);
    if (!docsRes.ok || !chunksRes.ok) return;

    const { documents } = await docsRes.json();
    const { chunks } = await chunksRes.json();

    if (!documents.length) {
      chunkTree.innerHTML = `<div class="empty-state"><p>No documents ingested yet.</p></div>`;
      return;
    }

    // Group chunks by doc_id
    const byDoc = {};
    for (const c of chunks) {
      if (!byDoc[c.doc_id]) byDoc[c.doc_id] = [];
      byDoc[c.doc_id].push(c);
    }

    chunkTree.innerHTML = documents.map(doc => {
      const docChunks = (byDoc[doc.doc_id] || []).sort((a, b) => a.chunk_index - b.chunk_index);
      const id = `tree-${escapeHtml(doc.doc_id)}`;
      return `
        <div class="tree-doc">
          <button class="tree-doc-header" onclick="toggleTreeDoc('${id}')">
            <svg class="tree-arrow" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><polyline points="13 2 13 9 20 9"/></svg>
            <span class="tree-doc-name">${escapeHtml(doc.name)}</span>
            <span class="tree-doc-count">${docChunks.length} chunks</span>
          </button>
          <div class="tree-chunks hidden" id="${id}">
            ${docChunks.map(c => `
              <div class="tree-chunk">
                <div class="tree-chunk-header">
                  <span class="source-badge">Chunk ${c.chunk_index}</span>
                  <span class="tree-chunk-chars">${c.char_length} chars</span>
                </div>
                <div class="tree-chunk-text">${escapeHtml(c.text)}</div>
              </div>`).join('')}
          </div>
        </div>`;
    }).join('');
  } catch {
    // server not running
  }
}

function toggleTreeDoc(id) {
  const el = document.getElementById(id);
  const arrow = el.previousElementSibling.querySelector('.tree-arrow');
  const isOpen = !el.classList.contains('hidden');
  el.classList.toggle('hidden', isOpen);
  arrow.style.transform = isOpen ? '' : 'rotate(90deg)';
}

async function runLiveSearch() {
  const question = liveSearchInput.value.trim();
  if (!question) return;

  liveSearchResults.innerHTML = `
    <div class="live-search-loading">
      <div class="loading-dots"><span></span><span></span><span></span></div>
      <span>Searching vector store...</span>
    </div>`;

  try {
    const res = await fetch(`${API_BASE}/search_raw`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    });
    const data = await res.json();

    if (!res.ok) {
      liveSearchResults.innerHTML = `<div class="live-search-empty">${escapeHtml(data.detail || 'Search failed')}</div>`;
      return;
    }

    if (!data.results.length) {
      liveSearchResults.innerHTML = `<div class="live-search-empty">No results found.</div>`;
      return;
    }

    const scoreLabel = data.results[0].score_type === 'rerank' ? 'Rerank score' : 'Cosine similarity';

    liveSearchResults.innerHTML = `
      <div class="live-search-meta">${data.results.length} chunks retrieved &nbsp;·&nbsp; ${scoreLabel}</div>
      ${data.results.map((r, i) => {
        const pct = r.score_type === 'rerank'
          ? Math.round(100 / (1 + Math.exp(-r.score)))
          : Math.round(r.score * 100);
        const cls = pct >= 70 ? 'score-high' : pct >= 40 ? 'score-mid' : 'score-low';
        return `
          <div class="source-item">
            <div class="source-header">
              <span class="source-badge">Chunk ${r.chunk_id}</span>
              <span class="source-name">${escapeHtml(r.document_name)}</span>
              <span class="score-badge ${cls}" title="${scoreLabel}: ${r.score.toFixed(4)}">${pct}%</span>
            </div>
            <div class="source-text">${escapeHtml(r.chunk_text)}</div>
          </div>`;
      }).join('')}`;
  } catch {
    liveSearchResults.innerHTML = `<div class="live-search-empty">Could not connect to the server.</div>`;
  }
}

// ── Init ──
initTheme();
loadDocuments();
