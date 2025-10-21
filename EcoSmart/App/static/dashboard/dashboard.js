// ===== DASHBOARD FUNCTIONALITY =====

document.addEventListener("DOMContentLoaded", () => {
  initializeSidebar();
  highlightActiveMenu();
  initializeUserDropdown();
  initializeSmoothScroll();
  initializeChatbot();
});

// ===== SIDEBAR TOGGLE =====
function initializeSidebar() {
  const toggleBtn = document.getElementById("toggle-btn");
  const sidebar = document.getElementById("sidebar");
  const main = document.querySelector("main");

  if (toggleBtn && sidebar && main) {
    toggleBtn.addEventListener("click", () => {
      sidebar.classList.toggle("collapsed");
      main.classList.toggle("sidebar-collapsed");
    });
  }
}

// ===== MENU ITEM ACTIVE STATE =====
function highlightActiveMenu() {
  const currentPath = window.location.pathname;
  document.querySelectorAll(".menu-item").forEach((item) => {
    const href = item.getAttribute("href");
    item.classList.toggle(
      "active",
      href && (currentPath === href || currentPath.startsWith(href))
    );
  });
}

// ===== SMOOTH SCROLL =====
function initializeSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener("click", (e) => {
      e.preventDefault();
      const target = document.querySelector(anchor.getAttribute("href"));
      if (target) target.scrollIntoView({ behavior: "smooth" });
    });
  });
}

// ===== USER DROPDOWN =====
function initializeUserDropdown() {
  const userAvatar = document.querySelector(".user-avatar");
  const userMenuBtn = document.querySelector(".user-menu-btn");
  const userDropdown = document.querySelector(".user-dropdown");

  // Support both avatar and button clicks
  const trigger = userAvatar || userMenuBtn;

  if (!trigger || !userDropdown) return;

  trigger.addEventListener("click", (e) => {
    e.stopPropagation();
    userDropdown.classList.toggle("active");
  });

  document.addEventListener("click", (e) => {
    if (!trigger.contains(e.target) && !userDropdown.contains(e.target))
      userDropdown.classList.remove("active");
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") userDropdown.classList.remove("active");
  });
}

// ===== CHATBOT =====
function initializeChatbot() {
  const toggle = document.getElementById("chatbot-toggle");
  const chat = document.getElementById("chatbot-chat");
  const close = document.getElementById("close-chatbot");
  const input = document.getElementById("chat-input");
  const send = document.getElementById("send-message");
  const messages = document.getElementById("chat-messages");
  const notification = document.getElementById("chatbot-notification");

  if (!toggle || !chat) return;

  // Notificación automática
  setTimeout(() => notification && (notification.style.display = "flex"), 3000);

  // Abrir/cerrar chat
  toggle.addEventListener("click", (e) => {
    e.stopPropagation();
    chat.classList.toggle("active");
    if (notification) notification.style.display = "none";
  });

  close?.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
    chat.classList.remove("active");
  });

  document.addEventListener("click", (e) => {
    if (!toggle.contains(e.target) && !chat.contains(e.target))
      chat.classList.remove("active");
  });

  // Enviar mensaje
  function sendChatMessage() {
    const message = input?.value.trim();
    if (!message) return;
    addMessage(message, "user");
    input.value = "";
    setTimeout(() => addMessage(getBotResponse(message), "bot"), 800);
  }

  // Agregar mensajes
  function addMessage(text, sender) {
    const msg = document.createElement("div");
    msg.className = `chatbot-message ${sender}`;
    msg.innerHTML = `
      <div class="message-avatar">${sender === "bot" ? "🤖" : "👤"}</div>
      <div class="message-content"><p>${text}</p></div>
    `;
    messages?.appendChild(msg);
    messages.scrollTop = messages.scrollHeight;
  }

  // Respuestas automáticas
  function getBotResponse(msg) {
    const text = msg.toLowerCase();
    if (text.includes("hola")) return "👋 ¡Hola! Soy tu asistente financiero de EcoSmart.";
    if (text.includes("plan")) return "📊 Puedes crear y gestionar tus planes financieros desde el dashboard.";
    if (text.includes("gasto")) return "💸 Registra tus gastos y analiza tus estadísticas.";
    if (text.includes("ingreso")) return "💰 Añade ingresos a tus planes para ver tu balance.";
    if (text.includes("objetivo")) return "🎯 Define objetivos de ahorro y sigue tu progreso.";
    if (text.includes("estadística")) return "📈 Mira los gráficos financieros en la sección de estadísticas.";
    if (text.includes("ayuda")) return "🤖 Puedo ayudarte con planes, ingresos, gastos y objetivos. ¿Sobre qué tema necesitas ayuda?";
    return "🤔 No entiendo del todo. ¿Podrías reformular tu pregunta?";
  }

  send?.addEventListener("click", sendChatMessage);
  input?.addEventListener("keypress", (e) => e.key === "Enter" && sendChatMessage());
}
