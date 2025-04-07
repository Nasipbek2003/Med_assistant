document.addEventListener('DOMContentLoaded', function() {
    const chatButton = document.getElementById('chatButton');
    const chatWindow = document.getElementById('chatWindow');
    const closeChat = document.getElementById('closeChat');
    const messageInput = document.getElementById('messageInput');
    const sendMessage = document.getElementById('sendMessage');
    const chatMessages = document.getElementById('chatMessages');

    // Открытие/закрытие чата
    function openChat() {
        chatWindow.classList.add('active');
        chatButton.style.display = 'none';
        messageInput.focus();
    }

    function closeChat() {
        chatWindow.classList.remove('active');
        chatButton.style.display = 'flex';
    }

    chatButton.addEventListener('click', openChat);
    closeChat.addEventListener('click', closeChat);

    // Автоматическое изменение высоты текстового поля
    function adjustTextareaHeight() {
        messageInput.style.height = 'auto';
        messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + 'px';
    }

    messageInput.addEventListener('input', adjustTextareaHeight);
    messageInput.addEventListener('focus', adjustTextareaHeight);

    // Отправка сообщения
    function sendMessageToBot() {
        const message = messageInput.value.trim();
        if (!message) return;

        // Добавляем сообщение пользователя
        addMessage(message, 'user');
        messageInput.value = '';
        messageInput.style.height = 'auto';
        
        // Эмулируем "печатание" бота
        const typingIndicator = addTypingIndicator();
        
        // Здесь будет вызов API
        setTimeout(() => {
            removeTypingIndicator(typingIndicator);
            addMessage('Спасибо за ваше сообщение. В данный момент я обрабатываю ваш запрос...', 'system');
        }, 1000);
    }

    // Добавление сообщения в чат
    function addMessage(text, type) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', type);
        messageDiv.textContent = text;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Индикатор печатания
    function addTypingIndicator() {
        const indicator = document.createElement('div');
        indicator.classList.add('message', 'system', 'typing-indicator');
        indicator.innerHTML = '<span>•</span><span>•</span><span>•</span>';
        chatMessages.appendChild(indicator);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return indicator;
    }

    function removeTypingIndicator(indicator) {
        if (indicator && indicator.parentNode) {
            indicator.parentNode.removeChild(indicator);
        }
    }

    // Обработка отправки
    sendMessage.addEventListener('click', sendMessageToBot);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessageToBot();
        }
    });

    // Добавляем стили для индикатора печатания
    const style = document.createElement('style');
    style.textContent = `
        .typing-indicator {
            display: flex;
            align-items: center;
            gap: 4px;
            padding: 12px !important;
        }
        .typing-indicator span {
            width: 6px;
            height: 6px;
            background: #666;
            border-radius: 50%;
            animation: typing 1s infinite;
            display: inline-block;
        }
        .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
        .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes typing {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-4px); }
        }
    `;
    document.head.appendChild(style);

    // Подготовка к интеграции с API
    async function callChatAPI(message) {
        try {
            const response = await fetch('/api/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ message: message })
            });
            return await response.json();
        } catch (error) {
            console.error('Error:', error);
            return { error: 'Произошла ошибка при обработке запроса' };
        }
    }

    // Получение CSRF токена
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Экспортируем функцию openChat для использования из других скриптов
    window.openChat = openChat;
}); 