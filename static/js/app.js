const chat = document.getElementById("chat");
const input = document.getElementById("message-input");
const sendBtn = document.getElementById("send-btn");
const statusBadge = document.getElementById("status-badge");

const ws = new WebSocket(`ws://${location.host}/ws`);

let currentBubble = null;

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === "status") {
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
    sendBtn.disabled = false;
    input.disabled = false;
    input.focus();
  }
};

ws.onclose = () => setStatus("DISCONNECTED");

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

sendBtn.addEventListener("click", send);

input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    send();
  }
});

// Auto-resize textarea
input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 160) + "px";
});
