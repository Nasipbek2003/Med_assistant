    // Переключение между формами
    const toggleBtn = document.querySelector('.toggle-btn');
    const formContainers = document.querySelectorAll('.form-container');
    const toggleText = document.querySelector('.toggle-forms span');

    let isLoginForm = true;

    toggleBtn.addEventListener('click', () => {
        formContainers.forEach(container => {
            container.style.display = container.style.display === 'none' ? 'block' : 'none';
        });

        isLoginForm = !isLoginForm;
        toggleBtn.textContent = isLoginForm ? 'Зарегистрироваться' : 'Войти';
        toggleText.textContent = isLoginForm ? 'Нет аккаунта?' : 'Уже есть аккаунт?';
    });

    // Простая валидация форм
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');

    loginForm.addEventListener('submit', (e) => {
        e.preventDefault();
        // Здесь будет логика авторизации
        console.log('Попытка входа');
    });

    registerForm.addEventListener('submit', (e) => {
        e.preventDefault();
        // Здесь будет логика регистрации
        console.log('Попытка регистрации');
    });