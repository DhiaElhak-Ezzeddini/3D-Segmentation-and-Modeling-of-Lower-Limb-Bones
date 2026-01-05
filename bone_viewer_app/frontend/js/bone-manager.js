/**
 * bone-manager.js - Bone Loading and Management
 */

class BoneManager {
    constructor(viewer, apiUrl = 'http://localhost:8000') {
        this.viewer = viewer;
        this.apiUrl = apiUrl;
        this.bones = [];
        this.loadedBones = {};
        this.plyLoader = new THREE.PLYLoader();
    }

    async loadBonesFromJob(jobId) {
        try {
            // Fetch metadata
            const response = await fetch(`${this.apiUrl}/bones/${jobId}`);
            if (!response.ok) throw new Error('Failed to fetch bones metadata');

            const metadata = await response.json();
            this.bones = metadata.bones;

            // Load each bone PLY file
            for (const bone of this.bones) {
                await this.loadBone(jobId, bone);
            }

            // Center camera on all bones
            this.viewer.resetCamera();

            return metadata;
        } catch (error) {
            console.error('Error loading bones:', error);
            throw error;
        }
    }

    async loadBone(jobId, boneData) {
        return new Promise((resolve, reject) => {
            const url = `${this.apiUrl}/ply/${jobId}/${boneData.filename}`;

            this.plyLoader.load(
                url,
                (geometry) => {
                    geometry.computeVertexNormals();

                    // Create points material with larger vertex size for better visibility
                    const material = new THREE.PointsMaterial({
                        size: 4,  // Increased from 2 to 4 for better visibility
                        vertexColors: true,
                        sizeAttenuation: true  // Points get smaller with distance
                    });

                    // Create points object
                    const points = new THREE.Points(geometry, material);
                    points.name = boneData.name;

                    // Rotate to correct orientation (medical images often need 90° rotation)
                    // Adjust these rotations based on your data orientation
                    points.rotation.x = -Math.PI / 2;  // -90 degrees to flip upside down

                    points.userData = {
                        type: 'bone',
                        name: boneData.name,
                        labelId: boneData.label_id,
                        color: boneData.color,
                        originalPosition: points.position.clone(),
                        originalRotation: points.rotation.clone(),
                        originalScale: points.scale.clone()
                    };

                    // Add to scene
                    this.viewer.addObject(points, points.userData);
                    this.loadedBones[boneData.name] = points;

                    console.log(`Loaded bone: ${boneData.name} (${boneData.num_points} points)`);
                    resolve(points);
                },
                (xhr) => {
                    console.log(`${boneData.name}: ${(xhr.loaded / xhr.total * 100)}%`);
                },
                (error) => {
                    console.error(`Error loading ${boneData.name}:`, error);
                    reject(error);
                }
            );
        });
    }

    getBone(boneName) {
        return this.loadedBones[boneName];
    }

    toggleBoneVisibility(boneName, visible) {
        const bone = this.loadedBones[boneName];
        if (bone) {
            bone.visible = visible;
        }
    }

    selectBone(boneName) {
        const bone = this.loadedBones[boneName];
        if (bone) {
            this.viewer.selectObject(bone);
        }
    }

    resetBoneTransform(boneName) {
        const bone = this.loadedBones[boneName];
        if (bone && bone.userData.originalPosition) {
            bone.position.copy(bone.userData.originalPosition);
            bone.rotation.copy(bone.userData.originalRotation);
            bone.scale.copy(bone.userData.originalScale);
        }
    }

    getBoneTransform(boneName) {
        const bone = this.loadedBones[boneName];
        if (!bone) return null;

        return {
            position: bone.position.toArray(),
            rotation: [bone.rotation.x, bone.rotation.y, bone.rotation.z],
            scale: bone.scale.toArray()
        };
    }

    exportSceneState() {
        const state = {
            bones: {},
            timestamp: new Date().toISOString()
        };

        for (const [name, bone] of Object.entries(this.loadedBones)) {
            state.bones[name] = this.getBoneTransform(name);
        }

        return state;
    }

    clearAllBones() {
        for (const bone of Object.values(this.loadedBones)) {
            this.viewer.removeObject(bone);
        }
        this.loadedBones = {};
        this.bones = [];
    }
}
