// AR Preview JavaScript
// This file handles AR functionality for the dashboard

let arPreviewInitialized = false;

// Three.js variables for 3D viewer
let scene, camera, renderer, controls;
let currentModel = null;
let models = [];
let autoRotate = false;
let wireframeMode = false;

// Alert function for AR preview
function showAlert(message, type = 'info') {
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

// Initialize AR preview when the AR tab is shown
function initializeARPreview() {
    if (arPreviewInitialized) return;

    console.log('Initializing AR Preview...');
    arPreviewInitialized = true;

    // Load AR models when the AR tab becomes active
    const arTab = document.querySelector('a[onclick="showTab(\'ar\')"]');
    if (arTab) {
        arTab.addEventListener('click', function() {
            // Longer delay to ensure tab is visible and DOM is ready
            setTimeout(() => {
                loadARModels();
            }, 500);
        });
    }

    // Also check if AR tab is already active on page load
    setTimeout(() => {
        const arTabContent = document.getElementById('ar');
        if (arTabContent && arTabContent.classList.contains('active')) {
            console.log('AR tab already active, loading models...');
            loadARModels();
        }
    }, 1000);
}

// Load AR models for preview
async function loadARModels() {
    try {
        console.log('Loading AR models...');

        // Show loading state
        const modelGrid = document.getElementById('modelGrid');
        const modelGallery = document.getElementById('arModelGallery');

        if (modelGrid) {
            modelGrid.innerHTML = '<p style="text-align: center; color: #666; padding: 20px;">Loading models...</p>';
        }

        if (modelGallery) {
            modelGallery.style.display = 'block';
        }

        // Try the public endpoint first
        let response = await fetch('/api/ar/models/public');
        let data = await response.json();

        // If public endpoint fails, try the authenticated one
        if (!data.success) {
            response = await fetch('/api/ar/models');
            data = await response.json();
        }

        if (data.success) {
            models = data.models; // Store models for 3D viewer

            // Display in both old and new formats
            displayARModels(data.models);
            displayARModelsInDashboard(data.models);

            console.log(`Loaded ${data.models.length} AR models`);
        } else {
            console.error('Failed to load AR models:', data.error);
            if (modelGrid) {
                modelGrid.innerHTML = '<p style="text-align: center; color: #e74c3c; padding: 20px;">Failed to load models: ' + (data.error || 'Unknown error') + '</p>';
            }
        }
    } catch (error) {
        console.error('Error loading AR models:', error);
        const modelGrid = document.getElementById('modelGrid');
        if (modelGrid) {
            modelGrid.innerHTML = '<p style="text-align: center; color: #e74c3c; padding: 20px;">Error loading models: ' + error.message + '</p>';
        }
    }
}

// Display AR models in the grid
function displayARModels(models) {
    const modelGrid = document.getElementById('modelGrid');
    if (!modelGrid) {
        console.error('Model grid element not found');
        return;
    }

    // Clear existing content
    modelGrid.innerHTML = '';

    if (models.length === 0) {
        modelGrid.innerHTML = '<p style="text-align: center; color: #666; padding: 20px;">No models available</p>';
        return;
    }

    // Add models to grid
    models.forEach((model, index) => {
        const modelItem = document.createElement('div');
        modelItem.className = 'model-item';
        modelItem.innerHTML = `
            <div class="model-item-icon">${getModelIcon(model.category)}</div>
            <div class="model-item-name">${model.filename.replace('.glb', '').replace(/_/g, ' ')}</div>
            <div class="model-item-category">${model.category}</div>
        `;

        modelItem.onclick = () => previewARModel(model);
        modelGrid.appendChild(modelItem);
    });
}

// Get appropriate icon for model category
function getModelIcon(category) {
    const icons = {
        'seating': '🛋️',
        'tables': '🪑',
        'lighting': '💡',
        'beds': '🛏️',
        'storage': '🗄️',
        'decor': '🖼️',
        'furniture': '🏠'
    };
    return icons[category] || '🏠';
}

// Preview a model (show details or open 3D viewer)
function previewARModel(model) {
    console.log('Previewing model:', model);

    // Show model details
    showAlert(`Selected: ${model.filename.replace('.glb', '').replace(/_/g, ' ')} (${model.category})`, 'info');

    // Option 1: Open in 3D viewer
    // window.open('/3d-viewer', '_blank');

    // Option 2: Show model details in a modal
    showModelDetails(model);

    // Option 3: Add to AR scene (if available)
    // addModelToARScene(model);
}

// Show detailed model information
function showModelDetails(model) {
    // Create a simple modal or alert with model details
    const message = `
Model: ${model.filename.replace('.glb', '').replace(/_/g, ' ')}
Category: ${model.category}
URL: ${model.url}
    `;

    showAlert(message, 'info');
}

// Add model to AR scene (placeholder)
function addModelToARScene(model) {
    console.log('Adding model to AR scene:', model);
    showAlert('AR scene integration coming soon!', 'info');
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeARPreview();
});

// Also initialize when the page loads (backup)
window.addEventListener('load', function() {
    initializeARPreview();
});

// Function to be called from dashboard button
async function loadARModelsFromPreview() {
    await loadARModels();
}

// Initialize Three.js scene for dashboard 3D viewer
function initThreeJS() {
    const viewerMain = document.querySelector('.model-viewer-main');
    if (!viewerMain) {
        console.error('3D viewer container not found');
        // Show error message in the viewer area
        const arContainer = document.querySelector('.ar-preview-container');
        if (arContainer) {
            arContainer.innerHTML = `
                <div style="text-align: center; padding: 40px; color: #e74c3c;">
                    <h3>3D Viewer Container Not Found</h3>
                    <p>The 3D viewer container element is missing from the DOM.</p>
                    <p>Please check that the dashboard template includes the required elements.</p>
                </div>
            `;
        }
        return;
    }

    console.log('Initializing Three.js scene...');
    console.log('Container dimensions:', viewerMain.offsetWidth, viewerMain.offsetHeight);

    // Check if Three.js is loaded
    if (typeof THREE === 'undefined') {
        console.error('Three.js library not loaded');
        viewerMain.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #e74c3c;">
                <h3>Three.js Library Not Loaded</h3>
                <p>The Three.js library could not be loaded from CDN.</p>
                <p>Please check your internet connection and try refreshing the page.</p>
            </div>
        `;
        return;
    }

    // Clear any existing content
    viewerMain.innerHTML = '';

    try {
        // Scene
        scene = new THREE.Scene();
        scene.background = new THREE.Color(0x34495e);

        // Camera
        camera = new THREE.PerspectiveCamera(75, viewerMain.offsetWidth / viewerMain.offsetHeight, 0.1, 1000);
        camera.position.set(5, 5, 5);

        // Renderer
        renderer = new THREE.WebGLRenderer({
            antialias: true,
            alpha: false
        });
        renderer.setSize(viewerMain.offsetWidth, viewerMain.offsetHeight);
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        renderer.setClearColor(0x34495e, 1);
        renderer.setPixelRatio(window.devicePixelRatio);

        // Add canvas to container
        viewerMain.appendChild(renderer.domElement);
        console.log('Canvas added to container, dimensions:', renderer.domElement.width, 'x', renderer.domElement.height);

        // Controls
        controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        controls.enableZoom = true;
        controls.enablePan = true;
        controls.enableRotate = true;

        // Lighting
        setupLighting();



        // Handle window resize
        window.addEventListener('resize', onWindowResize);

        // Start render loop
        animate();

        console.log('Three.js scene initialized successfully');

    } catch (error) {
        console.error('Error initializing Three.js scene:', error);
        viewerMain.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #e74c3c;">
                <h3>Three.js Initialization Error</h3>
                <p>Error: ${error.message}</p>
                <p>Please check the browser console for more details.</p>
            </div>
        `;
    }
}



function setupLighting() {
    // Ambient light
    const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
    scene.add(ambientLight);

    // Directional light (key light)
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(10, 10, 5);
    directionalLight.castShadow = true;
    directionalLight.shadow.mapSize.width = 2048;
    directionalLight.shadow.mapSize.height = 2048;
    scene.add(directionalLight);

    // Fill light
    const fillLight = new THREE.DirectionalLight(0x87CEEB, 0.3);
    fillLight.position.set(-5, 5, -5);
    scene.add(fillLight);

    // Rim light
    const rimLight = new THREE.DirectionalLight(0xffffff, 0.4);
    rimLight.position.set(0, 0, -10);
    scene.add(rimLight);
}

function animate() {
    requestAnimationFrame(animate);

    if (controls) {
        controls.update();
    }

    if (autoRotate && currentModel) {
        currentModel.rotation.y += 0.01;
    }

    renderer.render(scene, camera);
}

function onWindowResize() {
    const viewerMain = document.querySelector('.model-viewer-main');
    if (viewerMain && camera && renderer) {
        camera.aspect = viewerMain.offsetWidth / viewerMain.offsetHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(viewerMain.offsetWidth, viewerMain.offsetHeight);
    }
}

// Load 3D model in dashboard viewer
async function loadModelInDashboard(model) {
    try {
        console.log('Loading model:', model);
        updateStatus('Loading 3D model...');
        showLoading(true);

        // Clear current model
        if (currentModel) {
            scene.remove(currentModel);
            currentModel = null;
        }

        // Load GLTF model
        const loader = new THREE.GLTFLoader();
        console.log('Loading GLTF from:', model.url);

        // Try loading with the provided URL first
        let gltf;
        try {
            gltf = await new Promise((resolve, reject) => {
                loader.load(
                    model.url,
                    (gltf) => {
                        console.log('GLTF loaded successfully:', gltf);
                        resolve(gltf);
                    },
                    (progress) => {
                        console.log('Loading progress:', progress);
                    },
                    (error) => {
                        console.error('Error loading GLTF:', error);
                        reject(error);
                    }
                );
            });
        } catch (error) {
            console.error('Failed to load model with URL:', model.url);
            console.log('Trying with absolute URL...');

            // Try with absolute URL
            const absoluteUrl = window.location.origin + model.url;
            console.log('Trying absolute URL:', absoluteUrl);

            try {
                gltf = await new Promise((resolve, reject) => {
                    loader.load(
                        absoluteUrl,
                        (gltf) => {
                            console.log('GLTF loaded successfully with absolute URL:', gltf);
                            resolve(gltf);
                        },
                        (progress) => {
                            console.log('Loading progress:', progress);
                        },
                        (error) => {
                            console.error('Error loading GLTF with absolute URL:', error);
                            reject(error);
                        }
                    );
                });
            } catch (absoluteError) {
                console.error('Failed to load model with both relative and absolute URLs');
                throw new Error(`Failed to load model. Tried: ${model.url} and ${absoluteUrl}. Error: ${absoluteError.message}`);
            }
        }

        console.log('GLTF object:', gltf);

        // Add model to scene
        currentModel = gltf.scene;
        console.log('Adding model to scene:', currentModel);
        scene.add(currentModel);

        // Set up shadows and materials
        currentModel.traverse((child) => {
            if (child.isMesh) {
                child.castShadow = true;
                child.receiveShadow = true;
                console.log('Mesh found:', child);
            }
        });

        // Center and scale model
        const box = new THREE.Box3().setFromObject(currentModel);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());

        console.log('Model bounds:', box);
        console.log('Model center:', center);
        console.log('Model size:', size);

        // Center the model
        currentModel.position.sub(center);

        // Scale to reasonable size
        const maxDim = Math.max(size.x, size.y, size.z);
        const targetSize = 2;
        const scale = targetSize / maxDim;
        currentModel.scale.set(scale, scale, scale);

        console.log('Model scaled by:', scale);

        // Update UI
        updateModelInfo(model);
        showLoading(false);
        updateStatus('Model loaded successfully');

        // Reset camera to fit model
        resetCamera();

    } catch (error) {
        console.error('Error loading model:', error);
        updateStatus('Error loading model: ' + error.message);
        showLoading(false);

        // Show error in viewer
        const viewerMain = document.querySelector('.model-viewer-main');
        if (viewerMain) {
            viewerMain.innerHTML = `
                <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
                           text-align: center; color: white; background: rgba(0,0,0,0.8);
                           padding: 20px; border-radius: 8px;">
                    <h3 style="color: #e74c3c;">Error Loading Model</h3>
                    <p>${error.message}</p>
                    <p>URL: ${model.url}</p>
                </div>
            `;
        }
    }
}

function updateModelInfo(model) {
    const info = document.getElementById('viewerInfo');
    const name = document.getElementById('modelName');
    const category = document.getElementById('modelCategory');
    const dimensions = document.getElementById('modelDimensions');

    if (name) name.textContent = model.filename.replace('.glb', '').replace(/_/g, ' ');
    if (category) category.textContent = `Category: ${model.category}`;
    if (dimensions) dimensions.textContent = 'Dimensions: Loading...';

    if (info) info.style.display = 'block';

    // Calculate dimensions if model is loaded
    if (currentModel) {
        const box = new THREE.Box3().setFromObject(currentModel);
        const size = box.getSize(new THREE.Vector3());
        if (dimensions) dimensions.textContent = `Dimensions: ${size.x.toFixed(2)} × ${size.y.toFixed(2)} × ${size.z.toFixed(2)}`;
    }
}

function resetCamera() {
    if (currentModel) {
        const box = new THREE.Box3().setFromObject(currentModel);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());

        // Position camera to view the model
        const maxDim = Math.max(size.x, size.y, size.z);
        const fov = camera.fov * (Math.PI / 180);
        let cameraZ = Math.abs(maxDim / 2 / Math.tan(fov / 2));

        camera.position.set(center.x + maxDim, center.y + maxDim, center.z + cameraZ * 2);
        camera.lookAt(center);

        if (controls) {
            controls.target.set(center.x, center.y, center.z);
            controls.update();
        }
    }
}

function resetView() {
    resetCamera();
    updateStatus('View reset');
}

function toggleAutoRotate() {
    autoRotate = !autoRotate;
    const btn = document.getElementById('autoRotateBtn');
    if (btn) btn.classList.toggle('active', autoRotate);
    updateStatus(autoRotate ? 'Auto rotate ON' : 'Auto rotate OFF');
}

function toggleWireframe() {
    wireframeMode = !wireframeMode;
    const btn = document.getElementById('wireframeBtn');
    if (btn) btn.classList.toggle('active', wireframeMode);

    if (currentModel) {
        currentModel.traverse((child) => {
            if (child.isMesh && child.material) {
                if (Array.isArray(child.material)) {
                    child.material.forEach(mat => {
                        mat.wireframe = wireframeMode;
                    });
                } else {
                    child.material.wireframe = wireframeMode;
                }
            }
        });
    }

    updateStatus(wireframeMode ? 'Wireframe ON' : 'Wireframe OFF');
}

function setPresetView(view) {
    // Remove active class from all preset buttons
    document.querySelectorAll('.preset-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // Add active class to clicked button
    if (event.target) event.target.classList.add('active');

    if (!currentModel) return;

    const box = new THREE.Box3().setFromObject(currentModel);
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z);

    switch(view) {
        case 'front':
            camera.position.set(center.x, center.y, center.z + maxDim * 2);
            break;
        case 'top':
            camera.position.set(center.x, center.y + maxDim * 2, center.z);
            break;
        case 'side':
            camera.position.set(center.x + maxDim * 2, center.y, center.z);
            break;
        case 'iso':
            camera.position.set(center.x + maxDim, center.y + maxDim, center.z + maxDim);
            break;
    }

    camera.lookAt(center);
    if (controls) {
        controls.target.set(center.x, center.y, center.z);
        controls.update();
    }
}

function showLoading(show) {
    const loading = document.getElementById('loading');
    const noModel = document.getElementById('noModel');

    if (show) {
        if (loading) loading.style.display = 'block';
        if (noModel) noModel.style.display = 'none';
    } else {
        if (loading) loading.style.display = 'none';
        if (!currentModel && noModel) {
            noModel.style.display = 'block';
        }
    }
}

function updateStatus(message) {
    const status = document.getElementById('status');
    if (status) status.textContent = message;
}

// Control sliders
function setupControls() {
    const scaleSlider = document.getElementById('scaleSlider');
    const rotationYSlider = document.getElementById('rotationYSlider');
    const rotationXSlider = document.getElementById('rotationXSlider');

    if (scaleSlider) {
        scaleSlider.addEventListener('input', (e) => {
            const scale = parseFloat(e.target.value);
            document.getElementById('scaleValue').textContent = scale;

            if (currentModel) {
                currentModel.scale.set(scale, scale, scale);
            }
        });
    }

    if (rotationYSlider) {
        rotationYSlider.addEventListener('input', (e) => {
            const rotation = parseFloat(e.target.value);
            document.getElementById('rotationYValue').textContent = rotation + '°';

            if (currentModel) {
                currentModel.rotation.y = rotation * Math.PI / 180;
            }
        });
    }

    if (rotationXSlider) {
        rotationXSlider.addEventListener('input', (e) => {
            const rotation = parseFloat(e.target.value);
            document.getElementById('rotationXValue').textContent = rotation + '°';

            if (currentModel) {
                currentModel.rotation.x = rotation * Math.PI / 180;
            }
        });
    }
}

// Update displayARModels to also work with the new 3D viewer
function displayARModelsInDashboard(models) {
    const modelList = document.getElementById('modelList');
    if (!modelList) {
        console.error('Model list element not found');
        return;
    }

    // Clear existing content
    modelList.innerHTML = '';

    if (models.length === 0) {
        modelList.innerHTML = '<p style="color: #666; font-size: 12px; text-align: center; padding: 20px;">No models available</p>';
        return;
    }

    // Add models to list
    models.forEach((model, index) => {
        const modelItem = document.createElement('div');
        modelItem.className = 'model-item';
        if (index === 0) modelItem.classList.add('selected');

        modelItem.innerHTML = `
            <div class="model-item-icon">${getModelIcon(model.category)}</div>
            <div class="model-item-name">${model.filename.replace('.glb', '').replace(/_/g, ' ')}</div>
            <div class="model-item-category">${model.category}</div>
        `;

        modelItem.onclick = () => {
            // Remove previous selection
            document.querySelectorAll('.model-list .model-item').forEach(item => {
                item.classList.remove('selected');
            });

            // Add selection to clicked item
            modelItem.classList.add('selected');

            // Load the model in 3D viewer
            loadModelInDashboard(model);
        };

        modelList.appendChild(modelItem);
    });

    // Initialize 3D viewer if not already done
    if (!scene) {
        initThreeJS();
        setupControls();
    }
}
