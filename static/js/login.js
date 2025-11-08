// Toggle password visibility
document.getElementById('togglePassword').addEventListener('click', function() {
    const passwordInput = document.getElementById('password');
    const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
    passwordInput.setAttribute('type', type);
    
    // Change icon
    this.textContent = type === 'password' ? '👁️' : '🙈';
});

// Form validation
document.getElementById('loginForm').addEventListener('submit', function(e) {
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    
    if (!username || !password) {
        e.preventDefault();
        showAlert('Please fill in all fields', 'error');
        return false;
    }
    
    if (password.length < 4) {
        e.preventDefault();
        showAlert('Password must be at least 4 characters', 'error');
        return false;
    }
});

// Show alert message
function showAlert(message, type) {
    // Remove existing alerts
    const existingAlert = document.querySelector('.alert');
    if (existingAlert) {
        existingAlert.remove();
    }
    
    // Create new alert
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.textContent = message;
    
    // Insert before form
    const form = document.getElementById('loginForm');
    form.parentNode.insertBefore(alert, form);
    
    // Remove after 5 seconds
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

// Social login buttons (placeholder)
document.querySelectorAll('.social-btn').forEach(btn => {
    btn.addEventListener('click', function(e) {
        e.preventDefault();
        const provider = this.classList.contains('google') ? 'Google' : 'GitHub';
        showAlert(`${provider} login coming soon!`, 'success');
    });
});

