// Глобальные переменные
let currentPassword = '';
let selectedChatId = null;
let messageHistory = [];
let currentResponseFormat = {
  format_type: '[DEFAULT]',
  format: ''
};
let chats = [];
let responseFormats = [];

// DOM элементы
console.log("DOM элементы");
const authScreen = document.getElementById('authScreen');
const chatScreen = document.getElementById('chatScreen');
const passwordInput = document.getElementById('passwordInput');
const loginBtn = document.getElementById('loginBtn');
const authError = document.getElementById('authError');
const chatSelector = document.getElementById('chatSelector');
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

document.documentElement.setAttribute('data-color-scheme', 'dark');

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
  if (parts.length === 2) {
    const cookieValue = parts.pop().split(';').shift();
    console.log(`🍪 Куки ${name}=${cookieValue}`);
    return cookieValue;
  }
  console.log(`❌ Куки ${name} не найдена`);
  return null;
}

// ✅ Проверка авторизации через backend
async function checkAuthorization() {
  console.log("🔐 Проверяем авторизацию через backend...");
  try {
    const response = await fetch('/v1/check-auth', {
      credentials: 'include'
    });

    const isAuthorized = response.ok;
    console.log(`📊 Результат: ${isAuthorized ? '✅ Авторизован' : '❌ Нет (HTTP ' + response.status + ')'}`);
    return isAuthorized;
  } catch (error) {
    console.error('❌ Ошибка проверки:', error);
    return false;
  }
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

async function getChats() {
  const response = await fetch('/v1/chats', {
    credentials: 'include'
  });

  if (!response.ok) {
    throw new Error('Ошибка загрузки списка чатов');
  }

  return response.json();
}

async function setSelectedChat(chatId) {
  const response = await fetch('/v1/set_chat', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id: chatId }),
    credentials: 'include'
  });

  if (!response.ok) {
    throw new Error('Ошибка выбора чата');
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

async function getMessageHistory(chatId) {
  const response = await fetch(`/v1/history_message?id=${chatId}`, {
    credentials: 'include'
  });

  if (!response.ok) {
    throw new Error('Ошибка загрузки истории сообщений');
  }

  return response.json();
}

async function deleteMessageHistory(chatId) {
  const response = await fetch(`/v1/history_message?id=${chatId}`, {
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
  content.appendChild(header)
  // --- Метаданные агента ---
  if (!isUser) {
    const metadata = document.createElement('div');
    metadata.className = 'message__metadata'
    // Форматирование данных
    const promptTokens = typeof message.prompt_tokens === 'number' ? message.prompt_tokens : '-';
    const completionTokens = typeof message.completion_tokens === 'number' ? message.completion_tokens : '-';
    const requestTime = typeof message.request_time === 'number'
      ? (message.request_time / 1000).toFixed(3)
      : '-';
    const price = typeof message.price === 'number'
      ? message.price.toFixed(7)
      : '-';
    let metaBlock = '';
    if (message.meta && String(message.meta).trim() !== '') {
      metaBlock = `\n${message.meta}`;
    }
    metadata.textContent =
      `📊 prompt: ${promptTokens} | completion: ${completionTokens} | time: ${requestTime}s | price: ${price}${metaBlock}`;
    content.appendChild(metadata);
  }
  // --- Конец блока метаданных агента ---

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


async function isAuthorized() {
  try {
    const response = await fetch('/v1/check-auth', {
      credentials: 'include'
    });
    return response.ok;
  } catch {
    return false;
  }
}

// Инициализация при загрузке страницы
async function initializeApp() {
  try {
    const isAuthorized = await checkAuthorization();

    console.log(`🔍 Авторизация: ${isAuthorized ? '✅' : '❌'}`);

    if (!isAuthorized) {
      console.log("❌ Не авторизован - форма логина");
      chatScreen.classList.add('hidden');
      authScreen.classList.remove('hidden');
      return;
    }

    console.log("✅ Авторизован - показываем чат");

    chatScreen.classList.remove('hidden');
    authScreen.classList.add('hidden');

    // ============================================
    // Загрузка списка чатов
    // ============================================
    console.log("📦 Загружаем список чатов...");
    const chatsResponse = await getChats();
    chats = chatsResponse.chats;

    // Заполнение селектора чатов
    chatSelector.innerHTML = '<option value="">Выберите чат</option>';
    chats.forEach(chat => {
      const option = document.createElement('option');
      option.value = chat.id;
      option.textContent = chat.name;
      chatSelector.appendChild(option);
    });

    // ============================================
    // Загрузка форматов ответов
    // ============================================
    console.log("📦 Загружаем форматы ответов...");
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

    const savedChatId = localStorage.getItem('selectedChatId');
    if (savedChatId) {
      console.log(`✅ Восстановлен выбранный чат: ${savedChatId}`);
      chatSelector.value = savedChatId;
      selectedChatId = savedChatId;
    }

    const savedFormatType = localStorage.getItem('formatType');
    const savedFormat = localStorage.getItem('format');

    if (savedFormatType) {
      console.log(`✅ Восстановлен тип формата: ${savedFormatType}`);
      formatSelector.value = savedFormatType;
      currentResponseFormat.format_type = savedFormatType;
    }

    if (savedFormat) {
      console.log(`✅ Восстановлен формат: ${savedFormat}`);
      formatDescription.value = savedFormat;
      currentResponseFormat.format = savedFormat;
    }

    // ============================================
    // Загрузка истории сообщений
    // ============================================
    console.log("📜 Загружаем историю сообщений...");
    if (selectedChatId) {
      const historyResponse = await getMessageHistory(selectedChatId);
      if (historyResponse.messages) {
        messageHistory = historyResponse.messages;
        console.log(`✅ Загружено ${messageHistory.length} сообщений`);
        renderMessages(messageHistory);
      } else {
        console.log("ℹ️ История сообщений пуста");
      }
    }

    console.log("✅ Инициализация завершена успешно!");

  } catch (error) {
    console.error('❌ Ошибка инициализации приложения:', error);
    showNotification('Ошибка инициализации: ' + error.message, 'error');
  }
}


// Авторизация
async function handleLogin() {
  const password = passwordInput.value.trim();
  if (!password) {
    showError(authError, "Введите пароль");
    return;
  }

  hideError(authError);
  loginBtn.disabled = true;
  loginBtn.textContent = "Логирование...";

  try {
    console.log("🔐 Отправляем пароль на backend...");
    const loginResponse = await login(password);
    console.log("✅ Backend подтвердил логин:", loginResponse);

    console.log("⏳ Ожидаем установки кук...");
    await new Promise(resolve => setTimeout(resolve, 100));

    // ✅ ГЛАВНОЕ ИЗМЕНЕНИЕ
    const isAuthorized = await checkAuthorization();

    if (!isAuthorized) {
      throw new Error("❌ Авторизация не прошла. Проверьте CORS и samesite флаги.");
    }

    console.log("✅ Авторизация успешна!");
    currentPassword = password;

    authScreen.classList.add("hidden");
    chatScreen.classList.remove("hidden");

    console.log("📝 Инициализируем приложение...");
    await initializeApp();

    console.log("✅ Логин завершен!");
  } catch (error) {
    console.error("❌ Ошибка логина:", error);
    showError(authError, "Ошибка: " + error.message);
    authScreen.classList.remove("hidden");
    chatScreen.classList.add("hidden");
  } finally {
    loginBtn.disabled = false;
    loginBtn.textContent = "Войти";
  }
}

loginBtn.addEventListener('click', handleLogin);
passwordInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') {
    handleLogin();
  }
});

// Выбор чата
chatSelector.addEventListener('change', async (e) => {
  const chatId = e.target.value;

  if (!chatId) {
    selectedChatId = null;
    localStorage.removeItem('selectedChatId');
    return;
  }

  try {
    await setSelectedChat(chatId);
    localStorage.setItem('selectedChatId', chatId);
    selectedChatId = chatId;

    // Загрузить сообщения нового чата
    const historyResponse = await getMessageHistory(chatId);
    if (historyResponse.messages) {
      messageHistory = historyResponse.messages;
      renderMessages(messageHistory);
    }
    showNotification(`Чат "${chatId}" выбран`, 'success');
  } catch (error) {
    showNotification('Ошибка: ' + error.message, 'error');
    // Восстановить предыдущее значение
    e.target.value = selectedChatId || '';
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

    // ✅ Сохраняем в localStorage
    localStorage.setItem('formatType', formatType);
    localStorage.setItem('format', format);

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
  if (!confirm('Вы уверены, что хотите очистить текущую историю чата?')) {
    return;
  }

  try {
    await deleteMessageHistory(selectedChatId);
    messageHistory = [];
    renderMessages(messageHistory);
    showNotification('История текущего чата очищена', 'success');
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
    session_id: getCookie('KEY_SESSION_ID') || '',
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
      console.log(`✅ Загружено ${response}`);
      if (response.messages.length > 1) {
        messageArea.innerHTML = '';
        response.messages.forEach(it => messageArea.appendChild(renderMessage(it)));
        showNotification('Обновление всего списка');
      } else {
        messageArea.appendChild(renderMessage(response.messages[0]));
      }
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

document.addEventListener('DOMContentLoaded', () => {
  console.log("✅ Start!");
  initializeApp()
  console.log("✅ End!");
})
