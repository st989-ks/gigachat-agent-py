// Глобальные переменные
let currentPassword = '';
let selectedAgentSystem = null;
let messageHistory = [];
let currentResponseFormat = {
  format_type: '[DEFAULT]',
  format: ''
};
let agentSystems = [];
let responseFormats = [];

// DOM элементы
const authScreen = document.getElementById('authScreen');
const chatScreen = document.getElementById('chatScreen');
const passwordInput = document.getElementById('passwordInput');
const loginBtn = document.getElementById('loginBtn');
const authError = document.getElementById('authError');
const agentSystemSelector = document.getElementById('agentSystemSelector');
const settingsBtn = document.getElementById('settingsBtn');
const clearChatBtn = document.getElementById('clearChatBtn');
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

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}

async function login(password) {
  const response = await fetch('/v1/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ password }),
    credentials: 'include'
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('Неверный пароль');
    }
    throw new Error('Ошибка авторизации');
  }

  return response.json();
}

async function getAgentSystems() {
  const response = await fetch('/v1/agent_systems', {
    credentials: 'include'
  });

  if (!response.ok) {
    throw new Error('Ошибка загрузки списка систем агентов');
  }

  return response.json();
}

async function setAgentSystem(system) {
  const response = await fetch('/v1/set_agent_system', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ system }),
    credentials: 'include'
  });

  if (!response.ok) {
    throw new Error('Ошибка установки системы агентов');
  }

  return response.json();
}

async function getResponseFormats() {
  const response = await fetch('/v1/response_formats', {
    credentials: 'include'
  });

  if (!response.ok) {
    throw new Error('Ошибка загрузки списка форматов ответов');
  }

  return response.json();
}

async function setResponseFormat(formatType, format) {
  const response = await fetch('/v1/set_response_format', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ format_type: formatType, format }),
    credentials: 'include'
  });

  if (!response.ok) {
    throw new Error('Ошибка установки формата ответа');
  }

  return response.json();
}

async function sendMessage(message) {
  const response = await fetch('/v1/message', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
    credentials: 'include'
  });

  if (!response.ok) {
    throw new Error('Ошибка отправки сообщения');
  }

  return response.json();
}

async function getMessageHistory() {
  const response = await fetch('/v1/history_message', {
    credentials: 'include'
  });

  if (!response.ok) {
    throw new Error('Ошибка загрузки истории сообщений');
  }

  return response.json();
}

async function deleteMessageHistory() {
  const response = await fetch('/v1/history_message', {
    method: 'DELETE',
    credentials: 'include'
  });

  if (!response.ok) {
    throw new Error('Ошибка удаления истории сообщений');
  }

  return response.json();
}

// Рендеринг сообщений
function renderMessage(message) {
  const messageEl = document.createElement('div');
  const isUser = message.message_type === 'USER';
  messageEl.className = `message message--${isUser ? 'user' : 'agent'}`;
  messageEl.style.maxWidth = '90%';

  const avatar = document.createElement('div');
  avatar.className = 'message__avatar';
  avatar.textContent = isUser ? 'В' : 'А';

  const content = document.createElement('div');
  content.className = 'message__content';

  const header = document.createElement('div');
  header.className = 'message__header';

  const name = document.createElement('div');
  name.className = 'message__name';
  name.textContent = message.name || (isUser ? 'Вы' : 'Агент');

  const time = document.createElement('div');
  time.className = 'message__time';
  time.textContent = message.timestamp || formatTime(new Date());

  header.appendChild(name);
  header.appendChild(time);

  const text = document.createElement('div');
  text.className = 'message__text';
  text.textContent = message.message;

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

// Инициализация при загрузке страницы
async function initializeApp() {
  try {
    // Загрузка систем агентов
    const agentSystemsResponse = await getAgentSystems();
    agentSystems = agentSystemsResponse.systems;

    // Заполнение селектора систем агентов
    agentSystemSelector.innerHTML = '<option value="">Выберите систему агентов</option>';
    agentSystems.forEach(system => {
      const option = document.createElement('option');
      option.value = system;
      option.textContent = system;
      agentSystemSelector.appendChild(option);
    });

    // Загрузка форматов ответов
    const responseFormatsResponse = await getResponseFormats();
    responseFormats = responseFormatsResponse.formats;

    // Заполнение селектора форматов ответов
    formatSelector.innerHTML = '';
    responseFormats.forEach(format => {
      const option = document.createElement('option');
      option.value = format;
      option.textContent = format;
      formatSelector.appendChild(option);
    });

    // Восстановление состояния из куки
    const savedAgentSystem = getCookie('KEY_SELECTED_AGENT_SYSTEMS');
    if (savedAgentSystem) {
      agentSystemSelector.value = savedAgentSystem;
      selectedAgentSystem = savedAgentSystem;
    }

    const savedFormatType = getCookie('KEY_SELECTED_FORMAT_TYPE_REQUEST');
    const savedFormat = getCookie('KEY_SELECTED_FORMAT_REQUEST');

    if (savedFormatType) {
      formatSelector.value = savedFormatType;
      currentResponseFormat.format_type = savedFormatType;
    }

    if (savedFormat) {
      formatDescription.value = savedFormat;
      currentResponseFormat.format = savedFormat;
    }

    // Загрузка истории сообщений
    const historyResponse = await getMessageHistory();
    if (historyResponse.messages) {
      messageHistory = historyResponse.messages;
      renderMessages(messageHistory);
    }

  } catch (error) {
    console.error('Ошибка инициализации приложения:', error);
    showNotification('Ошибка инициализации: ' + error.message, 'error');
  }
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
    await login(password);
    currentPassword = password;

    // Переключиться на экран чата
    authScreen.classList.add('hidden');
    chatScreen.classList.remove('hidden');

    // Инициализация приложения
    await initializeApp();

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

// Выбор системы агентов
agentSystemSelector.addEventListener('change', async (e) => {
  const system = e.target.value;

  if (!system) {
    selectedAgentSystem = null;
    return;
  }

  try {
    await setAgentSystem(system);
    selectedAgentSystem = system;
    showNotification(`Система агентов "${system}" выбрана`, 'success');
  } catch (error) {
    showNotification('Ошибка: ' + error.message, 'error');
    // Восстановить предыдущее значение
    e.target.value = selectedAgentSystem || '';
  }
});

// Модальное окно настроек
settingsBtn.addEventListener('click', () => {
  // Установить текущие значения
  formatSelector.value = currentResponseFormat.format_type;
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
  const formatType = formatSelector.value;
  const format = formatDescription.value.trim();

  hideError(modalError);
  applyFormatBtn.disabled = true;
  applyFormatBtn.textContent = 'Применение...';

  try {
    await setResponseFormat(formatType, format);

    currentResponseFormat.format_type = formatType;
    currentResponseFormat.format = format;

    settingsModal.classList.add('hidden');
    showNotification(`Формат ответа установлен: ${formatType}`, 'success');
  } catch (error) {
    showError(modalError, error.message);
  } finally {
    applyFormatBtn.disabled = false;
    applyFormatBtn.textContent = 'Применить';
  }
});

// Очистка чата
clearChatBtn.addEventListener('click', async () => {
  if (!confirm('Вы уверены, что хотите очистить всю историю чата?')) {
    return;
  }

  try {
    await deleteMessageHistory();
    messageHistory = [];
    renderMessages(messageHistory);
    showNotification('История чата очищена', 'success');
  } catch (error) {
    showNotification('Ошибка очистки чата: ' + error.message, 'error');
  }
});

// ==================== ОТПРАВКА СООБЩЕНИЯ ====================
async function handleSendMessage() {
  const messageText = messageInput.value.trim();

  if (!messageText) {
    return;
  }

  // Создаём объект сообщения пользователя
  const userMessage = {
    id: null,
    session_id: getCookie('session_id') || '',
    message_type: 'USER',
    agent_id: null,
    name: 'Вы',
    timestamp: new Date().toLocaleTimeString('ru-RU', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    }),
    message: messageText
  };

  // Добавляем сообщение пользователя в ДОМ сразу
  messageArea.appendChild(renderMessage(userMessage));
  scrollToBottom();

  messageInput.value = '';
  messageInput.disabled = true;
  loadingIndicator.classList.remove('hidden');

  console.log('[Message] Отправка сообщения:', messageText);

  try {
    const response = await sendMessage(messageText);
    console.log('[Message] Ответ получен:', response);

    // Добавляем ответ AI в ДОМ
    if (response) {
      messageArea.appendChild(renderMessage(response));
      scrollToBottom();
    }
  } catch (error) {
    console.error('[Message] Ошибка отправки:', error);

    // При ошибке удаляем последнее "оптимистичное" сообщение пользователя
    const lastMessage = messageArea.lastChild;
    if (lastMessage) {
      lastMessage.remove();
    }

    showNotification('Ошибка отправки сообщения: ' + error.message, 'error');
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