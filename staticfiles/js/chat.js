document.addEventListener('DOMContentLoaded', function() {
    const chatButton = document.getElementById('chatButton');
    const chatWindow = document.getElementById('chatWindow');
    const closeChat = document.getElementById('closeChat');
    const messageInput = document.getElementById('messageInput');
    const sendMessage = document.getElementById('sendMessage');
    const chatMessages = document.getElementById('chatMessages');
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const userMessageTemplate = document.getElementById('user-message-template');
    const assistantMessageTemplate = document.getElementById('assistant-message-template');
    const loadingTemplate = document.getElementById('loading-template');
    const typingIndicator = document.querySelector('.typing-indicator');

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
        userInput.style.height = 'auto';
        userInput.style.height = Math.min(userInput.scrollHeight, 200) + 'px';
    }

    messageInput.addEventListener('input', adjustTextareaHeight);
    messageInput.addEventListener('focus', adjustTextareaHeight);

    // Загрузка истории сообщений из localStorage
    loadChatHistory();

    // Обработка отправки формы
    chatForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const message = userInput.value.trim();
        if (!message) return;

        addMessage(message, true);
        userInput.value = '';
        adjustTextareaHeight();

        showTyping();

        try {
            const response = await fetch('/chat/send_message/', {  // Обновленный URL
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ message: message })
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();
            
            setTimeout(() => {
                hideTyping();
                addMessage(data.response, false, new Date(data.timestamp).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' }));
            }, Math.random() * 1000 + 500);

        } catch (error) {
            console.error('Error:', error);
            hideTyping();
            addMessage('Извините, произошла ошибка. Пожалуйста, попробуйте позже.', false);
        }
    });

    // Обработка нажатия Enter
    userInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });

    function addMessage(text, isUser = false, time = null) {
        const messageTime = time || new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
        const messageHtml = `
            <div class="message ${isUser ? 'user-message' : 'ai-message'}">
                <div class="message-avatar">
                    <i class="fas ${isUser ? 'fa-user' : 'fa-robot'}"></i>
                    ${!isUser ? '<span class="status-dot"></span>' : ''}
                </div>
                <div class="message-bubble">
                    <div class="message-content">
                        <div class="message-text">${text}</div>
                        ${!isUser ? `
                        <div class="message-actions">
                            <button class="action-icon" title="Копировать" onclick="copyMessage(this)">
                                <i class="far fa-copy"></i>
                            </button>
                            <button class="action-icon" title="Реакция">
                                <i class="far fa-smile"></i>
                            </button>
                        </div>
                        ` : ''}
                    </div>
                    <div class="message-time">${messageTime}</div>
                </div>
            </div>
        `;
        
        const messageElement = document.createElement('div');
        messageElement.innerHTML = messageHtml;
        const message = messageElement.firstElementChild;
        message.style.opacity = '0';
        message.style.transform = 'translateY(20px)';
        
        chatMessages.insertBefore(message, typingIndicator);
        
        requestAnimationFrame(() => {
            message.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            message.style.opacity = '1';
            message.style.transform = 'translateY(0)';
        });

        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function saveChatHistory() {
        const messages = [];
        chatMessages.querySelectorAll('.message-text').forEach(element => {
            const isUser = element.closest('.justify-end') !== null;
            messages.push({
                type: isUser ? 'user' : 'assistant',
                text: element.textContent
            });
        });
        localStorage.setItem('chatHistory', JSON.stringify(messages));
    }

    function loadChatHistory() {
        const history = localStorage.getItem('chatHistory');
        if (history) {
            const messages = JSON.parse(history);
            messages.forEach(message => {
                addMessage(message.text, message.type === 'user');
            });
        }
    }

    // Функция для получения CSRF токена
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

    // Показать индикатор печатания
    function showTyping() {
        typingIndicator.classList.remove('hidden');
        typingIndicator.classList.add('visible');
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Скрыть индикатор печатания
    function hideTyping() {
        typingIndicator.classList.remove('visible');
        typingIndicator.classList.add('hidden');
    }

    // Экспортируем функцию openChat для использования из других скриптов
    window.openChat = openChat;

    // Копирование сообщения
    window.copyMessage = function(button) {
        const messageText = button.closest('.message-content').querySelector('.message-text').textContent;
        navigator.clipboard.writeText(messageText).then(() => {
            const icon = button.querySelector('i');
            icon.className = 'fas fa-check';
            setTimeout(() => {
                icon.className = 'far fa-copy';
            }, 2000);
        });
    };
}); 