const chatbox = document.getElementById("chatbox");
const userInput = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");
const mainTitle = document.getElementById("mainTitle");
const historyUl = document.getElementById("history");
const newChatBtn = document.getElementById("newChatBtn");
const weatherBtn = document.getElementById("weatherBtn");
const weatherAlert = document.getElementById("weatherAlert");
const sidebar = document.getElementById('sidebar');
const sidebarOverlay = document.getElementById('sidebarOverlay');
const mobileSidebarBtn = document.getElementById('mobileSidebarBtn');
const sidebarLogoBtn = document.getElementById('sidebarLogoBtn');

let currentChat = [];
let isFirstSend = true;
let currentHistoryIdx = null;

// --- Sidebar History Logic ---
function loadHistorySidebar() {
  const history = JSON.parse(localStorage.getItem('chatSidebarHistory') || '[]');
  historyUl.innerHTML = "";
  history.forEach((h, idx) => {
    const li = document.createElement("li");
    li.className = "history-item";
    li.innerHTML = `
      <span class="history-title">${h.title}</span>
      <span class="ellipsis" title="Hapus">&#8230;</span>
    `;
    li.querySelector('.ellipsis').onclick = (e) => {
      e.stopPropagation();
      if (confirm("Hapus chat ini?")) {
        deleteSidebarHistory(idx);
      }
    };
    li.onclick = (e) => {
      if (e.target.classList.contains('ellipsis')) return;
      loadChatFromHistory(idx);
    };
    historyUl.appendChild(li);
  });
}

function saveToSidebarHistory(title, chatLog) {
  let history = JSON.parse(localStorage.getItem('chatSidebarHistory') || '[]');
  history.unshift({ title, chat: chatLog });
  localStorage.setItem('chatSidebarHistory', JSON.stringify(history));
  loadHistorySidebar();
  currentHistoryIdx = 0;
  localStorage.setItem('currentHistoryIdx', 0);
}

function updateLastSidebarHistory(chatLog) {
  let history = JSON.parse(localStorage.getItem('chatSidebarHistory') || '[]');
  if (history.length > 0 && currentHistoryIdx !== null) {
    history[currentHistoryIdx].chat = chatLog;
    localStorage.setItem('chatSidebarHistory', JSON.stringify(history));
  }
}

function deleteSidebarHistory(idx) {
  let history = JSON.parse(localStorage.getItem('chatSidebarHistory') || '[]');
  history.splice(idx, 1);
  localStorage.setItem('chatSidebarHistory', JSON.stringify(history));
  loadHistorySidebar();
  if (currentHistoryIdx === idx) newChat();
}

function loadChatFromHistory(idx) {
  const history = JSON.parse(localStorage.getItem('chatSidebarHistory') || '[]');
  if (history[idx]) {
    chatbox.innerHTML = "";
    chatbox.style.display = "flex";
    mainTitle.style.display = "none";
    currentChat = [...history[idx].chat];
    currentHistoryIdx = idx;
    localStorage.setItem('currentHistoryIdx', idx);
    currentChat.forEach(item => {
      appendMessage(item.sender, item.text);
    });
    isFirstSend = false;
  }
}

// --- Chat Logic ---
function appendMessage(sender, message) {
  chatbox.style.display = "flex";
  mainTitle.style.display = "none";
  const msgDiv = document.createElement("div");
  msgDiv.className = "chat-msg " + (sender === "user" ? "user" : "bot");
  const bubble = document.createElement("div");
  bubble.className = "chat-bubble";
  bubble.innerText = message;
  msgDiv.appendChild(bubble);
  chatbox.appendChild(msgDiv);
  chatbox.scrollTop = chatbox.scrollHeight;
  currentChat.push({ sender, text: message });
}

// --- Weather Alert Logic ---
function showWeatherAlert(text) {
  weatherAlert.innerHTML = `
    <div>${text}</div>
    <button class="alert-btn-ok" id="okWeatherAlert">OK</button>
  `;
  weatherAlert.classList.add("active");

  document.getElementById("okWeatherAlert").onclick = () => {
    weatherAlert.classList.remove("active");
    weatherAlert.innerHTML = "";
  };
}

// --- Send Chat ---
async function sendMessage() {
  const q = userInput.value.trim();
  if (!q) return;
  userInput.value = "";

  if (isFirstSend) {
    chatbox.innerHTML = "";
    chatbox.style.display = "flex";
    mainTitle.style.display = "none";
    currentChat = [];
    currentHistoryIdx = null;
  }

  appendMessage("user", q);
  appendMessage("bot", "Mengetik...");

  try {
    const response = await fetch("http://127.0.0.1:5000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: q }),
    });
    const data = await response.json();
    console.log("Data diterima dari Flask:", data);
    console.log("Isi data.response:", data.response);

    const typingBubble = [...chatbox.querySelectorAll('.chat-msg.bot .chat-bubble')]
      .reverse().find(b => b.innerText === "Mengetik...");
    if (typingBubble) typingBubble.parentElement.remove();

    appendMessage("bot", data.response);

    if (isFirstSend) {
      const title = q.split(" ").slice(0, 10).join(" ") + (q.split(" ").length > 10 ? "..." : "");
      saveToSidebarHistory(title, [...currentChat]);
      isFirstSend = false;
    } else {
      updateLastSidebarHistory([...currentChat]);
    }
  } catch {
    const typingBubble = [...chatbox.querySelectorAll('.chat-msg.bot .chat-bubble')]
      .reverse().find(b => b.innerText === "Mengetik...");
    if (typingBubble) typingBubble.parentElement.remove();
    appendMessage("bot", "Gagal koneksi server.");
    if (isFirstSend) {
      const title = q.split(" ").slice(0, 10).join(" ") + (q.split(" ").length > 10 ? "..." : "");
      saveToSidebarHistory(title, [...currentChat]);
      isFirstSend = false;
    } else {
      updateLastSidebarHistory([...currentChat]);
    }
  }
}

// --- New Chat Logic ---
function newChat() {
  if (currentChat.length > 0) updateLastSidebarHistory([...currentChat]);
  chatbox.innerHTML = "";
  chatbox.style.display = "none";
  mainTitle.style.display = "";
  userInput.value = "";
  currentChat = [];
  isFirstSend = true;
  currentHistoryIdx = null;
  localStorage.removeItem('currentHistoryIdx');
}

// --- Weather Logic ---
weatherBtn.onclick = async function() {
  const city = prompt("Masukkan nama kota:");
  if (!city) return;
  showWeatherAlert("Mengetik...");
  try {
    const res = await fetch("http://127.0.0.1:5000/weather", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ city }),
    });
    const data = await res.json();
    showWeatherAlert(data.response);
    // TIDAK masuk history!
  } catch {
    showWeatherAlert("Gagal mengambil data cuaca.");
  }
};

// --- Events ---
sendBtn.onclick = sendMessage;
userInput.addEventListener("keypress", e => {
  if (e.key === "Enter") sendMessage();
});
newChatBtn.onclick = newChat;

// --- INIT ---
document.addEventListener("DOMContentLoaded", () => {
  loadHistorySidebar();
  const idx = localStorage.getItem('currentHistoryIdx');
  if (idx !== null && !isNaN(idx)) {
    loadChatFromHistory(Number(idx));
  } else {
    newChat();
  }
});

function openSidebar() {
  sidebar.classList.add('active');
  sidebarOverlay.classList.add('active');
}
function closeSidebar() {
  sidebar.classList.remove('active');
  sidebarOverlay.classList.remove('active');
}

//mobile sidebar
mobileSidebarBtn.onclick = openSidebar;
sidebarLogoBtn.onclick = closeSidebar;
sidebarOverlay.onclick = closeSidebar;

document.addEventListener('keydown', e => {
  if (e.key === "Escape") closeSidebar();
});