const chat = document.getElementById("chat");
const input = document.getElementById("message-input");
const sendBtn = document.getElementById("send-btn");
const micBtn = document.getElementById("mic-btn");
const statusBadge = document.getElementById("status-badge");
const stopTtsBar = document.getElementById("stop-tts-bar");
const stopTtsBtn = document.getElementById("stop-tts-btn");

const ws = new WebSocket(`ws://${location.host}/ws`);

let currentBubble = null;
let mediaRecorder = null;
let audioChunks = [];
let recording = false;

// ── WebSocket ──────────────────────────────────────────────

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === "record_start") {
    if (!recording) startRecording();
  } else if (data.type === "record_stop") {
    if (recording) stopRecording();
  } else if (data.type === "status") {
    setStatus(data.value);
  } else if (data.type === "token") {
    if (!currentBubble) {
      currentBubble = addBubble("assistant", "");
      currentBubble.classList.add("streaming");
    }
    currentBubble.textContent += data.value;
    scrollToBottom();
  } else if (data.type === "done") {
    if (currentBubble) {
      currentBubble.classList.remove("streaming");
      currentBubble = null;
    }
  } else if (data.type === "tts_start") {
    stopTtsBar.hidden = false;
  } else if (data.type === "tts_end") {
    stopTtsBar.hidden = true;
    sendBtn.disabled = false;
    input.disabled = false;
    input.focus();
  }
};

ws.onclose = () => setStatus("DISCONNECTED");

// ── Send ───────────────────────────────────────────────────

function send() {
  const text = input.value.trim();
  if (!text || ws.readyState !== WebSocket.OPEN) return;

  addBubble("user", text);
  input.value = "";
  input.style.height = "auto";
  sendBtn.disabled = true;
  input.disabled = true;
  scrollToBottom();

  ws.send(JSON.stringify({ message: text }));
}

// ── Voice recording ────────────────────────────────────────

micBtn.addEventListener("click", async () => {
  if (!recording) {
    await startRecording();
  } else {
    stopRecording();
  }
});

async function startRecording() {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const mimeType = getSupportedMimeType();
  mediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType } : {});
  audioChunks = [];

  mediaRecorder.ondataavailable = (e) => {
    if (e.data.size > 0) audioChunks.push(e.data);
  };

  mediaRecorder.onstop = async () => {
    stream.getTracks().forEach((t) => t.stop());
    const blob = new Blob(audioChunks, { type: mimeType || "audio/webm" });
    await transcribe(blob, mimeType);
  };

  mediaRecorder.start();
  recording = true;
  micBtn.classList.add("recording");
  setStatus("LISTENING");
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();
  }
  recording = false;
  micBtn.classList.remove("recording");
  setStatus("PROCESSING");
}

async function transcribe(blob, mimeType) {
  const ext = (mimeType || "").includes("mp4") ? "audio.mp4" : "audio.webm";
  const formData = new FormData();
  formData.append("file", blob, ext);

  try {
    const res = await fetch("/transcribe", { method: "POST", body: formData });
    const { text } = await res.json();
    if (text) {
      input.value = text;
      input.style.height = "auto";
      input.style.height = Math.min(input.scrollHeight, 160) + "px";
      send();
    }
  } catch (err) {
    console.error("Transcription error:", err);
  }
  setStatus("READY");
}

function getSupportedMimeType() {
  const types = [
    "audio/webm;codecs=opus",
    "audio/webm",
    "audio/ogg;codecs=opus",
    "audio/mp4",
  ];
  return types.find((t) => MediaRecorder.isTypeSupported(t)) || "";
}

// ── Helpers ────────────────────────────────────────────────

function addBubble(role, text) {
  const div = document.createElement("div");
  div.className = `message ${role}`;
  div.textContent = text;
  chat.appendChild(div);
  return div;
}

function setStatus(value) {
  statusBadge.textContent = value;
  statusBadge.className = value === "PROCESSING" ? "processing" : "";
}

function scrollToBottom() {
  chat.scrollTop = chat.scrollHeight;
}

// ── Events ─────────────────────────────────────────────────

sendBtn.addEventListener("click", send);

stopTtsBtn.addEventListener("click", () => {
  ws.send(JSON.stringify({ type: "stop_tts" }));
  stopTtsBar.hidden = true;
});

input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    send();
  }
});

input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 160) + "px";
});
