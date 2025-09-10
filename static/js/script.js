// KhetSetu Main JavaScript File

// Global Variables
let currentUser = null;
let animationSpeed = 1;

// DOM Content Loaded Event
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    addPageSpecificFeatures();
    initializeAnimations();
});

// Initialize Application
function initializeApp() {
    console.log('🌾 KhetSetu Application Initialized');
    
    // Check if user is logged in
    currentUser = document.querySelector('body').dataset.user || null;
    
    // Add loading states
    addLoadingStates();
    
    // Initialize tooltips
    initializeTooltips();
    
    // Setup form validations
    setupFormValidations();
}

// Setup Event Listeners
function setupEventListeners() {
    // Form submit handlers
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', handleFormSubmit);
    });
    
    // Button click handlers
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('click', handleButtonClick);
    });
    
    // Navigation handlers
    const navLinks = document.querySelectorAll('.nav-menu a');
    navLinks.forEach(link => {
        link.addEventListener('click', handleNavigation);
    });
    
    // Activity item handlers
    const activityItems = document.querySelectorAll('.activity-item');
    activityItems.forEach(item => {
        item.addEventListener('click', handleActivityClick);
    });
}

// Form Submit Handler
function handleFormSubmit(e) {
    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    
    if (submitBtn) {
        // Add loading state
        submitBtn.innerHTML = '<span class="loading"></span> Processing...';
        submitBtn.disabled = true;
        
        // Add form validation
        if (!validateForm(form)) {
            e.preventDefault();
            resetSubmitButton(submitBtn);
            return false;
        }
        
        // Add success animation after a delay (simulating server response)
        setTimeout(() => {
            addSuccessAnimation(form);
        }, 500);
    }
}

// Form Validation
function validateForm(form) {
    let isValid = true;
    const inputs = form.querySelectorAll('input[required], select[required]');
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            showFieldError(input, 'This field is required');
            isValid = false;
        } else {
            clearFieldError(input);
            
            // Specific validations
            if (input.type === 'email' && !isValidEmail(input.value)) {
                showFieldError(input, 'Please enter a valid email');
                isValid = false;
            }
            
            if (input.type === 'tel' && !isValidPhone(input.value)) {
                showFieldError(input, 'Please enter a valid phone number');
                isValid = false;
            }
            
            if (input.name === 'password' && input.value.length < 6) {
                showFieldError(input, 'Password must be at least 6 characters');
                isValid = false;
            }
        }
    });
    
    return isValid;
}

// Show Field Error
function showFieldError(input, message) {
    clearFieldError(input);
    
    input.classList.add('error');
    const errorDiv = document.createElement('div');
    errorDiv.className = 'field-error';
    errorDiv.textContent = message;
    errorDiv.style.cssText = `
        color: #f44336;
        font-size: 0.85rem;
        margin-top: 0.25rem;
        animation: slideIn 0.3s ease;
    `;
    
    input.parentNode.appendChild(errorDiv);
    
    // Add shake animation
    input.style.animation = 'shake 0.5s ease';
    setTimeout(() => {
        input.style.animation = '';
    }, 500);
}

// Clear Field Error
function clearFieldError(input) {
    input.classList.remove('error');
    const existingError = input.parentNode.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
}

// Validation Helpers
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function isValidPhone(phone) {
    const phoneRegex = /^[\d\s\-\+\(\)]{10,}$/;
    return phoneRegex.test(phone);
}

// Reset Submit Button
function resetSubmitButton(button) {
    const originalText = button.dataset.originalText || 'Submit';
    button.innerHTML = originalText;
    button.disabled = false;
}

// Button Click Handler
function handleButtonClick(e) {
    const button = e.target;
    
    // Add ripple effect
    addRippleEffect(button, e);
    
    // Handle specific button types
    if (button.classList.contains('continue-btn')) {
        handleContinueButton();
    }
}

// Add Ripple Effect
function addRippleEffect(button, event) {
    const ripple = document.createElement('span');
    const rect = button.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = event.clientX - rect.left - size / 2;
    const y = event.clientY - rect.top - size / 2;
    
    ripple.style.cssText = `
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.5);
        transform: scale(0);
        animation: ripple 0.6s linear;
        width: ${size}px;
        height: ${size}px;
        left: ${x}px;
        top: ${y}px;
        pointer-events: none;
    `;
    
    button.style.position = 'relative';
    button.style.overflow = 'hidden';
    button.appendChild(ripple);
    
    setTimeout(() => {
        ripple.remove();
    }, 600);
}

// Handle Continue Button (Welcome Page)
function handleContinueButton() {
    // Add transition effect
    document.body.style.opacity = '0';
    document.body.style.transition = 'opacity 0.5s ease';
    
    setTimeout(() => {
        window.location.href = '/dashboard';
    }, 500);
}

// Navigation Handler
function handleNavigation(e) {
    const link = e.target;
    
    // Add loading state for navigation
    if (!link.classList.contains('active')) {
        link.innerHTML += ' <span class="loading" style="margin-left: 0.5rem;"></span>';
    }
}

// Activity Click Handler
function handleActivityClick(e) {
    const item = e.currentTarget;
    
    // Add completion animation
    item.style.background = 'rgba(76, 175, 80, 0.2)';
    item.style.transform = 'scale(0.98)';
    
    // Add checkmark animation
    const checkmark = document.createElement('span');
    checkmark.innerHTML = '✓';
    checkmark.style.cssText = `
        color: #4CAF50;
        font-weight: bold;
        margin-left: auto;
        animation: bounceIn 0.5s ease;
    `;
    
    if (!item.querySelector('span[style*="margin-left: auto"]')) {
        item.appendChild(checkmark);
    }
    
    // Update points (simulate)
    updatePointsAnimation();
    
    setTimeout(() => {
        item.style.background = 'rgba(76, 175, 80, 0.1)';
        item.style.transform = 'scale(1)';
    }, 200);
}

// Update Points Animation
function updatePointsAnimation() {
    const pointsElement = document.querySelector('.xp-text');
    if (pointsElement) {
        const currentPoints = parseInt(pointsElement.textContent.match(/\d+/)[0]);
        const newPoints = currentPoints + 5;
        
        // Animate points increase
        animateNumber(pointsElement, currentPoints, newPoints, 'XP Points: ');
        
        // Update progress bar
        updateProgressBar();
        
        // Show points gained notification
        showPointsGained(5);
    }
}

// Animate Number
function animateNumber(element, start, end, prefix = '') {
    const duration = 1000;
    const startTime = Date.now();
    
    function update() {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const current = Math.floor(start + (end - start) * progress);
        
        element.textContent = prefix + current;
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    update();
}

// Update Progress Bar
function updateProgressBar() {
    const progressBar = document.querySelector('.progress-bar');
    if (progressBar) {
        const currentWidth = parseInt(progressBar.style.width) || 40;
        const newWidth = Math.min(currentWidth + 2, 100);
        
        progressBar.style.width = newWidth + '%';
        progressBar.style.transition = 'width 0.8s ease';
    }
}

// Show Points Gained Notification
function showPointsGained(points) {
    const notification = document.createElement('div');
    notification.innerHTML = `+${points} XP`;
    notification.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: linear-gradient(135deg, #4CAF50, #66BB6A);
        color: white;
        padding: 1rem 2rem;
        border-radius: 50px;
        font-weight: bold;
        font-size: 1.2rem;
        z-index: 1000;
        animation: pointsGained 2s ease forwards;
        box-shadow: 0 10px 30px rgba(76, 175, 80, 0.3);
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 2000);
}

// Page Specific Features
function addPageSpecificFeatures() {
    const currentPage = document.body.className;
    
    switch(currentPage) {
        case 'login-page':
            setupLoginFeatures();
            break;
        case 'signup-page':
            setupSignupFeatures();
            break;
        case 'welcome-page':
            setupWelcomeFeatures();
            break;
        case 'dashboard-page':
            setupDashboardFeatures();
            break;
    }
}

// Setup Login Features
function setupLoginFeatures() {
    // Add remember me functionality
    const rememberMe = document.querySelector('#remember');
    if (rememberMe) {
        rememberMe.addEventListener('change', function() {
            if (this.checked) {
                localStorage.setItem('khetsetu_remember', 'true');
            } else {
                localStorage.removeItem('khetsetu_remember');
            }
        });
    }
    
    // Check if user should be remembered
    if (localStorage.getItem('khetsetu_remember')) {
        const usernameField = document.querySelector('input[name="user_id"]');
        const savedUsername = localStorage.getItem('khetsetu_username');
        if (usernameField && savedUsername) {
            usernameField.value = savedUsername;
        }
    }
}

// Setup Signup Features
function setupSignupFeatures() {
    // Add password strength indicator
    const passwordField = document.querySelector('input[name="password"]');
    if (passwordField) {
        passwordField.addEventListener('input', showPasswordStrength);
    }
    
    // Add real-time validation
    const inputs = document.querySelectorAll('input[required]');
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value) {
                validateSingleField(this);
            }
        });
    });
}

// Show Password Strength
function showPasswordStrength(e) {
    const password = e.target.value;
    const strength = calculatePasswordStrength(password);
    
    // Remove existing strength indicator
    const existingIndicator = e.target.parentNode.querySelector('.password-strength');
    if (existingIndicator) {
        existingIndicator.remove();
    }
    
    // Add new strength indicator
    const indicator = document.createElement('div');
    indicator.className = 'password-strength';
    indicator.innerHTML = `
        <div style="margin-top: 0.5rem;">
            <div style="display: flex; gap: 0.25rem; margin-bottom: 0.25rem;">
                ${Array(4).fill().map((_, i) => 
                    `<div style="height: 4px; flex: 1; background: ${
                        i < strength.level ? strength.color : '#e0e0e0'
                    }; border-radius: 2px;"></div>`
                ).join('')}
            </div>
            <span style="font-size: 0.8rem; color: ${strength.color};">
                ${strength.text}
            </span>
        </div>
    `;
    
    e.target.parentNode.appendChild(indicator);
}

// Calculate Password Strength
function calculatePasswordStrength(password) {
    let score = 0;
    let feedback = [];
    
    if (password.length >= 8) score += 1;
    if (/[a-z]/.test(password)) score += 1;
    if (/[A-Z]/.test(password)) score += 1;
    if (/\d/.test(password)) score += 1;
    if (/[^A-Za-z\d]/.test(password)) score += 1;
    
    const levels = [
        { level: 0, text: 'Very Weak', color: '#f44336' },
        { level: 1, text: 'Weak', color: '#ff9800' },
        { level: 2, text: 'Fair', color: '#ffc107' },
        { level: 3, text: 'Good', color: '#4caf50' },
        { level: 4, text: 'Strong', color: '#2e7d32' }
    ];
    
    return { level: Math.min(score, 4), ...levels[Math.min(score, 4)] };
}

// Setup Welcome Features
function setupWelcomeFeatures() {
    // Enhanced farmer animations
    const farmer = document.querySelector('.farmer');
    if (farmer) {
        // Add random movement variations
        setInterval(() => {
            const randomDelay = Math.random() * 2;
            farmer.style.animationDelay = randomDelay + 's';
        }, 5000);
        
        // Add click interaction
        farmer.addEventListener('click', function() {
            this.style.animation = 'none';
            setTimeout(() => {
                this.style.animation = 'bounce 1s ease-in-out';
            }, 100);
        });
    }
    
    // Auto redirect with countdown
    let countdown = 10;
    const countdownElement = document.createElement('div');
    countdownElement.style.cssText = `
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        background: rgba(76, 175, 80, 0.9);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
    `;
    document.body.appendChild(countdownElement);
    
    const countdownTimer = setInterval(() => {
        countdown--;
        countdownElement.textContent = `Auto-redirect in ${countdown}s`;
        
        if (countdown <= 0) {
            clearInterval(countdownTimer);
            handleContinueButton();
        }
    }, 1000);
    
    // Clear countdown on user interaction
    document.addEventListener('click', () => {
        clearInterval(countdownTimer);
        countdownElement.remove();
    });
}

// Setup Dashboard Features
function setupDashboardFeatures() {
    // Initialize dashboard animations
    initializeDashboardAnimations();
    
    // Setup activity interactions
    setupActivityInteractions();
    
    // Initialize progress tracking
    initializeProgressTracking();
    
    // Setup navigation effects
    setupNavigationEffects();
}

// Initialize Dashboard Animations
function initializeDashboardAnimations() {
    // Stagger card animations
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        
        setTimeout(() => {
            card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 200);
    });
}

// Setup Activity Interactions
function setupActivityInteractions() {
    const activities = document.querySelectorAll('.activity-item');
    activities.forEach(activity => {
        activity.addEventListener('mouseenter', function() {
            this.style.transform = 'translateX(10px) scale(1.02)';
        });
        
        activity.addEventListener('mouseleave', function() {
            this.style.transform = 'translateX(0) scale(1)';
        });
    });
}

// Initialize Progress Tracking
function initializeProgressTracking() {
    // Simulate real-time progress updates
    setInterval(() => {
        const progressBar = document.querySelector('.progress-bar');
        const currentWidth = parseInt(progressBar.style.width) || 40;
        
        // Randomly update progress (simulate user activity)
        if (Math.random() > 0.95 && currentWidth < 100) {
            updateProgressBar();
        }
    }, 10000);
}

// Setup Navigation Effects
function setupNavigationEffects() {
    const navLinks = document.querySelectorAll('.nav-menu a');
    navLinks.forEach(link => {
        link.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
        });
        
        link.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

// Initialize Animations
function initializeAnimations() {
    // Add CSS animations dynamically
    const style = document.createElement('style');
    style.textContent = `
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-5px); }
            75% { transform: translateX(5px); }
        }
        
        @keyframes ripple {
            to { transform: scale(4); opacity: 0; }
        }
        
        @keyframes bounceIn {
            0% { transform: scale(0); opacity: 0; }
            50% { transform: scale(1.2); opacity: 1; }
            100% { transform: scale(1); opacity: 1; }
        }
        
        @keyframes pointsGained {
            0% { transform: translate(-50%, -50%) scale(0); opacity: 0; }
            20% { transform: translate(-50%, -50%) scale(1.2); opacity: 1; }
            80% { transform: translate(-50%, -50%) scale(1); opacity: 1; }
            100% { transform: translate(-50%, -70%) scale(0.8); opacity: 0; }
        }
        
        .field-error {
            animation: slideIn 0.3s ease !important;
        }
        
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
    `;
    document.head.appendChild(style);
}

// Add Loading States
function addLoadingStates() {
    // Store original button texts
    const buttons = document.querySelectorAll('button[type="submit"]');
    buttons.forEach(button => {
        button.dataset.originalText = button.textContent;
    });
}

// Initialize Tooltips
function initializeTooltips() {
    const elements = document.querySelectorAll('[data-tooltip]');
    elements.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

// Show Tooltip
function showTooltip(e) {
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = e.target.dataset.tooltip;
    tooltip.style.cssText = `
        position: absolute;
        background: #333;
        color: white;
        padding: 0.5rem;
        border-radius: 4px;
        font-size: 0.8rem;
        z-index: 1000;
        pointer-events: none;
        opacity: 0;
        transition: opacity 0.3s ease;
    `;
    
    document.body.appendChild(tooltip);
    
    const rect = e.target.getBoundingClientRect();
    tooltip.style.left = rect.left + 'px';
    tooltip.style.top = (rect.bottom + 5) + 'px';
    
    setTimeout(() => {
        tooltip.style.opacity = '1';
    }, 100);
}

// Hide Tooltip
function hideTooltip() {
    const tooltip = document.querySelector('.tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

// Success Animation
function addSuccessAnimation(form) {
    const successDiv = document.createElement('div');
    successDiv.innerHTML = '✓ Success!';
    successDiv.style.cssText = `
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: #4CAF50;
        color: white;
        padding: 1rem;
        border-radius: 50px;
        font-weight: bold;
        animation: bounceIn 0.5s ease;
    `;
    
    form.style.position = 'relative';
    form.appendChild(successDiv);
    
    setTimeout(() => {
        successDiv.remove();
    }, 2000);
}

// Validate Single Field
function validateSingleField(input) {
    if (input.value.trim()) {
        input.style.borderColor = '#4CAF50';
        input.style.boxShadow = '0 0 0 3px rgba(76, 175, 80, 0.1)';
    }
}

// Utility Functions
const Utils = {
    // Debounce function
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    // Throttle function
    throttle: function(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },
    
    // Random number generator
    random: function(min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    },
    
    // Format number with commas
    formatNumber: function(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    }
};

// Export for global use
window.KhetSetu = {
    Utils,
    handleContinueButton,
    updatePointsAnimation,
    showPointsGained
};

// Console welcome message
console.log(`
🌾 KhetSetu JavaScript Loaded Successfully!
Version: 1.0.0
Features: Enhanced animations, form validation, interactive elements
`);