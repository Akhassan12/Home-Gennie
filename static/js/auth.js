// Authentication JavaScript
let registeredEmail = '';
let loginData = {};
let currentUser = null;

function showAlert(message, type = 'success') {
    const alertContainer = document.getElementById('alertContainer');
    alertContainer.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
    setTimeout(() => alertContainer.innerHTML = '', 5000);
}

function toggleAuthForm() {
    document.getElementById('loginForm').classList.toggle('hidden');
    document.getElementById('registerForm').classList.toggle('hidden');
    document.getElementById('alertContainer').innerHTML = '';
}

async function handleRegister(e) {
    e.preventDefault();
    const username = document.getElementById('regUsername').value;
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPassword').value;

    try {
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password })
        });

        const data = await response.json();

        if (response.ok) {
            showAlert(data.message, 'success');
            registeredEmail = email; // Store email for OTP verification
            document.getElementById('registerForm').classList.add('hidden');
            document.getElementById('otpForm').classList.remove('hidden');
        } else {
            showAlert(data.error, 'error');
        }
    } catch (error) {
        showAlert('Registration failed. Please try again.', 'error');
    }
}

async function verifyOTP() {
    const otp = document.getElementById('otpInput').value;
    if (!otp || !registeredEmail) {
        showAlert('Please enter OTP', 'error');
        return;
    }

    try {
        const response = await fetch('/api/verify-otp', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: registeredEmail, otp: otp })
        });

        const data = await response.json();

        if (response.ok) {
            showAlert(data.message, 'success');
            document.getElementById('otpForm').classList.add('hidden');
            document.getElementById('loginForm').classList.remove('hidden');
        } else {
            showAlert(data.error, 'error');
        }
    } catch (error) {
        showAlert('OTP verification failed. Please try again.', 'error');
    }
}

async function resendOTP() {
    if (!registeredEmail) {
        showAlert('Email not found. Please register again.', 'error');
        return;
    }

    try {
        const response = await fetch('/api/resend-verification', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: registeredEmail })
        });

        const data = await response.json();
        showAlert(data.message || data.error, response.ok ? 'success' : 'error');
    } catch (error) {
        showAlert('Failed to resend OTP. Please try again.', 'error');
    }
}

function backToLogin() {
    document.getElementById('loginOtpForm').classList.add('hidden');
    document.getElementById('loginForm').classList.remove('hidden');
    document.getElementById('loginOtpInput').value = '';
}

async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    const remember = document.getElementById('rememberMe').checked;

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, remember })
        });

        const data = await response.json();

        if (response.ok && data.require_otp) {
            // Store login data for OTP verification
            loginData = {
                username,
                password,
                remember,
                email: data.email
            };
            // Show OTP form
            document.getElementById('loginForm').classList.add('hidden');
            document.getElementById('loginOtpForm').classList.remove('hidden');
            showAlert('OTP sent to your email', 'success');
        } else if (response.ok) {
            // Login successful with 2FA, redirect to dashboard
            currentUser = data;
            // Store user data in localStorage for dashboard
            localStorage.setItem('loggedInUser', JSON.stringify({
                username: data.username,
                email: data.email
            }));
            // Redirect to dashboard page
            window.location.href = '/dashboard';
        } else if (data.needs_verification) {
            showAlert(data.error, 'warning');
            showAlert(
                data.error +
                '<br><button onclick="resendVerification()" class="btn btn-primary" style="margin-top: 10px;">Resend Verification Email</button>',
                'warning'
            );
        } else if (response.status === 401) {
            showAlert('Invalid username or password', 'error');
        } else {
            showAlert(data.error || 'Login failed. Please try again.', 'error');
        }
    } catch (error) {
        showAlert('Login failed. Please try again.', 'error');
    }
}

async function verifyLoginOTP() {
    const otp = document.getElementById('loginOtpInput').value;
    if (!otp || !loginData.username) {
        showAlert('Please enter OTP', 'error');
        return;
    }

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: loginData.username,
                password: loginData.password,
                remember: loginData.remember,
                otp: otp
            })
        });

        const data = await response.json();

        if (response.ok) {
            currentUser = data;
            // Store user data in localStorage for dashboard
            localStorage.setItem('loggedInUser', JSON.stringify({
                username: data.username,
                email: data.email
            }));
            // Redirect to dashboard page
            window.location.href = '/dashboard';
        } else {
            showAlert(data.error, 'error');
        }
    } catch (error) {
        showAlert('Login failed. Please try again.', 'error');
    }
}

async function resendLoginOTP() {
    if (!loginData.username || !loginData.password) {
        showAlert('Please try logging in again', 'error');
        backToLogin();
        return;
    }

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: loginData.username,
                password: loginData.password,
                remember: loginData.remember
            })
        });

        const data = await response.json();
        if (response.ok && data.require_otp) {
            showAlert('New OTP sent to your email', 'success');
        } else {
            showAlert(data.error, 'error');
        }
    } catch (error) {
        showAlert('Failed to resend OTP. Please try again.', 'error');
    }
}

async function resendVerification() {
    if (!currentUser || !currentUser.email) {
        return;
    }

    try {
        const response = await fetch('/api/resend-verification', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: currentUser.email })
        });

        const data = await response.json();
        showAlert(data.message || data.error, response.ok ? 'success' : 'error');
    } catch (error) {
        showAlert('Failed to resend verification email.', 'error');
    }
}



// Password Reset Functions
let resetEmail = '';

function showResetPasswordForm() {
    document.getElementById('loginForm').classList.add('hidden');
    document.getElementById('resetPasswordForm').classList.remove('hidden');
    document.getElementById('alertContainer').innerHTML = '';
}

async function requestPasswordReset() {
    const email = document.getElementById('resetEmail').value;
    if (!email) {
        showAlert('Please enter your email', 'error');
        return;
    }

    try {
        const response = await fetch('/api/reset-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });

        const data = await response.json();

        if (response.ok) {
            resetEmail = email; // Store email for OTP verification
            document.getElementById('resetPasswordForm').classList.add('hidden');
            document.getElementById('resetPasswordOtpForm').classList.remove('hidden');
            showAlert('Reset code sent to your email', 'success');
        } else {
            showAlert(data.error, 'error');
        }
    } catch (error) {
        showAlert('Failed to request password reset. Please try again.', 'error');
    }
}

async function verifyPasswordReset() {
    const otp = document.getElementById('resetOtpInput').value;
    const newPassword = document.getElementById('newPasswordInput').value;

    if (!otp || !newPassword || !resetEmail) {
        showAlert('Please enter OTP and new password', 'error');
        return;
    }

    if (newPassword.length < 6) {
        showAlert('Password must be at least 6 characters', 'error');
        return;
    }

    try {
        const response = await fetch('/api/reset-password/verify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: resetEmail,
                otp: otp,
                new_password: newPassword
            })
        });

        const data = await response.json();

        if (response.ok) {
            showAlert(data.message, 'success');
            resetEmail = ''; // Clear stored email
            document.getElementById('resetPasswordOtpForm').classList.add('hidden');
            document.getElementById('loginForm').classList.remove('hidden');
        } else {
            showAlert(data.error, 'error');
        }
    } catch (error) {
        showAlert('Password reset failed. Please try again.', 'error');
    }
}

async function resendResetOTP() {
    if (!resetEmail) {
        showAlert('Please try resetting your password again', 'error');
        return;
    }

    try {
        const response = await fetch('/api/reset-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: resetEmail })
        });

        const data = await response.json();
        showAlert(data.message || data.error, response.ok ? 'success' : 'error');
    } catch (error) {
        showAlert('Failed to resend reset code. Please try again.', 'error');
    }
}

// Toggle password visibility
function togglePasswordVisibility(inputId) {
    const input = document.getElementById(inputId);
    const btn = document.querySelector(`[data-field="${inputId}"]`);
    const eyeOpen = btn.querySelector('.eye-open');
    const eyeClosed = btn.querySelector('.eye-closed');
    
    const isPassword = input.type === 'password';
    input.type = isPassword ? 'text' : 'password';
    
    // Toggle eye icons with animation
    if (isPassword) {
        // Show open eye when revealing password
        eyeClosed.style.display = 'none';
        eyeOpen.style.display = 'block';
        eyeOpen.classList.add('eye-animate-open');
        eyeClosed.classList.remove('eye-animate-close');
    } else {
        // Show closed eye when hiding password
        eyeOpen.style.display = 'none';
        eyeClosed.style.display = 'block';
        eyeClosed.classList.add('eye-animate-close');
        eyeOpen.classList.remove('eye-animate-open');
    }
}

// Export functions
window.showResetPasswordForm = showResetPasswordForm;
window.togglePasswordVisibility = togglePasswordVisibility;
