// Dashboard JavaScript
let currentUser = null;

// Alert function for dashboard
function showAlert(message, type = 'success') {
    // Create alert element if alertContainer doesn't exist
    let alertContainer = document.getElementById('alertContainer');
    if (!alertContainer) {
        alertContainer = document.createElement('div');
        alertContainer.id = 'alertContainer';
        document.querySelector('.content').prepend(alertContainer);
    }

    alertContainer.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
    setTimeout(() => alertContainer.innerHTML = '', 5000);
}

// Auto login and theme initialization
async function initializeDashboard() {
    // Check and apply saved theme
    const isDark = localStorage.getItem('darkTheme') === 'true';
    if (isDark) {
        document.body.classList.add('dark');
    }

    // Try to load user data from localStorage first
    const user = localStorage.getItem("loggedInUser");
    if (user) {
        try {
            const userData = JSON.parse(user);
            if (document.getElementById("profileName")) {
                document.getElementById("profileName").textContent = userData.username || 'User';
            }
        } catch (e) {
            console.error('Error parsing user data:', e);
            loadUserFromServer();
        }
    } else {
        // Try to get current user data from server
        await loadUserFromServer();
    }
}

// Load user data from server
async function loadUserFromServer() {
    try {
        const response = await fetch('/api/profile/get');
        const data = await response.json();

        if (response.ok && document.getElementById("profileName")) {
            document.getElementById("profileName").textContent = data.username || 'User';
            // Also store in localStorage for future use
            localStorage.setItem('loggedInUser', JSON.stringify({
                username: data.username,
                email: data.email
            }));
        }
    } catch (error) {
        console.error('Error loading user data:', error);
        if (document.getElementById("profileName")) {
            document.getElementById("profileName").textContent = 'User';
        }
    }
}

window.onload = initializeDashboard;

// Dashboard features
function showTab(tab) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.getElementById(tab).classList.add('active');
    document.querySelectorAll('.sidebar nav a').forEach(a => a.classList.remove('active'));
    if (event && event.target) {
        event.target.classList.add('active');
    }
}

function toggleTheme() {
    document.body.classList.toggle('dark');
    // Save theme preference
    const isDark = document.body.classList.contains('dark');
    localStorage.setItem('darkTheme', isDark);
}

function addProject() {
    let n = document.getElementById('projName').value,
        c = document.getElementById('projClient').value,
        d = document.getElementById('projDate').value,
        s = document.getElementById('projStatus').value;
    if (n && c && d) {
        let div = document.createElement('div');
        div.className = "item";
        div.innerText = `${n} – ${c} [${s}] – Due: ${d}`;
        document.getElementById('projList').appendChild(div);
    }
}

function searchProjects() {
    let v = document.getElementById('projSearch').value.toLowerCase();
    document.querySelectorAll('#projList .item').forEach(i => {
        i.style.display = i.innerText.toLowerCase().includes(v) ? 'block' : 'none';
    });
}

function addToAR(src) {
    let img = document.createElement('img');
    img.src = src;
    img.className = "furniture";
    img.style.left = "50px";
    img.style.top = "50px";
    document.getElementById('arArea').appendChild(img);
    makeDraggable(img);
}

function makeDraggable(el) {
    let drag = false, x, y;
    el.addEventListener('mousedown', e => {
        drag = true;
        x = e.offsetX;
        y = e.offsetY;
    });
    document.addEventListener('mouseup', () => drag = false);
    document.addEventListener('mousemove', e => {
        if (drag) {
            el.style.left = (e.pageX - x - 220) + 'px';
            el.style.top = (e.pageY - y - 100) + 'px';
        }
    });
    el.addEventListener('dblclick', () => el.remove());
}

function addBudget() {
    let p = document.getElementById('budgetProj').value,
        a = parseFloat(document.getElementById('budgetAmt').value);
    if (p && a) {
        let d = document.createElement('div');
        d.className = "item";
        d.innerText = `${p}: $${a}`;
        document.getElementById('budgetList').appendChild(d);
    }
}

// Profile Menu
function toggleProfileMenu() {
    const dropdown = document.getElementById('profileDropdown');
    const arrow = document.querySelector('.profile-arrow');
    dropdown.classList.toggle('show');
    arrow.style.transform = dropdown.classList.contains('show') ? 'rotate(180deg)' : 'rotate(0)';
}

// Close profile menu when clicking outside
document.addEventListener('click', (e) => {
    const profileMenu = document.querySelector('.profile-menu');
    const dropdown = document.getElementById('profileDropdown');
    if (!profileMenu.contains(e.target) && dropdown.classList.contains('show')) {
        dropdown.classList.remove('show');
        document.querySelector('.profile-arrow').style.transform = 'rotate(0)';
    }
});

// Feedback submission
function submitFeedback() {
    const feedback = document.getElementById('feedbackText').value.trim();
    if (!feedback) {
        alert('Please enter some feedback before submitting.');
        return;
    }
    alert('Thank you for your feedback!');
    document.getElementById('feedbackText').value = '';
}

// Profile Editor Functions
async function loadProfileData() {
    try {
        showAlert('Loading profile data...', 'info');
        const response = await fetch('/api/profile/get');
        const data = await response.json();

        if (response.ok) {
            // Fill form fields with profile data
            document.getElementById('profileUsername').value = data.username || '';
            document.getElementById('profileEmail').value = data.email || '';
            document.getElementById('profileBio').value = data.bio || '';
            document.getElementById('profileCompany').value = data.company || '';
            document.getElementById('profileWebsite').value = data.website || '';
            document.getElementById('profileLocation').value = data.location || '';
            document.getElementById('profileEmailNotif').checked = data.email_notifications || false;

            if (data.avatar) {
                const avatar = document.getElementById('profileAvatarLarge');
                avatar.style.backgroundImage = `url(${data.avatar})`;
                avatar.style.backgroundSize = 'cover';
                avatar.style.backgroundPosition = 'center';
                avatar.innerHTML = '';
            }
        } else {
            showAlert('Failed to load profile data: ' + data.error, 'error');
        }
    } catch (error) {
        showAlert('Failed to load profile data. Please try again.', 'error');
        console.error('Profile load error:', error);
    }
}

async function updateProfile(event) {
    event.preventDefault();

    try {
        showAlert('Saving profile changes...', 'info');

        const formData = {
            username: document.getElementById('profileUsername').value.trim(),
            email: document.getElementById('profileEmail').value.trim(),
            bio: document.getElementById('profileBio').value.trim(),
            company: document.getElementById('profileCompany').value.trim(),
            website: document.getElementById('profileWebsite').value.trim(),
            location: document.getElementById('profileLocation').value.trim(),
            emailNotifications: document.getElementById('profileEmailNotif').checked
        };

        // Validate required fields
        if (!formData.username || !formData.email) {
            showAlert('Username and email are required', 'error');
            return;
        }

        // Handle password change
        const newPassword = document.getElementById('newPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        const currentPassword = document.getElementById('currentPassword').value;

        if (newPassword || confirmPassword || currentPassword) {
            if (newPassword !== confirmPassword) {
                showAlert('New passwords do not match', 'error');
                return;
            }
            if (!currentPassword) {
                showAlert('Current password is required to change password', 'error');
                return;
            }
            if (newPassword.length < 6) {
                showAlert('New password must be at least 6 characters', 'error');
                return;
            }
            formData.currentPassword = currentPassword;
            formData.newPassword = newPassword;
        }

        const response = await fetch('/api/profile/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (response.ok) {
            showAlert('Profile updated successfully', 'success');
            // Update UI elements
            document.getElementById('profileName').textContent = formData.username;
            // Update localStorage with new username
            const currentUserData = JSON.parse(localStorage.getItem('loggedInUser') || '{}');
            currentUserData.username = formData.username;
            localStorage.setItem('loggedInUser', JSON.stringify(currentUserData));
            // Clear password fields
            document.getElementById('currentPassword').value = '';
            document.getElementById('newPassword').value = '';
            document.getElementById('confirmPassword').value = '';
            // Close dropdown if open
            const dropdown = document.getElementById('profileDropdown');
            if (dropdown.classList.contains('show')) {
                dropdown.classList.remove('show');
                document.querySelector('.profile-arrow').style.transform = 'rotate(0)';
            }
        } else {
            showAlert(data.error || 'Failed to update profile', 'error');
        }
    } catch (error) {
        showAlert('Failed to update profile. Please try again.', 'error');
        console.error('Profile update error:', error);
    }
}

function resetForm() {
    // Clear form fields
    document.getElementById('profileForm').reset();
    // Reset avatar
    const avatar = document.getElementById('profileAvatarLarge');
    avatar.style.backgroundImage = 'none';
    avatar.innerHTML = '👤';
    // Reload original data
    loadProfileData();
}

function handleAvatarUpload(event) {
    const file = event.target.files[0];
    if (!file) {
      return;
    }

    if (file.size > 2 * 1024 * 1024) {
        showAlert('File size should not exceed 2MB', 'error');
        return;
    }

    const reader = new FileReader();
    reader.onload = function(e) {
        const avatar = document.getElementById('profileAvatarLarge');
        avatar.style.backgroundImage = `url(${e.target.result})`;
        avatar.style.backgroundSize = 'cover';
        avatar.style.backgroundPosition = 'center';
        avatar.innerHTML = ''; // Remove the default icon
    };
    reader.readAsDataURL(file);
}

// Fix for file input click issue
function triggerFileUpload() {
    const fileInput = document.getElementById('avatarUpload');
    if (fileInput) {
        fileInput.click();
    } else {
        console.error('File input element not found');
    }
}

// Load profile data when the profile tab is opened
async function loadProfileData() {
    try {
        const response = await fetch('/api/profile/get');
        const data = await response.json();
        if (response.ok) {
            document.getElementById('profileUsername').value = data.username || '';
            document.getElementById('profileEmail').value = data.email || '';
            document.getElementById('profileBio').value = data.bio || '';
            document.getElementById('profileCompany').value = data.company || '';
            document.getElementById('profileWebsite').value = data.website || '';
            document.getElementById('profileLocation').value = data.location || '';
            document.getElementById('profileEmailNotif').checked = data.emailNotifications || false;

            if (data.avatar) {
                const avatar = document.getElementById('profileAvatarLarge');
                avatar.style.backgroundImage = `url(${data.avatar})`;
                avatar.style.backgroundSize = 'cover';
                avatar.style.backgroundPosition = 'center';
                avatar.innerHTML = '';
            }
        }
    } catch (error) {
        showAlert('Failed to load profile data', 'error');
    }
}

// Add profile tab click handler to load data
document.addEventListener('DOMContentLoaded', function() {
    const profileTab = document.querySelector('a[onclick="showTab(\'profile\')"]');
    if (profileTab) {
        profileTab.addEventListener('click', loadProfileData);
    }
});

// Logout function
async function logout() {
    try {
        // Call the server to logout
        const response = await fetch('/api/logout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        // Clear local storage
        localStorage.removeItem("loggedInUser");

        // Redirect to login page
        window.location.href = "/";
    } catch (error) {
        console.error('Logout error:', error);
        // Still redirect even if there's an error
        window.location.href = "/";
    }
}

// Profile Editor Function
function showProfileEditor() {
    // Hide the profile dropdown
    document.getElementById('profileDropdown').classList.remove('show');
    document.querySelector('.profile-arrow').style.transform = 'rotate(0)';

    // Show the profile tab
    showTab('profile');

    // Load profile data
    loadProfileData();
}

// AR Dashboard Functions
async function loadARModels() {
    try {
        showAlert('Loading AR models...', 'info');

        // Try the public endpoint first, then fallback to the authenticated one
        let response = await fetch('/api/ar/models/public');
        let data = await response.json();

        // If public endpoint fails, try the authenticated one
        if (!data.success) {
            response = await fetch('/api/ar/models');
            data = await response.json();
        }

        if (data.success) {
            displayARModels(data.models);
            showAlert(`Loaded ${data.models.length} AR models`, 'success');
        } else {
            showAlert('Failed to load AR models: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Error loading AR models:', error);
        showAlert('Error loading AR models: ' + error.message, 'error');
    }
}

function displayARModels(models) {
    const modelGrid = document.getElementById('modelGrid');
    const modelGallery = document.getElementById('arModelGallery');

    if (!modelGrid || !modelGallery) {
        console.error('AR model display elements not found');
        return;
    }

    // Clear existing models
    modelGrid.innerHTML = '';

    // Add models to grid
    models.forEach(model => {
        const modelItem = document.createElement('div');
        modelItem.className = 'model-item';
        modelItem.innerHTML = `
            <div class="model-item-icon">${getModelIcon(model.category)}</div>
            <div class="model-item-name">${model.name}</div>
            <div class="model-item-category">${model.category}</div>
        `;

        modelItem.onclick = () => previewARModel(model);
        modelGrid.appendChild(modelItem);
    });

    // Show the gallery
    modelGallery.style.display = 'block';
}

function getModelIcon(category) {
    const icons = {
        'seating': '🛋️',
        'tables': '🪑',
        'lighting': '💡',
        'beds': '🛏️',
        'storage': '🗄️',
        'decor': '🖼️'
    };
    return icons[category] || '🏠';
}

function previewARModel(model) {
    showAlert(`Selected: ${model.name} (${model.category})`, 'info');

    // In a full implementation, this would show a 3D preview of the model
    // For now, just show model info

    // Could open a modal or show detailed preview here
    // For example, show model dimensions, category, and options to place it
}
