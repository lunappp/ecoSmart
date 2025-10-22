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

  // Agregar mensajes con mejor formato
  function addMessage(text, sender) {
    const msg = document.createElement("div");
    msg.className = `chatbot-message ${sender}`;
    msg.innerHTML = `
      <div class="message-avatar">${sender === "bot" ? '<i class="fas fa-brain"></i>' : '<i class="fas fa-user"></i>'}</div>
      <div class="message-content"><div style="white-space: pre-line;">${text}</div></div>
    `;
    messages?.appendChild(msg);
    messages.scrollTop = messages.scrollHeight;
  }

  // Respuestas inteligentes con AI
  function getBotResponse(msg) {
    const text = msg.toLowerCase();

    // Saludar
    if (text.includes("hola") || text.includes("buenos") || text.includes("buenas")) {
      return "👋 ¡Hola! Soy EcoSmart AI, tu asistente financiero inteligente. ¿En qué puedo ayudarte hoy?";
    }

    // Preguntas sobre planes
    if (text.includes("plan") || text.includes("planes")) {
      return "📊 Los planes financieros te permiten organizar tus ingresos, gastos y objetivos.\n\nPuedes:\n• Crear un nuevo plan\n• Gestionar planes existentes\n• Ver estadísticas detalladas\n\n¿Quieres que te ayude con algún plan específico?";
    }

    // Preguntas sobre gastos
    if (text.includes("gasto") || text.includes("gastar") || text.includes("gasto")) {
      return "💸 Gestionar gastos es clave para el control financiero.\n\nRecomendaciones:\n• Registra todos tus gastos diarios\n• Categoriza por tipo (comida, transporte, etc.)\n• Revisa tus patrones de gasto semanalmente\n\n¿Necesitas ayuda con algún gasto específico?";
    }

    // Preguntas sobre ingresos
    if (text.includes("ingreso") || text.includes("ganar") || text.includes("dinero")) {
      return "💰 Los ingresos son la base de tu estabilidad financiera.\n\nConsejos:\n• Registra todos tus ingresos\n• Diversifica tus fuentes de ingreso\n• Ahorra al menos el 20% de tus ingresos\n\n¿Quieres analizar tus ingresos actuales?";
    }

    // Preguntas sobre objetivos
    if (text.includes("objetivo") || text.includes("meta") || text.includes("ahorro")) {
      return "🎯 Los objetivos financieros te mantienen motivado.\n\nPara lograrlos:\n• Define metas realistas y medibles\n• Establece plazos específicos\n• Revisa tu progreso regularmente\n• Ajusta según sea necesario\n\n¿Tienes algún objetivo en mente?";
    }

    // Preguntas sobre estadísticas
    if (text.includes("estadística") || text.includes("gráfico") || text.includes("análisis")) {
      return "📈 Las estadísticas te dan una visión clara de tus finanzas.\n\nPuedes ver:\n• Balance general de tus planes\n• Tendencias de ingresos vs gastos\n• Progreso de objetivos\n• Comparativas mensuales\n\n¿Sobre qué aspecto quieres más información?";
    }

    // Preguntas sobre ayuda
    if (text.includes("ayuda") || text.includes("cómo") || text.includes("que puedo")) {
      return "🤖 ¡Claro! Puedo ayudarte con:\n\n• 💡 Consejos financieros personalizados\n• 📊 Análisis de tus planes\n• 🎯 Estrategias de ahorro\n• 📈 Interpretación de estadísticas\n• 💰 Optimización de ingresos y gastos\n\n¿Qué tema te interesa más?";
    }

    // Preguntas sobre consejos
    if (text.includes("consejo") || text.includes("recomendación") || text.includes("tip")) {
      return "💡 Aquí van algunos consejos financieros esenciales:\n\n1. 📅 Regla 50/30/20: 50% necesidades, 30% deseos, 20% ahorro\n2. 💳 Paga tus deudas de alto interés primero\n3. 🎯 Establece objetivos SMART (específicos, medibles, alcanzables, relevantes, con tiempo)\n4. 📊 Revisa tus finanzas semanalmente\n5. 💰 Invierte en educación financiera\n\n¿Sobre qué aspecto quieres consejos específicos?";
    }

    // Respuesta por defecto
    return "🤔 Hmm, no estoy seguro de entender completamente tu pregunta. ¿Podrías darme más detalles sobre lo que necesitas? Puedo ayudarte con planes financieros, consejos de ahorro, análisis de gastos, o cualquier otra consulta financiera.";
  }

  send?.addEventListener("click", sendChatMessage);
  input?.addEventListener("keypress", (e) => e.key === "Enter" && sendChatMessage());
}
