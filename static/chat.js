// static/chat.js  – tiny vanilla helper
//----------------------------------------------------------
const chatBox  = document.querySelector("#chat");
const gallery  = document.querySelector("#gallery");
const msgInput = document.querySelector("#msg");
let   socket   = null;

// ---------- gallery ----------
// show only the items returned by the LLM
function showRecommendations(files = [], items = []) {
  gallery.innerHTML = files.map((f, i) => `
      <figure>
        <img src="/images/${f}" alt="${items[i] || ''}">
        <figcaption>${items[i] || ''}</figcaption>
      </figure>`).join("");
}

// ---------- chat UI ----------
function appendChat(text, cls = "bot") {
  const div = document.createElement("div");
  div.className = cls;
  div.textContent = text;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

// ---------- web-socket ----------
function ensureWS() {
  if (socket) return;
  socket = new WebSocket(`ws://${location.host}/ws`);

  socket.onmessage = ev => {
    let data;
    try { data = JSON.parse(ev.data); } catch { data = null; }

    // system / plain-text fallback
    if (!data) {
      appendChat(ev.data, "bot");
      return;
    }

    if (data.system) {
      appendChat(data.system, "system");
      return;
    }

    if (data.commentary) {
      appendChat(data.commentary, "bot");

      if (Array.isArray(data.files) && data.files.length) {
        showRecommendations(data.files, data.items || []);
      }
    }
  };

  socket.onclose = () => { socket = null; };
}

// open WS immediately (so user doesn’t need to say “Hi” twice)
ensureWS();

// ---------- wardrobe helpers ----------
async function doUpload() {
  const files = document.querySelector("#files").files;
  if (!files.length) return alert("Pick image files first");

  const fd = new FormData();
  for (const f of files) fd.append("files", f, f.name);

  await fetch('/upload?auto=false', { method: 'POST', body: fd });
  appendChat("⏳ Uploaded!  Click *Process wardrobe* next.", "system");
}

async function processWardrobe() {
  appendChat("⏳ Processing wardrobe …", "system");
  const r = await fetch('/process', { method: 'POST' });
  const j = await r.json();

  if (j.status === "started") {
    appendChat("🔎 Extracting metadata – this can take more than few minutes depends on number of clothing…", "system");
  } else {
    appendChat("✅ Nothing new to process.", "system");
  }
}

// ---------- send user message ----------
async function sendMsg() {
  const txt = msgInput.value.trim();
  if (!txt) return;

  // quick check: do we have any wardrobe data?
  const w = await fetch('/wardrobe').then(r => r.json());
  if (!w.length) {
    alert("Upload & process your wardrobe first!");
    return;
  }

  appendChat(txt, "user");
  msgInput.value = "";
  ensureWS();
  socket.send(txt);
}

document.querySelector("#send").onclick = sendMsg;
msgInput.addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey) sendMsg();
});
