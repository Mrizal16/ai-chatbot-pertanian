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
async function loadHistorySidebar() {
  historyUl.innerHTML = "";

  // Ambil list sesi dari database lewat API
  const res = await fetch("chat_api.php?action=get_sessions");
  const sessions = await res.json();

  sessions.forEach((session) => {
    const li = document.createElement("li");
    li.className = "history-item";
    li.innerHTML = `
      <span class="history-title">${session.session_name}</span>
      <span class="ellipsis" title="Hapus">&#8230;</span>
    `;

    li.querySelector('.ellipsis').onclick = async (e) => {
      e.stopPropagation();
      if (confirm("Hapus chat ini?")) {
        await fetch("chat_api.php?action=delete_session", {
          method: "POST",
          body: new URLSearchParams({ session_id: session.id })
        });
        loadHistorySidebar();
        if (currentHistoryIdx === session.id) newChat();
      }
    };

    li.onclick = () => loadChatFromHistory(session.id);

    historyUl.appendChild(li);
  });
}


async function saveToSidebarHistory(title, chatLog) {
  // Buat session baru di database
  const res = await fetch("chat_api.php?action=new_session", {
    method: "POST",
    body: new URLSearchParams({ session_name: title })
  });
  const data = await res.json();

  if (data.session_id) {
    currentHistoryIdx = data.session_id;

    // Simpan chat ke DB per pesan
    for (const msg of chatLog) {
      await fetch("chat_api.php?action=save_message", {
        method: "POST",
        body: new URLSearchParams({
          session_id: data.session_id,
          sender: msg.sender,
          message: msg.text
        })
      });
    }

    loadHistorySidebar();
  }
}


async function updateLastSidebarHistory(chatLog) {
  if (currentHistoryIdx === null) return;
  
  // Hapus dulu chat lama di session ini
  await fetch("chat_api.php?action=clear_messages", {
    method: "POST",
    body: new URLSearchParams({ session_id: currentHistoryIdx })
  });

  // Simpan ulang semua chat
  for (const msg of chatLog) {
    await fetch("chat_api.php?action=save_message", {
      method: "POST",
      body: new URLSearchParams({
        session_id: currentHistoryIdx,
        sender: msg.sender,
        message: msg.text
      })
    });
  }
}


function clearChatbox() {
  chatbox.innerHTML = "";
}


async function loadChatFromHistory(sessionId) {
  chatbox.innerHTML = "";
  chatbox.style.display = "flex";
  mainTitle.style.display = "none";

  const res = await fetch(`chat_api.php?action=get_messages&session_id=${sessionId}`);
  const messages = await res.json();

  currentChat = messages.map(msg => ({ sender: msg.sender, text: msg.message }));
  currentHistoryIdx = sessionId;

  currentChat.forEach(item => {
    appendMessage(item.sender, item.text);
  });

  isFirstSend = false;
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
  if (currentChat.length > 0) updateLastSidebarHistory(currentChat);
  clearChatbox();
  chatbox.style.display = "none";
  mainTitle.style.display = "";
  userInput.value = "";
  currentChat = [];
  isFirstSend = true;
  currentHistoryIdx = null;
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