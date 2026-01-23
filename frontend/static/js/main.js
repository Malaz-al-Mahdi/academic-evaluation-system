// Main JavaScript file for common functionality

const API_BASE = '/api';

// Check authentication on page load
(function() {
    // Skip auth check on login page
    if (window.location.pathname === '/login' || window.location.pathname === '/login.html') {
        return;
    }
    
    const token = localStorage.getItem('access_token');
    if (!token) {
        console.log('No token found, redirecting to login');
        window.location.href = '/login';
        return;
    }
    
    console.log('Token found, verifying...');
})();

// Utility functions
async function apiCall(endpoint, options = {}) {
    try {
        const token = localStorage.getItem('access_token');
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };
        
        // Add token to headers
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers,
            ...options
        });
        
        // If unauthorized, redirect to login
        if (response.status === 401) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('user_info');
            if (window.location.pathname !== '/login') {
                window.location.href = '/login';
            }
            throw new Error('Unauthorized');
        }
        
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(error.detail || `HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

// Check if form is valid
function checkFormValidity() {
    const form = document.getElementById('evaluationForm');
    if (!form) {
        console.log('Form not found');
        return false;
    }
    
    // Check all required fields explicitly
    const firstName = document.getElementById('firstName')?.value?.trim() || '';
    const lastName = document.getElementById('lastName')?.value?.trim() || '';
    const matriculationNumber = document.getElementById('matriculationNumber')?.value?.trim() || '';
    const reportCategory = document.getElementById('reportCategory')?.value || '';
    const reportType = document.getElementById('reportType')?.value || '';
    const reportTitle = document.getElementById('reportTitle')?.value?.trim() || '';
    
    let isValid = true;
    const errors = [];
    
    // Validate firstName
    if (!firstName) {
        isValid = false;
        errors.push('First name is required');
    }
    
    // Validate lastName
    if (!lastName) {
        isValid = false;
        errors.push('Last name is required');
    }
    
    // Validate matriculation number
    if (!matriculationNumber) {
        isValid = false;
        errors.push('Matriculation number is required');
    } else if (matriculationNumber.length !== 7) {
        isValid = false;
        errors.push('Matriculation number must be exactly 7 digits');
        const field = document.getElementById('matriculationNumber');
        if (field) {
            field.setCustomValidity('Matriculation number must be exactly 7 digits');
        }
    } else if (!/^\d{7}$/.test(matriculationNumber)) {
        isValid = false;
        errors.push('Matriculation number must contain only digits');
        const field = document.getElementById('matriculationNumber');
        if (field) {
            field.setCustomValidity('Matriculation number must contain only digits');
        }
    } else {
        const field = document.getElementById('matriculationNumber');
        if (field) {
            field.setCustomValidity('');
        }
    }
    
    // Validate report category
    if (!reportCategory) {
        isValid = false;
        errors.push('Report category is required');
    }
    
    // Validate report type
    if (!reportType) {
        isValid = false;
        errors.push('Report type is required');
    }
    
    // Validate report title
    if (!reportTitle) {
        isValid = false;
        errors.push('Report title is required');
    }
    
    if (errors.length > 0) {
        console.log('Form validation errors:', errors);
    }
    
    const continueBtn = document.getElementById('continueBtn');
    if (continueBtn) {
        continueBtn.disabled = !isValid;
        if (isValid) {
            continueBtn.style.opacity = '1';
            continueBtn.style.cursor = 'pointer';
            continueBtn.classList.remove('disabled');
        } else {
            continueBtn.style.opacity = '0.6';
            continueBtn.style.cursor = 'not-allowed';
            continueBtn.classList.add('disabled');
        }
    }
    
    return isValid;
}

// Initialize form validation
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('evaluationForm');
    if (form) {
        // Add event listeners to all inputs and selects
        const inputs = form.querySelectorAll('input, select');
        inputs.forEach(input => {
            input.addEventListener('input', checkFormValidity);
            input.addEventListener('change', checkFormValidity);
            input.addEventListener('blur', checkFormValidity);
        });
        
        // Special handling for matriculation number
        const matriculationInput = document.getElementById('matriculationNumber');
        if (matriculationInput) {
            matriculationInput.addEventListener('input', function(e) {
                this.value = this.value.replace(/\D/g, '');
                if (this.value.length > 7) {
                    this.value = this.value.slice(0, 7);
                }
                checkFormValidity();
            });
            
            matriculationInput.addEventListener('paste', function(e) {
                e.preventDefault();
                const pastedText = (e.clipboardData || window.clipboardData).getData('text');
                const digitsOnly = pastedText.replace(/\D/g, '').slice(0, 7);
                this.value = digitsOnly;
                checkFormValidity();
            });
        }
        
        // Validate when report category changes
        const reportCategory = document.getElementById('reportCategory');
        if (reportCategory) {
            reportCategory.addEventListener('change', () => {
                console.log('Report category changed to:', reportCategory.value);
                checkFormValidity();
            });
        }
        
        // Validate when report type changes
        const reportType = document.getElementById('reportType');
        if (reportType) {
            reportType.addEventListener('change', () => {
                console.log('Report type changed to:', reportType.value);
                checkFormValidity();
            });
        }
        
        // Initial validation
        setTimeout(() => {
            checkFormValidity();
        }, 500);
        
        // Periodic validation
        setInterval(() => {
            checkFormValidity();
        }, 1000);
    }
});

// Show error message
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> <span>${message}</span>`;
    const container = document.querySelector('.container');
    if (container) {
        container.prepend(errorDiv);
        setTimeout(() => {
            errorDiv.style.opacity = '0';
            errorDiv.style.transform = 'translateY(-10px)';
            setTimeout(() => errorDiv.remove(), 300);
        }, 5000);
    }
}

// Show success message
function showSuccess(message) {
    const successDiv = document.createElement('div');
    successDiv.className = 'success-message';
    successDiv.innerHTML = `<i class="fas fa-check-circle"></i> <span>${message}</span>`;
    const container = document.querySelector('.container');
    if (container) {
        container.prepend(successDiv);
        setTimeout(() => {
            successDiv.style.opacity = '0';
            successDiv.style.transform = 'translateY(-10px)';
            setTimeout(() => successDiv.remove(), 300);
        }, 5000);
    }
}

