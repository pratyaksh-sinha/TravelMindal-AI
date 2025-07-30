/**
 * TravelMindal AI - Main JavaScript
 * Common functionality for the TravelMindal AI application
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize any Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize any Bootstrap popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Check for authentication token
    const token = localStorage.getItem('access_token');
    updateAuthUI(token);

    // Handle login form submission if on login page
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    // Handle register form submission if on register page
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }

    // Handle logout button clicks
    const logoutButtons = document.querySelectorAll('.logout-btn');
    logoutButtons.forEach(button => {
        button.addEventListener('click', handleLogout);
    });
});

/**
 * Update UI elements based on authentication status
 * @param {string} token - Authentication token
 */
function updateAuthUI(token) {
    const isLoggedIn = !!token;
    const authNav = document.getElementById('auth-nav');
    const userNav = document.getElementById('user-nav');
    
    // If these elements exist, update their visibility
    if (authNav && userNav) {
        if (isLoggedIn) {
            authNav.style.display = 'none';
            userNav.style.display = 'block';
            
            // Fetch and display user info
            fetchUserInfo(token);
        } else {
            authNav.style.display = 'block';
            userNav.style.display = 'none';
        }
    }
}

/**
 * Fetch user information using the token
 * @param {string} token - Authentication token
 */
function fetchUserInfo(token) {
    fetch('/auth/profile', {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (!response.ok) {
            if (response.status === 401) {
                // Token expired or invalid
                localStorage.removeItem('access_token');
                updateAuthUI(null);
                return;
            }
            throw new Error('Failed to fetch user info');
        }
        return response.json();
    })
    .then(data => {
        if (data && data.username) {
            // Update user display name in the navbar
            const userDisplayName = document.getElementById('user-display-name');
            if (userDisplayName) {
                userDisplayName.textContent = data.full_name || data.username;
            }
        }
    })
    .catch(error => {
        console.error('Error fetching user info:', error);
    });
}

/**
 * Handle login form submission
 * @param {Event} event - Form submission event
 */
function handleLogin(event) {
    event.preventDefault();
    
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    
    // Validate form
    if (!email || !password) {
        showAlert('Please fill in all required fields', 'danger');
        return;
    }
    
    // Submit login request
    fetch('/auth/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showAlert(data.error, 'danger');
            return;
        }
        
        // Store token and redirect
        localStorage.setItem('access_token', data.access_token);
        window.location.href = '/';
    })
    .catch(error => {
        console.error('Login error:', error);
        showAlert('An error occurred during login. Please try again.', 'danger');
    });
}

/**
 * Handle register form submission
 * @param {Event} event - Form submission event
 */
function handleRegister(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirm-password').value;
    
    // Validate form
    if (!username || !email || !password || !confirmPassword) {
        showAlert('Please fill in all required fields', 'danger');
        return;
    }
    
    if (password !== confirmPassword) {
        showAlert('Passwords do not match', 'danger');
        return;
    }
    
    // Submit registration request
    fetch('/auth/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, email, password })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showAlert(data.error, 'danger');
            return;
        }
        
        // Store token and redirect
        localStorage.setItem('access_token', data.access_token);
        window.location.href = '/';
    })
    .catch(error => {
        console.error('Registration error:', error);
        showAlert('An error occurred during registration. Please try again.', 'danger');
    });
}

/**
 * Handle user logout
 */
function handleLogout() {
    // Remove token
    localStorage.removeItem('access_token');
    
    // Make logout API request
    fetch('/auth/logout', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .finally(() => {
        // Redirect to home page regardless of API response
        window.location.href = '/';
    });
}

/**
 * Display an alert message
 * @param {string} message - Alert message
 * @param {string} type - Alert type (success, danger, warning, info)
 */
function showAlert(message, type = 'info') {
    const alertsContainer = document.querySelector('.container .alerts');
    
    if (!alertsContainer) {
        // Create alerts container if it doesn't exist
        const mainContainer = document.querySelector('main .container');
        if (mainContainer) {
            const newAlertsContainer = document.createElement('div');
            newAlertsContainer.className = 'alerts mt-3';
            mainContainer.prepend(newAlertsContainer);
            showAlert(message, type); // Call again now that container exists
            return;
        }
        
        // If we can't find a container, use a toast instead
        showToast(message, type);
        return;
    }
    
    // Create alert element
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.role = 'alert';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add to container
    alertsContainer.appendChild(alert);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }
    }, 5000);
}

/**
 * Display a toast notification
 * @param {string} message - Toast message
 * @param {string} type - Toast type (success, danger, warning, info)
 */
function showToast(message, type = 'info') {
    // Check if toast container exists, create if not
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.id = toastId;
    toast.className = 'toast';
    toast.role = 'alert';
    toast.ariaLive = 'assertive';
    toast.ariaAtomic = 'true';
    toast.innerHTML = `
        <div class="toast-header bg-${type} text-white">
            <strong class="me-auto">TravelMindal AI</strong>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;
    
    // Add to container
    toastContainer.appendChild(toast);
    
    // Show toast
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove from DOM after hiding
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

/**
 * Format a date to a readable string
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted date string
 */
function formatDate(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    const options = { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    
    return date.toLocaleDateString('en-IN', options);
}

/**
 * Format currency
 * @param {number} amount - Amount to format
 * @returns {string} Formatted currency string
 */
function formatCurrency(amount) {
    if (amount === undefined || amount === null) return '';
    
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        maximumFractionDigits: 0
    }).format(amount);
}

/**
 * Add loading spinner to a button
 * @param {HTMLElement} button - Button element
 * @param {string} loadingText - Text to show while loading
 */
function addButtonSpinner(button, loadingText = 'Loading...') {
    const originalHTML = button.innerHTML;
    button.disabled = true;
    button.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> ${loadingText}`;
    
    // Return function to restore button
    return function() {
        button.disabled = false;
        button.innerHTML = originalHTML;
    };
}

/**
 * Format text with some basic markdown-like features
 * @param {string} text - Text to format
 * @returns {string} Formatted HTML
 */
function formatTextWithMarkdown(text) {
    if (!text) return '';
    
    // Escape HTML
    text = text.replace(/&/g, '&amp;')
               .replace(/</g, '&lt;')
               .replace(/>/g, '&gt;')
               .replace(/"/g, '&quot;')
               .replace(/'/g, '&#039;');
    
    // Replace newlines with <br> tags
    text = text.replace(/\n/g, '<br>');
    
    // Bold text between ** markers
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Italic text between * markers
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Links [text](url)
    text = text.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank">$1</a>');
    
    return text;
}
