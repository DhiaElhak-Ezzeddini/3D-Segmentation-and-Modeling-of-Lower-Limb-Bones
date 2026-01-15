/**
 * bone-manager-mesh.js - Version avec rendu mesh au lieu de points
 * Alternative à bone-manager.js pour un rendu plus solide des os
 */

class BoneManagerMesh {
    constructor(viewer, apiUrl = 'http://localhost:8001') {
        this.viewer = viewer;
        this.apiUrl = apiUrl;
        this.bones = [];
        this.loadedBones = {};
        this.plyLoader = new THREE.PLYLoader();
    }

    async loadBonesFromJob(jobId) {
        try {
            const response = await fetch(`${this.apiUrl}/bones/${jobId}`);
            if (!response.ok) throw new Error('Failed to fetch bones metadata');

            const metadata = await response.json();
            this.bones = metadata.bones;

            // Load all bones
            for (const bone of this.bones) {
                await this.loadBone(jobId, bone);
            }

            // Center all bones as a group (preserving relative positions)
            this.centerBonesGroup();

            this.viewer.resetCamera();

            return metadata;
        } catch (error) {
            console.error('Error loading bones:', error);
            throw error;
        }
    }

    centerBonesGroup() {
        // Calculate bounding box of all bones together
        const allBones = Object.values(this.loadedBones);
        if (allBones.length === 0) return;

        const box = new THREE.Box3();
        allBones.forEach(bone => {
            box.expandByObject(bone);
        });

        const center = new THREE.Vector3();
        box.getCenter(center);

        // Offset all bones by the negative center
        allBones.forEach(bone => {
            bone.position.sub(center);
        });

        console.log(`Centered ${allBones.length} bones at origin. Offset: ${center.x.toFixed(2)}, ${center.y.toFixed(2)}, ${center.z.toFixed(2)}`);
    }

    async loadBone(jobId, boneData) {
        return new Promise((resolve, reject) => {
            const url = `${this.apiUrl}/ply/${jobId}/${boneData.filename}`;

            this.plyLoader.load(
                url,
                (geometry) => {
                    geometry.computeVertexNormals();

                    // Convert color from RGB (0-255) to THREE.js range (0-1)
                    const color = new THREE.Color(
                        boneData.color[0] / 255,
                        boneData.color[1] / 255,
                        boneData.color[2] / 255
                    );

                    // Material with realistic bone appearance
                    const material = new THREE.MeshStandardMaterial({
                        color: color,
                        roughness: 0.4,  // Réduit pour surface plus lisse
                        metalness: 0.05,
                        side: THREE.DoubleSide,
                        flatShading: false
                    });

                    // Créer un mesh à partir des vertices
                    // Si le PLY n'a pas de faces, on crée des petites sphères pour chaque vertex
                    let mesh;

                    if (geometry.index && geometry.index.count > 0) {
                        // Le PLY a des faces, on peut créer un mesh normal
                        mesh = new THREE.Mesh(geometry, material);
                        console.log(`${boneData.name}: Mesh with ${geometry.index.count / 3} faces`);
                    } else {
                        // Pas de faces, créer un point cloud avec des sphères instanciées
                        console.log(`${boneData.name}: Point cloud, creating instanced mesh...`);

                        const positions = geometry.attributes.position;
                        const instanceCount = Math.min(positions.count, 30000); // Réduit pour performance

                        // Sphère plus détaillée pour smoothness
                        const sphereGeometry = new THREE.SphereGeometry(2.0, 10, 10); // 10x10 pour meilleur smooth
                        const instancedMesh = new THREE.InstancedMesh(
                            sphereGeometry,
                            material,
                            instanceCount
                        );

                        // Positionner chaque instance
                        const matrix = new THREE.Matrix4();
                        const step = Math.floor(positions.count / instanceCount);

                        for (let i = 0; i < instanceCount; i++) {
                            const idx = i * step;
                            const x = positions.getX(idx);
                            const y = positions.getY(idx);
                            const z = positions.getZ(idx);

                            matrix.setPosition(x, y, z);
                            instancedMesh.setMatrixAt(i, matrix);
                        }

                        instancedMesh.instanceMatrix.needsUpdate = true;
                        mesh = instancedMesh;
                    }

                    mesh.name = boneData.name;

                    // Rotation correction (medical data orientation)
                    mesh.rotation.x = -Math.PI / 2;  // Flip to correct orientation

                    mesh.userData = {
                        type: 'bone',
                        name: boneData.name,
                        labelId: boneData.label_id,
                        color: boneData.color,
                        originalPosition: mesh.position.clone(),
                        originalRotation: mesh.rotation.clone(),
                        originalScale: mesh.scale.clone()
                    };

                    this.viewer.addObject(mesh, mesh.userData);
                    this.loadedBones[boneData.name] = mesh;

                    console.log(`Loaded bone: ${boneData.name}`);
                    resolve(mesh);
                },
                (xhr) => {
                    console.log(`${boneData.name}: ${(xhr.loaded / xhr.total * 100).toFixed(1)}%`);
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
