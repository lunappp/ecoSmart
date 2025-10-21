// ===== DASHBOARD JAVASCRIPT =====

document.addEventListener('DOMContentLoaded', function() {
  // Toggle sidebar
  const toggleBtn = document.getElementById('toggle-btn');
  const sidebar = document.getElementById('sidebar');
  const main = document.querySelector('main');

  if (toggleBtn && sidebar && main) {
    toggleBtn.addEventListener('click', function() {
      sidebar.classList.toggle('collapsed');
      main.classList.toggle('sidebar-collapsed');
    });
  }

  // Menu item active state
  const menuItems = document.querySelectorAll('.menu-item');
  const currentPath = window.location.pathname;

  menuItems.forEach(item => {
    const href = item.getAttribute('href');
    if (href && (currentPath === href || (href !== '#' && currentPath.startsWith(href)))) {
      item.classList.add('active');
    } else {
      item.classList.remove('active');
    }
  });

  // User dropdown functionality
  initializeUserDropdown();

  // Smooth scroll for anchor links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      e.preventDefault();
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        target.scrollIntoView({
          behavior: 'smooth'
        });
      }
    });
  });

  // Chatbot functionality
  initializeChatbot();
});

// ===== CHATBOT FUNCTIONALITY =====
function initializeChatbot() {
  const chatbotToggle = document.getElementById('chatbot-toggle');
  const chatbotChat = document.getElementById('chatbot-chat');
  const closeChatbot = document.getElementById('close-chatbot');
  const chatInput = document.getElementById('chat-input');
  const sendMessage = document.getElementById('send-message');
  const chatMessages = document.getElementById('chat-messages');
  const chatbotNotification = document.getElementById('chatbot-notification');

  if (!chatbotToggle || !chatbotChat) return;

  // Show notification badge after 3 seconds
  setTimeout(() => {
    if (chatbotNotification) {
      chatbotNotification.style.display = 'flex';
    }
  }, 3000);

  // Toggle chatbot chat
  chatbotToggle.addEventListener('click', () => {
    chatbotChat.classList.toggle('hidden');
    if (chatbotNotification) chatbotNotification.style.display = 'none';
  });

  if (closeChatbot) {
    closeChatbot.addEventListener('click', () => {
      chatbotChat.classList.add('hidden');
    });
  }

  // Close chat when clicking outside
  document.addEventListener('click', (e) => {
    if (!chatbotToggle.contains(e.target) && !chatbotChat.contains(e.target)) {
      chatbotChat.classList.add('hidden');
    }
  });

  // Send message functionality
  function sendChatMessage() {
    if (!chatInput || !chatMessages) return;
    
    const message = chatInput.value.trim();
    if (!message) return;

    // Add user message
    addMessage(message, 'user');
    chatInput.value = '';

    // Simulate bot response
    setTimeout(() => {
      const botResponse = getBotResponse(message);
      addMessage(botResponse, 'bot');
    }, 1000);
  }

  // Add message to chat
  function addMessage(text, sender) {
    if (!chatMessages) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `chatbot-message ${sender}`;

    if (sender === 'bot') {
      messageDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content">
          <p>${text}</p>
        </div>
      `;
    } else {
      messageDiv.innerHTML = `
        <div class="message-avatar">👤</div>
        <div class="message-content">
          <p>${text}</p>
        </div>
      `;
    }

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  // Bot response logic
  function getBotResponse(message) {
    const lowerMessage = message.toLowerCase();

    if (lowerMessage.includes('hola') || lowerMessage.includes('buenos') || lowerMessage.includes('saludos')) {
      return '¡Hola! 👋 Soy tu asistente financiero de EcoSmart. ¿En qué puedo ayudarte hoy?';
    }

    if (lowerMessage.includes('plan') || lowerMessage.includes('planes')) {
      return '📊 Puedes crear y gestionar tus planes financieros desde el dashboard. Cada plan te ayuda a organizar tus ingresos, gastos y objetivos.';
    }

    if (lowerMessage.includes('gasto') || lowerMessage.includes('gastos')) {
      return '💸 Los gastos se registran en cada plan. Puedes categorizarlos y ver estadísticas detalladas de tus finanzas.';
    }

    if (lowerMessage.includes('ingreso') || lowerMessage.includes('ingresos')) {
      return '💰 Registra tus ingresos en los planes correspondientes. Esto te ayudará a tener un balance completo de tus finanzas.';
    }

    if (lowerMessage.includes('objetivo') || lowerMessage.includes('objetivos')) {
      return '🎯 Los objetivos te permiten ahorrar para metas específicas. Puedes aportar dinero periódicamente y hacer seguimiento del progreso.';
    }

    if (lowerMessage.includes('estadística') || lowerMessage.includes('estadísticas')) {
      return '📈 Las estadísticas muestran gráficos y resúmenes de tus finanzas. Incluyen desgloses por categoría y por miembro.';
    }

    if (lowerMessage.includes('ayuda') || lowerMessage.includes('help')) {
      return '🤖 Estoy aquí para ayudarte con:\n• Crear y gestionar planes financieros\n• Registrar ingresos y gastos\n• Configurar objetivos de ahorro\n• Ver estadísticas y reportes\n• Gestionar miembros en planes grupales\n\n¿Sobre qué tema específico necesitas ayuda?';
    }

    return '🤔 No estoy seguro de cómo ayudarte con eso. ¿Puedes ser más específico sobre tu consulta financiera? También puedes explorar las diferentes secciones del dashboard.';
  }

  // Event listeners
  if (sendMessage) {
    sendMessage.addEventListener('click', sendChatMessage);
  }
  
  if (chatInput) {
    chatInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        sendChatMessage();
      }
    });
  }
}

// ===== USER DROPDOWN FUNCTIONALITY =====
function initializeUserDropdown() {
  const userMenuBtn = document.querySelector('.user-menu-btn');
  const userDropdown = document.querySelector('.user-dropdown');

  if (userMenuBtn && userDropdown) {
    userMenuBtn.addEventListener('click', function(e) {
      e.stopPropagation();
      userDropdown.classList.toggle('active');
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
      if (!userMenuBtn.contains(e.target) && !userDropdown.contains(e.target)) {
        userDropdown.classList.remove('active');
      }
    });

    // Close dropdown when pressing Escape
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') {
        userDropdown.classList.remove('active');
      }
    });
  }
}
