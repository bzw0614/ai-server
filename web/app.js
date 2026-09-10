/**
 * 仿 ChatGPT 聊天前端。
 * 只依赖后端两个接口：
 *   POST /api/chat         -> { message, temperature } => { message }
 *   POST /api/chat/stream  -> { message, temperature } => SSE（text/event-stream）
 */

const API_CHAT = '/api/chat';
const API_STREAM = '/api/chat/stream';
const STORE_KEY = 'ai-server-chat-v1';
const DEFAULT_TEMPERATURE = 0.7;

const $ = (sel) => document.querySelector(sel);

const els = {
  sidebar: $('#sidebar'),
  sidebarMask: $('#sidebarMask'),
  chatList: $('#chatList'),
  searchInput: $('#searchInput'),
  messages: $('#messages'),
  chatScroll: $('#chatScroll'),
  title: $('#chatTitle'),
  statusDot: $('#statusDot'),
  input: $('#input'),
  composer: $('#composer'),
  sendBtn: $('#sendBtn'),
  temperature: $('#temperature'),
  temperatureValue: $('#temperatureValue'),
  streamToggle: $('#streamToggle'),
  toast: $('#toast'),
  emptyTemplate: $('#emptyTemplate'),
  scrollBottomBtn: $('#scrollBottomBtn'),
};

/* ------------------------------------------------------------------ */
/* 状态与持久化（会话记录存在浏览器 localStorage，后端接口本身无状态）  */
/* ------------------------------------------------------------------ */

const state = {
  conversations: [],
  currentId: null,
  settings: { temperature: DEFAULT_TEMPERATURE, stream: true, theme: 'dark' },
  keyword: '',
  busy: false,
  controller: null,
};

function uid() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
}

function load() {
  try {
    const raw = localStorage.getItem(STORE_KEY);
    if (!raw) return;
    const data = JSON.parse(raw);
    state.conversations = Array.isArray(data.conversations) ? data.conversations : [];
    state.currentId = data.currentId || null;
    state.settings = Object.assign(state.settings, data.settings || {});
  } catch (err) {
    console.warn('本地会话读取失败，已忽略：', err);
  }
}

function save() {
  try {
    localStorage.setItem(
      STORE_KEY,
      JSON.stringify({
        conversations: state.conversations,
        currentId: state.currentId,
        settings: state.settings,
      })
    );
  } catch (err) {
    console.warn('本地会话保存失败：', err);
  }
}

const currentConv = () => state.conversations.find((c) => c.id === state.currentId) || null;

function createConversation() {
  const conv = {
    id: uid(),
    title: '新的对话',
    createdAt: Date.now(),
    updatedAt: Date.now(),
    messages: [],
  };
  state.conversations.unshift(conv);
  state.currentId = conv.id;
  return conv;
}

/* ------------------------------------------------------------------ */
/* 小工具                                                              */
/* ------------------------------------------------------------------ */

function escapeHtml(str) {
  return String(str ?? '').replace(
    /[&<>"']/g,
    (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])
  );
}

let toastTimer = null;
function toast(message, ok = false) {
  els.toast.textContent = message;
  els.toast.classList.toggle('ok', ok);
  els.toast.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    els.toast.hidden = true;
  }, 3200);
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    // http 或者旧浏览器下 clipboard 可能不可用，退回 textarea 方案
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    const ok = document.execCommand('copy');
    ta.remove();
    return ok;
  }
}

/* ------------------------------------------------------------------ */
/* 轻量 Markdown 渲染（不引第三方库，先转义再生成标签，避免 XSS）        */
/* ------------------------------------------------------------------ */

const T = '\u0000';

function renderInline(text) {
  return text
    .replace(/\*\*\*([^*\n]+)\*\*\*/g, '<strong><em>$1</em></strong>')
    .replace(/\*\*([^*\n]+)\*\*/g, '<strong>$1</strong>')
    .replace(/(^|[^*])\*([^*\n]+)\*/g, '$1<em>$2</em>')
    .replace(/~~([^~\n]+)~~/g, '<del>$1</del>')
    .replace(
      /\[([^\]\n]+)\]\((https?:\/\/[^\s)]+)\)/g,
      '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>'
    );
}

function isTableSeparator(line) {
  return /^\s*\|?[\s:|-]+\|[\s:|-]*$/.test(line) && line.includes('-');
}

function splitRow(line) {
  return line
    .replace(/^\s*\|/, '')
    .replace(/\|\s*$/, '')
    .split('|')
    .map((c) => c.trim());
}

function renderBlock(block, codes) {
  const text = block.trim();
  if (!text) return '';

  // 单独一行的代码块占位符
  const onlyCode = text.match(new RegExp(`^${T}C(\\d+)${T}$`));
  if (onlyCode) return codeBlockHtml(codes[Number(onlyCode[1])]);

  if (/^(-{3,}|\*{3,}|_{3,})$/.test(text)) return '<hr>';

  const heading = text.match(/^(#{1,6})\s+(.*)$/);
  if (heading && !heading[2].includes('\n')) {
    const level = heading[1].length;
    return `<h${level}>${renderInline(heading[2].trim())}</h${level}>`;
  }

  const lines = text.split(/\r?\n/);

  // 引用（注意 ">" 在上一步已经被转义成 "&gt;"）
  if (lines.every((l) => /^\s*(?:&gt;|>)/.test(l))) {
    const inner = lines.map((l) => l.replace(/^\s*(?:&gt;|>)\s?/, '')).join('<br>');
    return `<blockquote>${renderInline(inner)}</blockquote>`;
  }

  // 表格：表头 + 分隔行
  if (lines.length >= 2 && lines[0].includes('|') && isTableSeparator(lines[1])) {
    const head = splitRow(lines[0]);
    const body = lines.slice(2).map(splitRow);
    const th = head.map((c) => `<th>${renderInline(c)}</th>`).join('');
    const trs = body
      .map((row) => `<tr>${row.map((c) => `<td>${renderInline(c)}</td>`).join('')}</tr>`)
      .join('');
    return `<table><thead><tr>${th}</tr></thead><tbody>${trs}</tbody></table>`;
  }

  // 列表
  const isUl = lines.every((l) => /^\s*[-*+]\s+/.test(l));
  const isOl = lines.every((l) => /^\s*\d+[.)]\s+/.test(l));
  if (isUl || isOl) {
    const items = lines
      .map((l) => l.replace(/^\s*(?:[-*+]|\d+[.)])\s+/, ''))
      .map((l) => `<li>${renderInline(l)}</li>`)
      .join('');
    return isOl ? `<ol>${items}</ol>` : `<ul>${items}</ul>`;
  }

  return `<p>${renderInline(text).replace(/\r?\n/g, '<br>')}</p>`;
}

function codeBlockHtml({ lang, code }) {
  return (
    '<div class="code-block">' +
    '<div class="code-head">' +
    `<span>${escapeHtml(lang || 'text')}</span>` +
    '<button class="code-copy" type="button" data-copy-code>复制</button>' +
    '</div>' +
    `<pre><code>${escapeHtml(code)}</code></pre>` +
    '</div>'
  );
}

function renderMarkdown(src) {
  const codes = [];
  const inlines = [];

  // 1. 先摘出 ``` 代码块，避免代码里的 # * _ 被当成 Markdown
  let text = String(src ?? '').replace(
    /```([^\n`]*)\r?\n?([\s\S]*?)(?:```|$)/g,
    (_m, lang, code) => {
      codes.push({ lang: String(lang || '').trim(), code: code.replace(/\s+$/, '') });
      return `${T}C${codes.length - 1}${T}`;
    }
  );

  // 2. 摘出行内代码
  text = text.replace(/`([^`\n]+)`/g, (_m, code) => {
    inlines.push(code);
    return `${T}I${inlines.length - 1}${T}`;
  });

  // 3. 转义，之后生成的标签都是我们自己的，不会被注入
  text = escapeHtml(text);

  // 4. 按空行切块
  const html = text
    .split(/\r?\n{2,}/)
    .map((block) => renderBlock(block, codes))
    .join('');

  // 5. 还原代码占位符
  return html
    .replace(new RegExp(`${T}C(\\d+)${T}`, 'g'), (_m, i) => codeBlockHtml(codes[Number(i)] || { code: '' }))
    .replace(new RegExp(`${T}I(\\d+)${T}`, 'g'), (_m, i) => `<code>${escapeHtml(inlines[Number(i)] ?? '')}</code>`);
}

/* ------------------------------------------------------------------ */
/* 渲染                                                                */
/* ------------------------------------------------------------------ */

function groupLabel(ts) {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  if (ts >= today) return '今天';
  if (ts >= today - 86400000) return '昨天';
  if (ts >= today - 7 * 86400000) return '过去 7 天';
  return '更早';
}

function renderSidebar() {
  els.chatList.innerHTML = '';
  const keyword = state.keyword.trim().toLowerCase();
  const list = state.conversations
    .filter((c) => {
      if (!keyword) return true;
      const inTitle = c.title.toLowerCase().includes(keyword);
      const inMsg = c.messages.some((m) => (m.content || '').toLowerCase().includes(keyword));
      return inTitle || inMsg;
    })
    .sort((a, b) => b.updatedAt - a.updatedAt);

  if (!list.length) {
    const empty = document.createElement('div');
    empty.className = 'chat-list-empty';
    empty.textContent = keyword ? '没有匹配的对话' : '还没有历史对话';
    els.chatList.appendChild(empty);
    return;
  }

  let group = '';
  for (const conv of list) {
    const label = groupLabel(conv.updatedAt);
    if (label !== group) {
      group = label;
      const title = document.createElement('div');
      title.className = 'chat-group-title';
      title.textContent = label;
      els.chatList.appendChild(title);
    }

    const item = document.createElement('div');
    item.className = 'chat-item' + (conv.id === state.currentId ? ' active' : '');
    item.dataset.id = conv.id;
    item.tabIndex = 0;

    const name = document.createElement('span');
    name.className = 'chat-item-title';
    name.textContent = conv.title;

    const del = document.createElement('button');
    del.className = 'chat-item-del';
    del.type = 'button';
    del.title = '删除对话';
    del.textContent = '×';
    del.dataset.delete = conv.id;

    item.append(name, del);
    els.chatList.appendChild(item);
  }
}

function messageActionsHtml(msg) {
  const buttons = ['<button class="msg-action" type="button" data-copy-msg>复制</button>'];
  if (msg.role === 'assistant') {
    buttons.push('<button class="msg-action" type="button" data-regenerate>重新生成</button>');
  }
  return buttons.join('');
}

function createMessageEl(msg) {
  const wrap = document.createElement('div');
  wrap.className = `msg ${msg.role}`;
  wrap.dataset.id = msg.id;

  const avatar = document.createElement('div');
  avatar.className = 'msg-avatar';
  avatar.textContent = msg.role === 'user' ? '我' : '⚡';

  const body = document.createElement('div');
  body.className = 'msg-body';

  const name = document.createElement('div');
  name.className = 'msg-name';
  name.textContent = msg.role === 'user' ? '你' : 'AI 助手';

  const content = document.createElement('div');
  content.className = 'msg-content';

  const actions = document.createElement('div');
  actions.className = 'msg-actions';
  actions.innerHTML = messageActionsHtml(msg);

  body.append(name, content);
  if (msg.reasoning) {
    const details = document.createElement('details');
    details.className = 'reasoning';
    details.innerHTML = '<summary>思考过程</summary><div class="reasoning-body md"></div>';
    body.insertBefore(details, content);
  }
  body.appendChild(actions);
  wrap.append(avatar, body);
  return wrap;
}

function paintMessage(el, msg, streaming) {
  const content = el.querySelector('.msg-content');
  if (msg.error) {
    content.className = 'msg-content';
    content.innerHTML = `<div class="msg-error">${escapeHtml(msg.error)}</div>`;
  } else if (msg.role === 'user') {
    content.className = 'msg-content';
    content.textContent = msg.content;
  } else {
    content.className = 'msg-content md';
    if (msg.content) {
      content.innerHTML =
        renderMarkdown(msg.content) + (streaming ? '<span class="cursor-blink"></span>' : '');
    } else if (streaming) {
      content.innerHTML = '<div class="thinking"><i></i><i></i><i></i></div>';
    } else {
      content.innerHTML = '';
    }
  }

  const reasoning = el.querySelector('.reasoning-body');
  if (reasoning && msg.reasoning) {
    reasoning.innerHTML = renderMarkdown(msg.reasoning);
  }

  // 重新生成只对最后一条助手消息开放
  const regen = el.querySelector('[data-regenerate]');
  if (regen) {
    const conv = currentConv();
    const last = conv && conv.messages[conv.messages.length - 1];
    regen.disabled = streaming || !last || last.id !== msg.id;
    regen.style.opacity = regen.disabled ? '0.4' : '1';
  }
}

function renderMessages() {
  els.messages.innerHTML = '';
  const conv = currentConv();
  if (!conv || !conv.messages.length) {
    els.messages.appendChild(els.emptyTemplate.content.cloneNode(true));
    els.title.textContent = conv ? conv.title : '新的对话';
    return;
  }
  els.title.textContent = conv.title;
  for (const msg of conv.messages) {
    const el = createMessageEl(msg);
    paintMessage(el, msg, false);
    els.messages.appendChild(el);
  }
}

function liveEl(msgId) {
  return els.messages.querySelector(`.msg[data-id="${msgId}"]`);
}

/* 滚动：只有用户本来就贴着底部时才自动跟随新内容 */
let stickToBottom = true;

function isNearBottom() {
  const el = els.chatScroll;
  return el.scrollHeight - el.scrollTop - el.clientHeight < 90;
}

function scrollToBottom(force = false) {
  if (force || stickToBottom) {
    els.chatScroll.scrollTop = els.chatScroll.scrollHeight;
  }
}

/* ------------------------------------------------------------------ */
/* 发送                                                                */
/* ------------------------------------------------------------------ */

function setBusy(busy) {
  state.busy = busy;
  els.sendBtn.classList.toggle('busy', busy);
  els.sendBtn.disabled = !busy && !els.input.value.trim();
  els.statusDot.classList.toggle('active', busy);
}

function makeTitle(text) {
  const t = text.replace(/\s+/g, ' ').trim();
  return t.length > 22 ? `${t.slice(0, 22)}…` : t || '新的对话';
}

async function readError(res) {
  try {
    const data = await res.json();
    if (typeof data.detail === 'string') return data.detail;
    if (Array.isArray(data.detail) && data.detail.length) {
      return `参数校验失败：${data.detail[0].msg || ''}`.trim();
    }
    if (data.message) return data.message;
  } catch {
    /* 忽略：响应体不是 JSON */
  }
  if (res.status === 422) return '请求参数不合法（message 不能为空，temperature 需在 0~2 之间）';
  return `请求失败（HTTP ${res.status}）`;
}

/** 流式：解析后端转发的 SSE，逐块回调增量文本 */
async function requestStream(payload, { signal, onDelta, onReasoning }) {
  const res = await fetch(API_STREAM, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal,
  });
  if (!res.ok) throw new Error(await readError(res));
  if (!res.body) throw new Error('当前浏览器不支持流式响应');

  const reader = res.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';

  const handleEvent = (raw) => {
    const dataLines = [];
    for (const line of raw.split(/\r?\n/)) {
      if (!line || line.startsWith(':')) continue;
      if (line.startsWith('data:')) dataLines.push(line.slice(5).trimStart());
    }
    const data = dataLines.join('\n').trim();
    if (!data || data === '[DONE]') return;

    let json;
    try {
      json = JSON.parse(data);
    } catch {
      return; // 上游偶尔会插入心跳之类的非 JSON 行，直接跳过
    }

    if (json.error) throw new Error(json.error.message || '模型服务返回错误');

    const delta = json.choices && json.choices[0] && json.choices[0].delta;
    if (!delta) return;
    if (delta.reasoning_content) onReasoning(delta.reasoning_content);
    if (delta.content) onDelta(delta.content);
  };

  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let index;
    while ((index = buffer.search(/\r?\n\r?\n/)) !== -1) {
      const raw = buffer.slice(0, index);
      buffer = buffer.slice(index).replace(/^\r?\n\r?\n/, '');
      handleEvent(raw);
    }
  }
  buffer += decoder.decode();
  if (buffer.trim()) handleEvent(buffer);
}

/** 非流式：一次性拿完整回答 */
async function requestOnce(payload, { signal }) {
  const res = await fetch(API_CHAT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal,
  });
  if (!res.ok) throw new Error(await readError(res));
  const data = await res.json();
  return data.message ?? '';
}

async function sendMessage(rawText) {
  const text = String(rawText ?? '').trim();
  if (!text || state.busy) return;

  const conv = currentConv() || createConversation();
  if (conv.title === '新的对话') conv.title = makeTitle(text);
  conv.updatedAt = Date.now();
  conv.messages.push({ id: uid(), role: 'user', content: text });

  const assistant = { id: uid(), role: 'assistant', content: '', reasoning: '' };
  conv.messages.push(assistant);

  els.input.value = '';
  autoResize();
  stickToBottom = true;
  renderMessages();
  renderSidebar();
  scrollToBottom(true);
  save();

  const el = liveEl(assistant.id);
  if (!el) return;

  // 流式时按帧刷新 Markdown，避免每个 token 都重排一次
  let frame = null;
  let streaming = true;
  const refresh = () => {
    if (frame) return;
    frame = requestAnimationFrame(() => {
      frame = null;
      paintMessage(el, assistant, streaming);
      scrollToBottom();
    });
  };

  const controller = new AbortController();
  state.controller = controller;
  setBusy(true);

  const payload = { message: text, temperature: state.settings.temperature };

  try {
    if (state.settings.stream) {
      await requestStream(payload, {
        signal: controller.signal,
        onDelta: (chunk) => {
          assistant.content += chunk;
          refresh();
        },
        onReasoning: (chunk) => {
          assistant.reasoning += chunk;
          refresh();
        },
      });
    } else {
      assistant.content = await requestOnce(payload, { signal: controller.signal });
    }

    if (!assistant.content.trim() && !assistant.reasoning.trim()) {
      assistant.error = '模型没有返回内容，请重试。';
    }
  } catch (err) {
    if (err.name === 'AbortError') {
      assistant.content = assistant.content.trim() ? `${assistant.content.trimEnd()}\n\n（已停止生成）` : '（已停止生成）';
    } else {
      assistant.error = err.message || '请求出错，请稍后重试。';
      toast(assistant.error);
    }
  } finally {
    streaming = false;
    if (frame) cancelAnimationFrame(frame);
    frame = null;
    state.controller = null;
    setBusy(false);
    conv.updatedAt = Date.now();
    paintMessage(el, assistant, false);
    renderSidebar();
    scrollToBottom();
    save();
    els.input.focus();
  }
}

function stopGeneration() {
  if (state.controller) state.controller.abort();
}

function regenerate() {
  const conv = currentConv();
  if (!conv || state.busy) return;
  let lastUserIndex = -1;
  for (let i = conv.messages.length - 1; i >= 0; i -= 1) {
    if (conv.messages[i].role === 'user') {
      lastUserIndex = i;
      break;
    }
  }
  if (lastUserIndex === -1) return;
  const text = conv.messages[lastUserIndex].content;
  // 丢掉最后一问之后的所有内容，然后重新提问
  conv.messages = conv.messages.slice(0, lastUserIndex);
  sendMessage(text);
}

/* ------------------------------------------------------------------ */
/* 交互绑定                                                            */
/* ------------------------------------------------------------------ */

function autoResize() {
  els.input.style.height = 'auto';
  els.input.style.height = `${Math.min(els.input.scrollHeight, 200)}px`;
}

function selectConversation(id) {
  if (state.busy) return;
  state.currentId = id;
  stickToBottom = true;
  renderSidebar();
  renderMessages();
  scrollToBottom(true);
  save();
  closeSidebarOnMobile();
}

function deleteConversation(id) {
  const index = state.conversations.findIndex((c) => c.id === id);
  if (index === -1) return;
  state.conversations.splice(index, 1);
  if (state.currentId === id) {
    state.currentId = state.conversations.length ? state.conversations[0].id : null;
  }
  if (!state.conversations.length) createConversation();
  renderSidebar();
  renderMessages();
  save();
}

function openSidebar() {
  els.sidebar.classList.add('open');
  els.sidebarMask.hidden = false;
}

function closeSidebarOnMobile() {
  if (window.matchMedia('(max-width: 860px)').matches) {
    els.sidebar.classList.remove('open');
    els.sidebarMask.hidden = true;
  }
}

function applyTheme() {
  document.documentElement.dataset.theme = state.settings.theme;
}

function initEvents() {
  els.composer.addEventListener('submit', (e) => {
    e.preventDefault();
    sendMessage(els.input.value);
  });

  els.sendBtn.addEventListener('click', (e) => {
    if (state.busy) {
      e.preventDefault();
      stopGeneration();
    }
  });

  els.input.addEventListener('input', () => {
    autoResize();
    els.sendBtn.disabled = !state.busy && !els.input.value.trim();
  });

  els.input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
      e.preventDefault();
      sendMessage(els.input.value);
    }
  });

  $('#newChatBtn').addEventListener('click', () => {
    if (state.busy) return;
    createConversation();
    renderSidebar();
    renderMessages();
    save();
    els.input.focus();
    closeSidebarOnMobile();
  });

  els.searchInput.addEventListener('input', () => {
    state.keyword = els.searchInput.value;
    renderSidebar();
  });

  els.chatList.addEventListener('click', (e) => {
    const del = e.target.closest('[data-delete]');
    if (del) {
      e.stopPropagation();
      deleteConversation(del.dataset.delete);
      return;
    }
    const item = e.target.closest('.chat-item');
    if (item) selectConversation(item.dataset.id);
  });

  els.chatList.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      const item = e.target.closest('.chat-item');
      if (item) {
        e.preventDefault();
        selectConversation(item.dataset.id);
      }
    }
  });

  $('#clearAllBtn').addEventListener('click', () => {
    if (state.busy || !state.conversations.length) return;
    if (!window.confirm('确定清空全部历史对话？该操作不可撤销。')) return;
    state.conversations = [];
    createConversation();
    renderSidebar();
    renderMessages();
    save();
  });

  els.temperature.addEventListener('input', () => {
    state.settings.temperature = Number(els.temperature.value);
    els.temperatureValue.textContent = state.settings.temperature.toFixed(1);
    save();
  });

  els.streamToggle.addEventListener('change', () => {
    state.settings.stream = els.streamToggle.checked;
    save();
  });

  $('#themeBtn').addEventListener('click', () => {
    state.settings.theme = state.settings.theme === 'dark' ? 'light' : 'dark';
    applyTheme();
    save();
  });

  $('#openSidebarBtn').addEventListener('click', openSidebar);
  $('#closeSidebarBtn').addEventListener('click', closeSidebarOnMobile);
  els.sidebarMask.addEventListener('click', closeSidebarOnMobile);

  els.chatScroll.addEventListener('scroll', () => {
    stickToBottom = isNearBottom();
    els.scrollBottomBtn.hidden = stickToBottom;
  });

  els.scrollBottomBtn.addEventListener('click', () => {
    stickToBottom = true;
    els.scrollBottomBtn.hidden = true;
    scrollToBottom(true);
  });

  // 消息区里的复制 / 重新生成 / 代码块复制，统一事件委托
  els.messages.addEventListener('click', async (e) => {
    const codeBtn = e.target.closest('[data-copy-code]');
    if (codeBtn) {
      const code = codeBtn.closest('.code-block').querySelector('code').textContent;
      toast((await copyText(code)) ? '代码已复制' : '复制失败', true);
      return;
    }
    const copyMsg = e.target.closest('[data-copy-msg]');
    if (copyMsg) {
      const wrap = copyMsg.closest('.msg');
      const conv = currentConv();
      const msg = conv && conv.messages.find((m) => m.id === wrap.dataset.id);
      if (msg) toast((await copyText(msg.content)) ? '已复制到剪贴板' : '复制失败', true);
      return;
    }
    if (e.target.closest('[data-regenerate]')) regenerate();
  });

  // 点击示例问题直接发送
  els.messages.addEventListener('click', (e) => {
    const card = e.target.closest('.suggestion');
    if (card) sendMessage(card.dataset.prompt);
  });

  window.addEventListener('resize', () => {
    if (!window.matchMedia('(max-width: 860px)').matches) {
      els.sidebar.classList.remove('open');
      els.sidebarMask.hidden = true;
    }
  });
}

function init() {
  load();
  applyTheme();
  els.temperature.value = state.settings.temperature;
  els.temperatureValue.textContent = Number(state.settings.temperature).toFixed(1);
  els.streamToggle.checked = state.settings.stream;
  if (!state.conversations.length) createConversation();
  if (!currentConv()) state.currentId = state.conversations[0].id;

  renderSidebar();
  renderMessages();
  initEvents();
  autoResize();
  els.sendBtn.disabled = !els.input.value.trim();
  scrollToBottom(true);
  els.input.focus();
}

init();
