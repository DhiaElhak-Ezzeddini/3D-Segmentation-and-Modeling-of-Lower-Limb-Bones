/**
 * app.js - Main Application Logic
 */

// Configuration
const API_URL = 'http://localhost:8001';

// Initialize components
let viewer, boneManager, implantManager;
let currentJobId = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Create viewer
    viewer = new Viewer3D('viewer-canvas');

    // Create managers (using mesh version for smooth rendering)
    boneManager = new BoneManagerMesh(viewer, API_URL);
    implantManager = new ImplantManager(viewer, API_URL);

    // Setup event listeners
    setupUploadHandlers();
    setupTransformControls();
    setupCameraControls();
    setupViewerControls();
    setupImplantHandlers();
    setupObjectSelectionHandlers();
});

// ============================================================================
// Upload Handlers
// ============================================================================

function setupUploadHandlers() {
    const uploadZone = document.getElementById('upload-zone');
    const fileInput = document.getElementById('file-input');
    const uploadStatus = document.getElementById('upload-status');

    // Click to upload
    uploadZone.addEventListener('click', () => fileInput.click());

    // File selected
    fileInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (file) {
            await handleSegmentationUpload(file);
        }
    });

    // Drag and drop
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('drag-over');
    });

    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('drag-over');
    });

    uploadZone.addEventListener('drop', async (e) => {
        e.preventDefault();
        uploadZone.classList.remove('drag-over');

        const file = e.dataTransfer.files[0];
        if (file) {
            await handleSegmentationUpload(file);
        }
    });
}

async function handleSegmentationUpload(file) {
    const uploadStatus = document.getElementById('upload-status');
    const loadingOverlay = document.getElementById('loading-overlay');

    try {
        // Show loading
        loadingOverlay.classList.remove('hidden');
        uploadStatus.textContent = 'Uploading...';
        uploadStatus.className = 'upload-status';

        // Upload file
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_URL}/upload-segmentation`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('Upload failed');

        const result = await response.json();
        currentJobId = result.job_id;

        uploadStatus.textContent = `✓ Uploaded: ${file.name}`;
        uploadStatus.className = 'upload-status success';

        // Clear previous bones
        boneManager.clearAllBones();

        // Load bones
        uploadStatus.textContent = 'Processing bones...';
        const metadata = await boneManager.loadBonesFromJob(currentJobId);

        // Update UI
        updateBoneList(metadata.bones);
        updateStats(metadata);

        uploadStatus.textContent = `✓ Loaded ${metadata.total_bones} bones`;
        loadingOverlay.classList.add('hidden');

    } catch (error) {
        console.error('Upload error:', error);
        uploadStatus.textContent = `✗ Error: ${error.message}`;
        uploadStatus.className = 'upload-status error';
        loadingOverlay.classList.add('hidden');
    }
}

// ============================================================================
// Bone List UI
// ============================================================================

function updateBoneList(bones) {
    const boneList = document.getElementById('bone-list');
    boneList.innerHTML = '';

    bones.forEach(bone => {
        const item = document.createElement('div');
        item.className = 'bone-item';
        item.dataset.boneName = bone.name;

        const colorDiv = document.createElement('div');
        colorDiv.className = 'bone-color';
        colorDiv.style.backgroundColor = `rgb(${bone.color.join(',')})`;

        const nameSpan = document.createElement('span');
        nameSpan.className = 'bone-name';
        nameSpan.textContent = bone.name.replace(/_/g, ' ');

        const toggle = document.createElement('div');
        toggle.className = 'bone-toggle visible';
        toggle.addEventListener('click', (e) => {
            e.stopPropagation();
            const isVisible = toggle.classList.toggle('visible');
            boneManager.toggleBoneVisibility(bone.name, isVisible);
        });

        item.appendChild(colorDiv);
        item.appendChild(nameSpan);
        item.appendChild(toggle);

        item.addEventListener('click', () => {
            boneManager.selectBone(bone.name);
        });

        boneList.appendChild(item);
    });
}

function updateStats(metadata) {
    const statsContent = document.getElementById('stats-content');
    statsContent.innerHTML = '';

    // Total bones
    addStat(statsContent, 'Total Bones', metadata.total_bones);

    // Total points
    const totalPoints = metadata.bones.reduce((sum, b) => sum + b.num_points, 0);
    addStat(statsContent, 'Total Points', totalPoints.toLocaleString());

    // Bones details
    metadata.bones.forEach(bone => {
        addStat(statsContent, bone.name.replace(/_/g, ' '), `${bone.num_points.toLocaleString()} pts`);
    });
}

function addStat(container, label, value) {
    const item = document.createElement('div');
    item.className = 'stat-item';

    const labelSpan = document.createElement('span');
    labelSpan.className = 'stat-label';
    labelSpan.textContent = label;

    const valueSpan = document.createElement('span');
    valueSpan.className = 'stat-value';
    valueSpan.textContent = value;

    item.appendChild(labelSpan);
    item.appendChild(valueSpan);
    container.appendChild(item);
}

// ============================================================================
// Transform Controls
// ============================================================================

function setupTransformControls() {
    const modeBtns = document.querySelectorAll('.mode-btn');
    const resetBtn = document.getElementById('reset-transform');

    modeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            modeBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const mode = btn.dataset.mode;
            viewer.setTransformMode(mode);
        });
    });

    resetBtn.addEventListener('click', () => {
        if (viewer.selectedObject) {
            const name = viewer.selectedObject.userData.name;
            if (viewer.selectedObject.userData.type === 'bone') {
                boneManager.resetBoneTransform(name);
            } else if (viewer.selectedObject.userData.type === 'implant') {
                implantManager.resetImplantTransform(name);
            }
        }
    });
}

// ============================================================================
// Object Selection Handlers
// ============================================================================

function setupObjectSelectionHandlers() {
    const selectedInfo = document.getElementById('selected-bone-info');
    const resetBtn = document.getElementById('reset-transform');

    window.addEventListener('objectSelected', (e) => {
        const obj = e.detail.object;
        const type = obj.userData.type;
        const name = obj.userData.name;

        selectedInfo.innerHTML = `
            <strong>${type === 'bone' ? '🦴' : '🔧'} ${name.replace(/_/g, ' ')}</strong>
            <p style="font-size: 0.85rem; color: var(--text-muted); margin-top: 0.5rem;">
                Selected ${type}
            </p>
        `;

        resetBtn.disabled = false;

        // Highlight in bone list
        document.querySelectorAll('.bone-item').forEach(item => {
            item.classList.remove('selected');
            if (item.dataset.boneName === name) {
                item.classList.add('selected');
            }
        });
    });

    window.addEventListener('objectDeselected', () => {
        selectedInfo.innerHTML = '<p class="empty-state">Select a bone to transform</p>';
        resetBtn.disabled = true;

        document.querySelectorAll('.bone-item').forEach(item => {
            item.classList.remove('selected');
        });
    });
}

// ============================================================================
// Camera Controls
// ============================================================================

function setupCameraControls() {
    const presetBtns = document.querySelectorAll('.preset-btn');
    const resetBtn = document.getElementById('reset-camera');

    presetBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const view = btn.dataset.view;
            viewer.setCameraView(view);
        });
    });

    resetBtn.addEventListener('click', () => {
        viewer.resetCamera();
    });
}

// ============================================================================
// Viewer Controls
// ============================================================================

function setupViewerControls() {
    document.getElementById('toggle-grid').addEventListener('click', () => {
        viewer.toggleGrid();
    });

    document.getElementById('toggle-axes').addEventListener('click', () => {
        viewer.toggleAxes();
    });

    document.getElementById('screenshot').addEventListener('click', () => {
        viewer.takeScreenshot();
    });
}

// ============================================================================
// Implant Handlers
// ============================================================================

function setupImplantHandlers() {
    const implantZone = document.getElementById('implant-upload-zone');
    const implantInput = document.getElementById('implant-input');
    const implantList = document.getElementById('implant-list');

    implantZone.addEventListener('click', () => implantInput.click());

    implantInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (file) {
            try {
                implantList.innerHTML = '<p class="empty-state">Uploading...</p>';
                const result = await implantManager.uploadImplant(file);
                updateImplantList();
            } catch (error) {
                console.error('Implant upload error:', error);
                alert('Failed to upload implant: ' + error.message);
            }
        }
    });
}

function updateImplantList() {
    const implantList = document.getElementById('implant-list');
    implantList.innerHTML = '';

    if (implantManager.implants.length === 0) {
        implantList.innerHTML = '<p class="empty-state">No implants loaded</p>';
        return;
    }

    implantManager.implants.forEach(implant => {
        const item = document.createElement('div');
        item.className = 'implant-item';

        const name = document.createElement('span');
        name.textContent = implant.filename;

        const removeBtn = document.createElement('button');
        removeBtn.textContent = '×';
        removeBtn.style.border = 'none';
        removeBtn.style.background = 'none';
        removeBtn.style.color = 'var(--danger)';
        removeBtn.style.cursor = 'pointer';
        removeBtn.style.fontSize = '1.5rem';
        removeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            implantManager.removeImplant(implant.filename);
            updateImplantList();
        });

        item.appendChild(name);
        item.appendChild(removeBtn);

        item.addEventListener('click', () => {
            implantManager.selectImplant(implant.filename);
        });

        implantList.appendChild(item);
    });
}
