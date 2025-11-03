// Глобальные переменные
let currentPassword = '';
let selectedAgent = null;
let messageHistory = [];
let currentResponseFormat = {
  tag: '[DEFAULT]',
  format: ''
};

// DOM элементы
const authScreen = document.getElementById('authScreen');
const chatScreen = document.getElementById('chatScreen');
const passwordInput = document.getElementById('passwordInput');
const loginBtn = document.getElementById('loginBtn');
const authError = document.getElementById('authError');
const agentSelector = document.getElementById('agentSelector');
const settingsBtn = document.getElementById('settingsBtn');
const settingsModal = document.getElementById('settingsModal');
const closeModalBtn = document.getElementById('closeModalBtn');
const cancelModalBtn = document.getElementById('cancelModalBtn');
const applyFormatBtn = document.getElementById('applyFormatBtn');
const formatSelector = document.getElementById('formatSelector');
const formatDescription = document.getElementById('formatDescription');
const modalError = document.getElementById('modalError');
const messageArea = document.getElementById('messageArea');
const messageInput = document.getElementById('messageInput');
const loadingIndicator = document.getElementById('loadingIndicator');
const notification = document.getElementById('notification');

// Утилиты
function showError(element, message) {
  element.textContent = message;
  element.classList.remove('hidden');
}

function hideError(element) {
  element.classList.add('hidden');
  element.textContent = '';
}

function showNotification(message, type = 'success') {
  notification.textContent = message;
  notification.className = `notification notification--${type}`;
  
  setTimeout(() => {
    notification.classList.add('hidden');
  }, type === 'success' ? 3000 : 5000);
}

function formatTime(date) {
  const hours = date.getHours().toString().padStart(2, '0');
  const minutes = date.getMinutes().toString().padStart(2, '0');
  return `${hours}:${minutes}`;
}

function scrollToBottom() {
  messageArea.scrollTop = messageArea.scrollHeight;
}

// API функции
async function verifyPassword(password) {
  const response = await fetch('/api/verify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ password }),
    credentials: 'include'
  });

  if (!response.ok) {
    if (response.status === 400) {
      throw new Error('Пароль не может быть пустым');
    } else if (response.status === 401) {
      throw new Error('Неверный пароль');
    }
    throw new Error('Ошибка авторизации');
  }

  return response.json();
}

async function getAgentsList() {
  const response = await fetch('/api/agents/list', {
    credentials: 'include'
  });

  if (!response.ok) {
    throw new Error('Ошибка загрузки списка агентов');
  }

  return response.json();
}

async function sendQuestion(question, password) {
  const response = await fetch('/api/question', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, password }),
    credentials: 'include'
  });

  if (!response.ok) {
    throw new Error('Ошибка отправки сообщения');
  }

  return response.json();
}

async function setResponseFormat(responseFormat) {
  const response = await fetch('/api/model/set_response_format', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ response_format: responseFormat }),
    credentials: 'include'
  });

  if (!response.ok) {
    throw new Error('Ошибка установки формата ответа');
  }

  return response.json();
}

// Рендеринг сообщений
function renderMessage(message) {
  const messageEl = document.createElement('div');
  const isUser = message.role === 'user';
  messageEl.className = `message message--${isUser ? 'user' : 'agent'}`;

  const avatar = document.createElement('div');
  avatar.className = 'message__avatar';
  avatar.textContent = isUser ? 'В' : 'А';

  const content = document.createElement('div');
  content.className = 'message__content';

  const header = document.createElement('div');
  header.className = 'message__header';

  const name = document.createElement('div');
  name.className = 'message__name';
  name.textContent = isUser ? 'Вы' : 'Агент';

  const time = document.createElement('div');
  time.className = 'message__time';
  time.textContent = message.time || formatTime(new Date());

  header.appendChild(name);
  header.appendChild(time);

  // Добавить метку формата для сообщений агента
  if (!isUser && message.responseFormat && message.responseFormat.tag) {
    const formatBadge = document.createElement('div');
    formatBadge.className = 'message__format-badge';
    formatBadge.textContent = message.responseFormat.tag;
    header.appendChild(formatBadge);
  }

  const text = document.createElement('div');
  text.className = 'message__text';
  text.textContent = message.content;

  content.appendChild(header);
  content.appendChild(text);

  messageEl.appendChild(avatar);
  messageEl.appendChild(content);

  return messageEl;
}

function renderMessages(messages) {
  messageArea.innerHTML = '';
  messages.forEach(message => {
    messageArea.appendChild(renderMessage(message));
  });
  scrollToBottom();
}

// Авторизация
async function handleLogin() {
  const password = passwordInput.value.trim();
  
  if (!password) {
    showError(authError, 'Пароль не может быть пустым');
    return;
  }

  hideError(authError);
  loginBtn.disabled = true;
  loginBtn.textContent = 'Вход...';

  try {
    const data = await verifyPassword(password);
    currentPassword = password;
    messageHistory = data.history || [];
    
    // Переключиться на экран чата
    authScreen.classList.add('hidden');
    chatScreen.classList.remove('hidden');
    
    // Отобразить историю сообщений
    renderMessages(messageHistory);
    
    // Загрузить список агентов
    await loadAgents();
    
  } catch (error) {
    showError(authError, error.message);
  } finally {
    loginBtn.disabled = false;
    loginBtn.textContent = 'Авторизоваться';
  }
}

loginBtn.addEventListener('click', handleLogin);
passwordInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') {
    handleLogin();
  }
});

// Загрузка списка агентов
async function loadAgents() {
  try {
    const data = await getAgentsList();
    
    if (data.success && data.agents) {
      // Очистить текущие опции (кроме первой)
      agentSelector.innerHTML = '<option value="">Выберите агента</option>';
      
      // Добавить агентов
      data.agents.forEach(agent => {
        const option = document.createElement('option');
        option.value = agent.id;
        option.textContent = agent.name;
        option.dataset.agent = JSON.stringify(agent);
        agentSelector.appendChild(option);
      });
    }
  } catch (error) {
    showNotification('Ошибка загрузки списка агентов: ' + error.message, 'error');
  }
}

// Выбор агента
agentSelector.addEventListener('change', async (e) => {
  const selectedOption = e.target.options[e.target.selectedIndex];

  if (selectedOption.dataset.agent) {
    selectedAgent = JSON.parse(selectedOption.dataset.agent);

    try {
      const response = await fetch('/api/model/set_new_agent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_key: selectedAgent.id }),
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Ошибка установки агента');
      }

      showNotification(`Агент "${selectedAgent.name}" выбран`, 'success');
    } catch (error) {
      showNotification('Ошибка: ' + error.message, 'error');
    }
  } else {
    selectedAgent = null;
  }
});


// Модальное окно настроек
settingsBtn.addEventListener('click', () => {
  // Установить текущие значения
  formatSelector.value = currentResponseFormat.tag;
  formatDescription.value = currentResponseFormat.format;
  hideError(modalError);
  settingsModal.classList.remove('hidden');
});

closeModalBtn.addEventListener('click', () => {
  settingsModal.classList.add('hidden');
});

cancelModalBtn.addEventListener('click', () => {
  settingsModal.classList.add('hidden');
});

// Закрытие модального окна при клике на overlay
settingsModal.querySelector('.modal-overlay').addEventListener('click', () => {
  settingsModal.classList.add('hidden');
});

// Применение формата ответа
applyFormatBtn.addEventListener('click', async () => {
  const tag = formatSelector.value;
  const format = formatDescription.value.trim();

  if (!format && tag !== '[DEFAULT]') {
    showError(modalError, 'Введите описание формата');
    return;
  }

  hideError(modalError);
  applyFormatBtn.disabled = true;
  applyFormatBtn.textContent = 'Применение...';

  try {
    const responseFormat = {
      'tag': tag,
      'format': format
    };
    const data = await setResponseFormat(responseFormat);
    
    if (data.success) {
      currentResponseFormat = responseFormat;
      settingsModal.classList.add('hidden');
      showNotification(`Формат ответа установлен: ${tag}`, 'success');
    } else {
      throw new Error(data.message || 'Ошибка установки формата');
    }
  } catch (error) {
    showError(modalError, error.message);
  } finally {
    applyFormatBtn.disabled = false;
    applyFormatBtn.textContent = 'Применить';
  }
});

// Отправка сообщения
async function handleSendMessage() {
  const question = messageInput.value.trim();
  
  if (!question) {
    return;
  }

  messageInput.value = '';
  messageInput.disabled = true;
  loadingIndicator.classList.remove('hidden');

  // Добавить сообщение пользователя в историю
  const userMessage = {
    role: 'user',
    content: question,
    time: formatTime(new Date())
  };
  
  messageHistory.push(userMessage);
  renderMessages(messageHistory);

  try {
    const data = await sendQuestion(question, currentPassword);
    
    if (data.history) {
      messageHistory = data.history;
      renderMessages(messageHistory);
    }
  } catch (error) {
    showNotification('Ошибка отправки сообщения: ' + error.message, 'error');
    // Удалить сообщение пользователя из истории при ошибке
    messageHistory.pop();
    renderMessages(messageHistory);
  } finally {
    messageInput.disabled = false;
    loadingIndicator.classList.add('hidden');
    messageInput.focus();
  }
}

// Обработка нажатия клавиш в поле ввода
messageInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    handleSendMessage();
  }
});

// Автоматическая регулировка высоты textarea
messageInput.addEventListener('input', () => {
  messageInput.style.height = 'auto';
  messageInput.style.height = Math.min(messageInput.scrollHeight, 200) + 'px';
});