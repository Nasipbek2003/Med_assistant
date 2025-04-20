document.addEventListener('DOMContentLoaded', function() {
    // Мобильное меню
    const mobileMenuButton = document.querySelector('.mobile-menu-btn');
    const mobileMenu = document.getElementById('mobile-menu');

    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', function() {
            mobileMenu.classList.toggle('hidden');
        });
    }

    // Чат функционал
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');
    const typingIndicator = document.querySelector('.typing-indicator');

    if (chatForm) {
        chatForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const message = userInput.value.trim();
            if (!message) return;

            // Добавляем сообщение пользователя
            addMessage(message, 'user');
            userInput.value = '';

            // Показываем индикатор набора
            typingIndicator.classList.remove('hidden');

            try {
                const response = await fetch('/chat/send_message/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({ message: message })
                });

                if (!response.ok) throw new Error('Network response was not ok');
                
                const data = await response.json();
                
                // Скрываем индикатор набора
                typingIndicator.classList.add('hidden');
                
                // Добавляем ответ ассистента
                addMessage(data.response, 'assistant');
            } catch (error) {
                console.error('Error:', error);
                typingIndicator.classList.add('hidden');
                addMessage('Извините, произошла ошибка. Пожалуйста, попробуйте еще раз.', 'assistant');
            }
        });
    }

    // Функция для добавления сообщения
    function addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = `<i class="fas ${sender === 'user' ? 'fa-user' : 'fa-robot'}"></i>`;
        
        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        
        const content = document.createElement('div');
        content.className = 'message-content';
        
        const messageText = document.createElement('div');
        messageText.className = 'message-text';
        messageText.innerHTML = text;
        
        const time = document.createElement('div');
        time.className = 'message-time';
        time.textContent = new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
        
        content.appendChild(messageText);
        bubble.appendChild(content);
        bubble.appendChild(time);
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(bubble);
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
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
}); 