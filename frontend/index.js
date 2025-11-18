// If executed with Node, exit with a helpful message.
if (typeof document === 'undefined') {
  console.error('This script is meant to run in the browser. Open frontend/index.html in a browser.');
  if (typeof process !== 'undefined' && process.exit) process.exit(1);
}

const API_URL = 'http://127.0.0.1:5000/api/query';

const el = {
  messages: document.getElementById('messages'),
  form: document.getElementById('chat-form'),
  input: document.getElementById('user-input'),
  nResults: document.getElementById('n-results'),
  status: document.getElementById('status'),
  send: document.getElementById('send-btn'),
};

function scrollToBottom() {
  el.messages.scrollTop = el.messages.scrollHeight;
}

function addMessage(role, text) {
  const div = document.createElement('div');
  div.className = `msg ${role === 'user' ? 'user' : 'ai'}`;
  div.textContent = text;
  el.messages.appendChild(div);
  scrollToBottom();
  return div;
}

function addSources(sources) {
  if (!Array.isArray(sources) || sources.length === 0) return;
  const wrap = document.createElement('div');
  wrap.className = 'sources';
  wrap.innerHTML = '<strong>Sources</strong>';
  sources.forEach((src, i) => {
    const item = document.createElement('div');
    item.className = 'item';
    const snippet = String(src).replace(/\n/g, ' ').slice(0, 200) + (String(src).length > 200 ? '…' : '');
    item.textContent = `[${i + 1}] ${snippet}`;
    wrap.appendChild(item);
  });
  el.messages.appendChild(wrap);
  scrollToBottom();
}

function setBusy(busy, msg = '') {
  el.input.disabled = busy;
  el.nResults.disabled = busy;
  el.send.disabled = busy;
  el.status.textContent = msg;
}

el.form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const query = el.input.value.trim();
  if (!query) return;

  const nResults = parseInt(el.nResults.value) || 3;

  addMessage('user', query);
  el.input.value = '';
  setBusy(true, 'Thinking...');

  try {
    const res = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, n_results: nResults }),
    });

    if (!res.ok) {
      const text = await res.text().catch(() => '');
      throw new Error(`HTTP ${res.status} ${res.statusText}${text ? ` - ${text}` : ''}`);
    }

    const data = await res.json();
    const answer = data?.answer ?? '(no answer)';
    addMessage('ai', answer);

    const sources = data?.retrieved_context;
    if (Array.isArray(sources) && sources.length > 0) {
      addSources(sources);
    }
  } catch (err) {
    addMessage('ai', `Error: ${err.message}`);
  } finally {
    setBusy(false, '');
    el.input.focus();
  }
});

// Optional welcome message
addMessage('ai', 'Hi! Ask me anything. Type your question below and press Enter.');