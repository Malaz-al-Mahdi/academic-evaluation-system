// Login functionality
const API_BASE = '/api';

// Log immediately when script loads
console.log('login.js loaded! API_BASE:', API_BASE);

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOMContentLoaded fired in login.js');
    const loginForm = document.getElementById('loginForm');
    const loginBtn = document.getElementById('loginBtn');
    const errorDiv = document.getElementById('loginError');
    const passwordInput = document.getElementById('password');
    const emailInput = document.getElementById('email');
    const togglePasswordBtn = document.getElementById('togglePassword');
    const passwordIcon = document.getElementById('passwordIcon');
    
    // Read URL parameters and pre-fill form (if present)
    const urlParams = new URLSearchParams(window.location.search);
    const urlEmail = urlParams.get('email');
    const urlPassword = urlParams.get('password');
    
    if (urlEmail && emailInput) {
        emailInput.value = decodeURIComponent(urlEmail);
    }
    if (urlPassword && passwordInput) {
        passwordInput.value = decodeURIComponent(urlPassword);
    }
    
    // Clean URL after reading parameters (remove sensitive data from URL)
    if (urlEmail || urlPassword) {
        window.history.replaceState({}, document.title, '/login');
    }
    
    // Toggle password visibility
    if (togglePasswordBtn && passwordInput && passwordIcon) {
        togglePasswordBtn.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                passwordIcon.className = 'fas fa-eye-slash';
                togglePasswordBtn.setAttribute('aria-label', 'Hide password');
                togglePasswordBtn.setAttribute('title', 'Hide password');
            } else {
                passwordInput.type = 'password';
                passwordIcon.className = 'fas fa-eye';
                togglePasswordBtn.setAttribute('aria-label', 'Show password');
                togglePasswordBtn.setAttribute('title', 'Show password');
            }
            return false;
        };
    }
    
    // Check if already logged in
    const token = localStorage.getItem('access_token');
    if (token) {
        // Verify token is still valid
        fetch(`${API_BASE}/auth/me`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (response.ok) {
                window.location.href = '/';
            } else {
                localStorage.removeItem('access_token');
                localStorage.removeItem('user_info');
            }
        })
        .catch(() => {
            localStorage.removeItem('access_token');
            localStorage.removeItem('user_info');
        });
    }
    
    // Login button click handler (instead of form submit)
    if (loginBtn) {
        loginBtn.addEventListener('click', async (e) => {
            // CRITICAL: Prevent default form submission
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();
            
            const email = document.getElementById('email').value.trim();
            const password = document.getElementById('password').value;
            
            if (!email || !password) {
                errorDiv.textContent = 'Please enter both email and password.';
                errorDiv.style.display = 'block';
                return false;
            }
            
            // Disable button
            loginBtn.disabled = true;
            loginBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Logging in...';
            errorDiv.style.display = 'none';
            
            try {
                // Prepare form data for OAuth2
                const formData = new URLSearchParams();
                formData.append('username', email);
                formData.append('password', password);
                
                console.log('=== LOGIN ATTEMPT ===');
                console.log('Email:', email);
                console.log('API Endpoint:', `${API_BASE}/auth/login`);
                
                // Make login request to API endpoint (NOT the HTML page)
                const response = await fetch(`${API_BASE}/auth/login`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: formData.toString()
                });
                
                console.log('Response status:', response.status);
                console.log('Response OK:', response.ok);
                
                // Handle response
                if (!response.ok) {
                    let errorMessage = 'Login failed. ';
                    try {
                        const errorData = await response.json();
                        console.error('Error response:', errorData);
                        if (errorData.detail) {
                            if (Array.isArray(errorData.detail)) {
                                errorMessage += errorData.detail.map(d => d.msg || d).join(', ');
                            } else {
                                errorMessage += errorData.detail;
                            }
                        } else {
                            errorMessage += `HTTP ${response.status}`;
                        }
                    } catch (e) {
                        const text = await response.text().catch(() => '');
                        console.error('Error text:', text);
                        errorMessage += text || `HTTP ${response.status}`;
                    }
                    throw new Error(errorMessage);
                }
                
                // Parse success response
                const data = await response.json();
                console.log('Login response:', data);
                
                if (!data || !data.access_token) {
                    throw new Error('Server did not return an access token.');
                }
                
                console.log('Login successful, storing token...');
                
                // Store token
                localStorage.setItem('access_token', data.access_token);
                console.log('Token stored in localStorage');
                
                // Get user info
                try {
                    const userResponse = await fetch(`${API_BASE}/auth/me`, {
                        headers: {
                            'Authorization': `Bearer ${data.access_token}`,
                            'Content-Type': 'application/json'
                        }
                    });
                    
                    if (userResponse.ok) {
                        const userInfo = await userResponse.json();
                        localStorage.setItem('user_info', JSON.stringify(userInfo));
                        console.log('User info stored:', userInfo.email || userInfo.username);
                    }
                } catch (e) {
                    console.warn('Could not fetch user info:', e);
                    // Continue anyway
                }
                
                console.log('=== LOGIN SUCCESS ===');
                console.log('Redirecting to home page...');
                
                // Redirect to home page
                window.location.href = '/';
                
                return false;
                
            } catch (error) {
                console.error('=== LOGIN ERROR ===');
                console.error('Error:', error);
                errorDiv.textContent = error.message || 'Login failed. Please check your credentials.';
                errorDiv.style.display = 'block';
                loginBtn.disabled = false;
                loginBtn.innerHTML = '<i class="fas fa-sign-in-alt"></i> Login';
                return false;
            }
        });
        
    } else {
        console.error('Login button not found!');
    }
    
    // Also prevent form submission if someone presses Enter
    if (loginForm) {
        loginForm.addEventListener('submit', (e) => {
            e.preventDefault();
            e.stopPropagation();
            // Trigger login button click instead
            if (loginBtn) {
                loginBtn.click();
            }
            return false;
        });
    }
});
