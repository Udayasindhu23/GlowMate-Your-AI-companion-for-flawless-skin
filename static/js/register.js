// Toggle password visibility
document.getElementById('togglePassword').addEventListener('click', function() {
    const passwordInput = document.getElementById('password');
    const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
    passwordInput.setAttribute('type', type);
    this.textContent = type === 'password' ? '👁️' : '🙈';
});

document.getElementById('togglePasswordConfirm').addEventListener('click', function() {
    const passwordInput = document.getElementById('confirm_password');
    const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
    passwordInput.setAttribute('type', type);
    this.textContent = type === 'password' ? '👁️' : '🙈';
});

// Form validation
document.getElementById('registerForm').addEventListener('submit', function(e) {
    const username = document.getElementById('username').value.trim();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirm_password').value;
    
    if (!username || !email || !password || !confirmPassword) {
        e.preventDefault();
        showAlert('Please fill in all fields', 'error');
        return false;
    }
    
    if (password.length < 4) {
        e.preventDefault();
        showAlert('Password must be at least 4 characters', 'error');
        return false;
    }
    
    if (password !== confirmPassword) {
        e.preventDefault();
        showAlert('Passwords do not match', 'error');
        return false;
    }
    
    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        e.preventDefault();
        showAlert('Please enter a valid email address', 'error');
        return false;
    }
});

function showAlert(message, type) {
    const existingAlert = document.querySelector('.alert');
    if (existingAlert) {
        existingAlert.remove();
    }
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.textContent = message;
    
    const form = document.getElementById('registerForm');
    form.parentNode.insertBefore(alert, form);
    
    setTimeout(() => {
        alert.remove();
    }, 5000);
}

// Add focus effects
document.querySelectorAll('input').forEach(input => {
    input.addEventListener('focus', function() {
        this.parentElement.classList.add('focused');
    });
    
    input.addEventListener('blur', function() {
        this.parentElement.classList.remove('focused');
    });
});

