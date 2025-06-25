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

  try {
    const res = await fetch("chat_api.php?action=get_sessions");
    if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
    const sessions = await res.json();

    sessions.forEach((session) => {
      const li = document.createElement("li");
      li.className = "history-item";
      li.innerHTML = `
        <span class="history-title">${session.session_name}</span>
        <span class="ellipsis" title="Hapus">…</span>
      `;

      li.querySelector('.ellipsis').onclick = async (e) => {
        e.stopPropagation();
        if (confirm("Hapus chat ini?")) {
          try {
            const deleteRes = await fetch("chat_api.php?action=delete_session", {
              method: "POST",
              body: new URLSearchParams({ session_id: session.id })
            });
            if (!deleteRes.ok) throw new Error(`HTTP error! Status: ${deleteRes.status}`);
            await loadHistorySidebar();
            if (currentHistoryIdx === session.id) newChat();
          } catch (error) {
            console.error("Gagal menghapus sesi:", error);
          }
        }
      };

      li.onclick = () => loadChatFromHistory(session.id);
      historyUl.appendChild(li);
    });
  } catch (error) {
    console.error("Gagal memuat history sidebar:", error);
  }
}

async function saveToSidebarHistory(title, chatLog) {
  try {
    const res = await fetch("chat_api.php?action=new_session", {
      method: "POST",
      body: new URLSearchParams({ session_name: title })
    });
    if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
    const data = await res.json();

    if (!data.success || !data.session_id) {
      throw new Error(data.error || "Gagal membuat sesi baru");
    }

    currentHistoryIdx = data.session_id;
    localStorage.setItem('currentHistoryIdx', currentHistoryIdx); // Simpan ke localStorage
    for (const msg of chatLog) {
      const saveRes = await fetch("chat_api.php?action=save_message", {
        method: "POST",
        body: new URLSearchParams({
          session_id: data.session_id,
          sender: msg.sender,
          message: msg.text
        })
      });
      if (!saveRes.ok) throw new Error(`HTTP error! Status: ${saveRes.status}`);
      const saveData = await saveRes.json();
      if (!saveData.success) {
        throw new Error(saveData.error || "Gagal menyimpan pesan");
      }
    }

    await loadHistorySidebar();
  } catch (error) {
    console.error("Error saat menyimpan ke history:", error);
  }
}

async function updateLastSidebarHistory(chatLog) {
  if (currentHistoryIdx === null) {
    console.warn("currentHistoryIdx null, tidak dapat memperbarui history.");
    return;
  }

  try {
    const clearRes = await fetch("chat_api.php?action=clear_messages", {
      method: "POST",
      body: new URLSearchParams({ session_id: currentHistoryIdx })
    });
    if (!clearRes.ok) throw new Error(`HTTP error! Status: ${clearRes.status}`);
    const clearData = await clearRes.json();
    if (!clearData.success) {
      throw new Error(clearData.error || "Gagal menghapus pesan lama");
    }

    for (const msg of chatLog) {
      const saveRes = await fetch("chat_api.php?action=save_message", {
        method: "POST",
        body: new URLSearchParams({
          session_id: currentHistoryIdx,
          sender: msg.sender,
          message: msg.text
        })
      });
      if (!saveRes.ok) throw new Error(`HTTP error! Status: ${saveRes.status}`);
      const saveData = await saveRes.json();
      if (!saveData.success) {
        throw new Error(saveData.error || "Gagal menyimpan pesan");
      }
    }
  } catch (error) {
    console.error("Error saat memperbarui history:", error);
  }
}

function clearChatbox() {
  chatbox.innerHTML = "";
}

async function loadChatFromHistory(sessionId) {
  try {
    chatbox.innerHTML = "";
    chatbox.style.display = "flex";
    mainTitle.style.display = "none";

    const res = await fetch(`chat_api.php?action=get_messages&session_id=${sessionId}`);
    if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
    const messages = await res.json();

    currentChat = messages.map(msg => ({ sender: msg.sender, text: msg.message }));
    currentHistoryIdx = sessionId;
    localStorage.setItem('currentHistoryIdx', currentHistoryIdx); // Simpan ke localStorage

    currentChat.forEach(item => {
      appendMessage(item.sender, item.text);
    });

    isFirstSend = false;
  } catch (error) {
    console.error("Gagal memuat chat dari history:", error);
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

  console.log("isFirstSend sebelum pengiriman:", isFirstSend);
  console.log("currentChat sebelum pengiriman:", currentChat);
  console.log("currentHistoryIdx sebelum pengiriman:", currentHistoryIdx);

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
    if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
    const data = await response.json();
    console.log("Data diterima dari Flask:", data);
    console.log("Isi data.response:", data.response);

    const typingBubble = [...chatbox.querySelectorAll('.chat-msg.bot .chat-bubble')]
      .reverse().find(b => b.innerText === "Mengetik...");
    if (typingBubble) typingBubble.parentElement.remove();

    appendMessage("bot", data.response);

    if (isFirstSend) {
      const title = q.split(" ").slice(0, 10).join(" ") + (q.split(" ").length > 10 ? "..." : "");
      await saveToSidebarHistory(title, [...currentChat]);
      isFirstSend = false;
    } else {
      await updateLastSidebarHistory([...currentChat]);
    }
  } catch (error) {
    console.error("Gagal mengirim pesan:", error);
    const typingBubble = [...chatbox.querySelectorAll('.chat-msg.bot .chat-bubble')]
      .reverse().find(b => b.innerText === "Mengetik...");
    if (typingBubble) typingBubble.parentElement.remove();
    appendMessage("bot", "Gagal koneksi server.");
    if (isFirstSend) {
      const title = q.split(" ").slice(0, 10).join(" ") + (q.split(" ").length > 10 ? "..." : "");
      await saveToSidebarHistory(title, [...currentChat]);
      isFirstSend = false;
    } else {
      await updateLastSidebarHistory([...currentChat]);
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
    if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
    const data = await res.json();
    showWeatherAlert(data.response);
    // TIDAK masuk history!
  } catch (error) {
    console.error("Gagal mengambil data cuaca:", error);
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
  const savedSessionId = localStorage.getItem('currentHistoryIdx');
  if (savedSessionId && !isNaN(savedSessionId)) {
    loadChatFromHistory(Number(savedSessionId));
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

// Mobile sidebar
mobileSidebarBtn.onclick = openSidebar;
sidebarLogoBtn.onclick = closeSidebar;
sidebarOverlay.onclick = closeSidebar;

document.addEventListener('keydown', e => {
  if (e.key === "Escape") closeSidebar();
});