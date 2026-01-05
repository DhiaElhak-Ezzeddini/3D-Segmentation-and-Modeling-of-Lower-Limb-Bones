/**
 * viewer.js - Three.js 3D Viewer Setup
 */

class Viewer3D {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.orbitControls = null;
        this.transformControls = null;
        this.raycaster = new THREE.Raycaster();
        this.mouse = new THREE.Vector2();

        this.gridHelper = null;
        this.axesHelper = null;

        this.selectedObject = null;
        this.transformMode = 'translate';

        this.init();
    }

    init() {
        // Scene
        this.scene = new THREE.Scene();
        // Background controlled by CSS via alpha: true

        // Camera
        const aspect = this.canvas.clientWidth / this.canvas.clientHeight;
        this.camera = new THREE.PerspectiveCamera(60, aspect, 1, 5000);
        this.camera.position.set(300, 300, 500);

        // Renderer
        this.renderer = new THREE.WebGLRenderer({
            canvas: this.canvas,
            antialias: true,
            alpha: true
        });
        this.renderer.setSize(this.canvas.clientWidth, this.canvas.clientHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);

        // Lights
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        this.scene.add(ambientLight);

        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(200, 300, 200);
        this.scene.add(directionalLight);

        const directionalLight2 = new THREE.DirectionalLight(0xffffff, 0.4);
        directionalLight2.position.set(-200, -300, -200);
        this.scene.add(directionalLight2);

        // Grid Helper
        this.gridHelper = new THREE.GridHelper(1000, 50, 0x888888, 0xcccccc);
        this.scene.add(this.gridHelper);

        // Axes Helper
        this.axesHelper = new THREE.AxesHelper(200);
        this.scene.add(this.axesHelper);

        // Orbit Controls
        this.orbitControls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.orbitControls.enableDamping = true;
        this.orbitControls.dampingFactor = 0.05;
        this.orbitControls.minDistance = 50;
        this.orbitControls.maxDistance = 2000;

        // Transform Controls
        this.transformControls = new THREE.TransformControls(this.camera, this.renderer.domElement);
        this.transformControls.addEventListener('dragging-changed', (event) => {
            this.orbitControls.enabled = !event.value;
        });
        this.scene.add(this.transformControls);

        // Event Listeners
        window.addEventListener('resize', () => this.onWindowResize());
        this.canvas.addEventListener('click', (e) => this.onClick(e));
        window.addEventListener('keydown', (e) => this.onKeyDown(e));

        // Start animation loop
        this.animate();
    }

    animate() {
        requestAnimationFrame(() => this.animate());
        this.orbitControls.update();
        this.renderer.render(this.scene, this.camera);
    }

    onWindowResize() {
        this.camera.aspect = this.canvas.clientWidth / this.canvas.clientHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(this.canvas.clientWidth, this.canvas.clientHeight);
    }

    onClick(event) {
        const rect = this.canvas.getBoundingClientRect();
        this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

        this.raycaster.setFromCamera(this.mouse, this.camera);

        // Find intersected objects (bones and implants)
        const intersectables = this.scene.children.filter(obj =>
            obj.userData.type === 'bone' || obj.userData.type === 'implant'
        );

        const intersects = this.raycaster.intersectObjects(intersectables, true);

        if (intersects.length > 0) {
            const selectedObj = intersects[0].object;
            this.selectObject(selectedObj);
        }
    }

    selectObject(object) {
        // Find the top-level parent (bone or implant group)
        let target = object;
        while (target.parent && target.parent !== this.scene) {
            target = target.parent;
        }

        if (this.selectedObject === target) return;

        // Deselect previous
        if (this.selectedObject) {
            this.transformControls.detach();
        }

        // Select new
        this.selectedObject = target;
        this.transformControls.attach(target);
        this.transformControls.setMode(this.transformMode);

        // Dispatch selection event
        const event = new CustomEvent('objectSelected', {
            detail: { object: target }
        });
        window.dispatchEvent(event);
    }

    deselectObject() {
        if (this.selectedObject) {
            this.transformControls.detach();
            this.selectedObject = null;

            const event = new CustomEvent('objectDeselected');
            window.dispatchEvent(event);
        }
    }

    setTransformMode(mode) {
        this.transformMode = mode;
        if (this.selectedObject) {
            this.transformControls.setMode(mode);
        }
    }

    onKeyDown(event) {
        switch (event.key.toLowerCase()) {
            case 'g':
                this.setTransformMode('translate');
                break;
            case 'r':
                this.setTransformMode('rotate');
                break;
            case 's':
                this.setTransformMode('scale');
                break;
            case 'escape':
                this.deselectObject();
                break;
        }
    }

    setCameraView(view) {
        const distance = 600;
        const positions = {
            'top': { x: 0, y: distance, z: 0 },
            'bottom': { x: 0, y: -distance, z: 0 },
            'left': { x: -distance, y: 0, z: 0 },
            'right': { x: distance, y: 0, z: 0 },
            'front': { x: 0, y: 0, z: distance },
            'back': { x: 0, y: 0, z: -distance }
        };

        if (positions[view]) {
            this.camera.position.set(positions[view].x, positions[view].y, positions[view].z);
            this.camera.lookAt(0, 0, 0);
            this.orbitControls.target.set(0, 0, 0);
            this.orbitControls.update();
        }
    }

    resetCamera() {
        // Calculate bounding box of all objects
        const box = new THREE.Box3();
        this.scene.children.forEach(obj => {
            if (obj.userData.type === 'bone' || obj.userData.type === 'implant') {
                box.expandByObject(obj);
            }
        });

        if (!box.isEmpty()) {
            const center = box.getCenter(new THREE.Vector3());
            const size = box.getSize(new THREE.Vector3());
            const maxDim = Math.max(size.x, size.y, size.z);

            this.orbitControls.target.copy(center);
            this.camera.position.set(
                center.x + maxDim,
                center.y + maxDim,
                center.z + maxDim
            );
            this.orbitControls.update();
        } else {
            // Default position
            this.camera.position.set(300, 300, 500);
            this.orbitControls.target.set(0, 0, 0);
            this.orbitControls.update();
        }
    }

    toggleGrid() {
        this.gridHelper.visible = !this.gridHelper.visible;
    }

    toggleAxes() {
        this.axesHelper.visible = !this.axesHelper.visible;
    }

    takeScreenshot() {
        this.renderer.render(this.scene, this.camera);
        this.canvas.toBlob((blob) => {
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `bone-viewer-${Date.now()}.png`;
            a.click();
            URL.revokeObjectURL(url);
        });
    }

    addObject(object, userData = {}) {
        object.userData = { ...object.userData, ...userData };
        this.scene.add(object);
    }

    removeObject(object) {
        if (this.selectedObject === object) {
            this.deselectObject();
        }
        this.scene.remove(object);
    }

    clearAll() {
        const objectsToRemove = this.scene.children.filter(obj =>
            obj.userData.type === 'bone' || obj.userData.type === 'implant'
        );
        objectsToRemove.forEach(obj => this.scene.remove(obj));
    }
}
