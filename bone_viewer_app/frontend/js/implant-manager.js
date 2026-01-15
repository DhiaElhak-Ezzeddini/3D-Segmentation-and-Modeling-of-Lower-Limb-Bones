/**
 * implant-manager.js - Implant Loading and Management
 */

class ImplantManager {
    constructor(viewer, apiUrl = 'http://localhost:8001') {
        this.viewer = viewer;
        this.apiUrl = apiUrl;
        this.implants = [];
        this.loadedImplants = {};

        this.plyLoader = new THREE.PLYLoader();
        this.stlLoader = new THREE.STLLoader();
        this.objLoader = new THREE.OBJLoader();
    }

    async uploadImplant(file) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(`${this.apiUrl}/upload-implant`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) throw new Error('Failed to upload implant');

            const result = await response.json();
            console.log('Implant uploaded:', result);

            // Load the implant into scene
            await this.loadImplant(result.filename);

            return result;
        } catch (error) {
            console.error('Error uploading implant:', error);
            throw error;
        }
    }

    async loadImplant(filename) {
        const url = `${this.apiUrl}/implants/${filename}`;
        const ext = filename.split('.').pop().toLowerCase();

        return new Promise((resolve, reject) => {
            const onLoad = (geometry) => {
                if (!geometry.isGeometry && !geometry.isBufferGeometry) {
                    // OBJ loader returns a group
                    geometry.traverse((child) => {
                        if (child.isMesh) {
                            this.createImplantMesh(child.geometry, filename);
                        }
                    });
                    resolve();
                } else {
                    const mesh = this.createImplantMesh(geometry, filename);
                    resolve(mesh);
                }
            };

            const onProgress = (xhr) => {
                console.log(`${filename}: ${(xhr.loaded / xhr.total * 100)}%`);
            };

            const onError = (error) => {
                console.error(`Error loading ${filename}:`, error);
                reject(error);
            };

            // Load based on file extension
            switch (ext) {
                case 'ply':
                    this.plyLoader.load(url, onLoad, onProgress, onError);
                    break;
                case 'stl':
                    this.stlLoader.load(url, onLoad, onProgress, onError);
                    break;
                case 'obj':
                    this.objLoader.load(url, onLoad, onProgress, onError);
                    break;
                default:
                    reject(new Error(`Unsupported file format: ${ext}`));
            }
        });
    }

    createImplantMesh(geometry, filename) {
        geometry.computeVertexNormals();

        // Create material (metallic appearance for implants)
        const material = new THREE.MeshStandardMaterial({
            color: 0x888888,
            metalness: 0.8,
            roughness: 0.2
        });

        const mesh = new THREE.Mesh(geometry, material);
        mesh.name = filename;

        // Rotation correction (same as bones)
        mesh.rotation.x = -Math.PI / 2;  // Flip to correct orientation

        mesh.userData = {
            type: 'implant',
            name: filename,
            originalPosition: mesh.position.clone(),
            originalRotation: mesh.rotation.clone(),
            originalScale: mesh.scale.clone()
        };

        // Add to scene
        this.viewer.addObject(mesh, mesh.userData);
        this.loadedImplants[filename] = mesh;
        this.implants.push({ filename });

        console.log(`Loaded implant: ${filename}`);
        return mesh;
    }

    getImplant(filename) {
        return this.loadedImplants[filename];
    }

    removeImplant(filename) {
        const implant = this.loadedImplants[filename];
        if (implant) {
            this.viewer.removeObject(implant);
            delete this.loadedImplants[filename];
            this.implants = this.implants.filter(i => i.filename !== filename);
        }
    }

    selectImplant(filename) {
        const implant = this.loadedImplants[filename];
        if (implant) {
            this.viewer.selectObject(implant);
        }
    }

    resetImplantTransform(filename) {
        const implant = this.loadedImplants[filename];
        if (implant && implant.userData.originalPosition) {
            implant.position.copy(implant.userData.originalPosition);
            implant.rotation.copy(implant.userData.originalRotation);
            implant.scale.copy(implant.userData.originalScale);
        }
    }

    clearAllImplants() {
        for (const implant of Object.values(this.loadedImplants)) {
            this.viewer.removeObject(implant);
        }
        this.loadedImplants = {};
        this.implants = [];
    }
}
