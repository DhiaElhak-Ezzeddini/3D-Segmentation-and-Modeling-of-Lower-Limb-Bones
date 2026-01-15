import numpy as np
import nibabel as nib
from pathlib import Path
import json
import logging
from typing import Dict, Any
from ..domain.interfaces import IBoneProcessor

logger = logging.getLogger(__name__)

# Dataset labels
LABELS = {
    0: "background",
    1: "Femur_L",
    2: "Femur_R",
    3: "Hip_L",
    4: "Hip_R",
    5: "Patella_L",
    6: "Patella_R",
    7: "Sacrum",
    8: "Threshold-200-MAX"
}

# Bone colors (RGB 0-255)
BONE_COLORS = {
    'Femur_L': (255, 100, 100),      # Red
    'Femur_R': (100, 200, 255),      # Light Blue
    'Hip_L': (255, 150, 50),         # Orange
    'Hip_R': (150, 100, 255),        # Purple
    'Patella_L': (100, 255, 150),    # Mint Green
    'Patella_R': (255, 200, 100),    # Yellow-Orange
    'Sacrum': (200, 100, 200),       # Pink-Purple
    'Threshold-200-MAX': (150, 150, 150)  # Gray
}

class NiftiBoneProcessor(IBoneProcessor):
    def extract_bone_voxels(self, segmentation_data, label_id, spacing):
        """Extract voxels for a specific bone and convert to world coordinates"""
        bone_mask = (segmentation_data == label_id)
        voxel_coords = np.argwhere(bone_mask)
        world_coords = voxel_coords * spacing
        return voxel_coords, world_coords

    def write_ply_file(self, vertices, output_path, colors=None):
        """Write PLY file with optional vertex colors"""
        num_vertices = len(vertices)
        
        header = f"ply\nformat ascii 1.0\ncomment Created from bone segmentation\nelement vertex {num_vertices}\nproperty float x\nproperty float y\nproperty float z\n"
        
        if colors is not None:
            header += "property uchar red\nproperty uchar green\nproperty uchar blue\n"
        
        header += "end_header\n"
        
        with open(output_path, 'w') as f:
            f.write(header)
            for i in range(num_vertices):
                line = f"{vertices[i, 0]:.6f} {vertices[i, 1]:.6f} {vertices[i, 2]:.6f}"
                if colors is not None:
                    line += f" {int(colors[i, 0])} {int(colors[i, 1])} {int(colors[i, 2])}"
                line += "\n"
                f.write(line)
        
        logger.info(f"Wrote PLY file: {output_path} ({num_vertices:,} vertices)")

    def process_segmentation(self, nifti_path: str, output_dir: str, downsample_factor: int = 2) -> Dict[str, Any]:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Loading segmentation: {nifti_path}")
        nii = nib.load(nifti_path)
        seg_data = nii.get_fdata()
        spacing = nii.header.get_zooms()
        
        logger.info(f"Segmentation shape: {seg_data.shape}")
        
        bones_metadata = []
        
        # Process each bone label
        for label_id, bone_name in LABELS.items():
            if bone_name == "background":
                continue
            
            voxel_coords, world_coords = self.extract_bone_voxels(seg_data, label_id, spacing)
            
            if len(voxel_coords) > 0:
                # Downsample for performance
                if downsample_factor > 1 and len(world_coords) > 1000:
                    indices = np.arange(0, len(world_coords), downsample_factor)
                    world_coords_downsampled = world_coords[indices]
                else:
                    world_coords_downsampled = world_coords
                
                # Get bone color
                color = BONE_COLORS.get(bone_name, (150, 150, 150))
                colors = np.tile(color, (len(world_coords_downsampled), 1))
                
                # Write PLY file
                ply_file = output_path / f"{bone_name}.ply"
                self.write_ply_file(world_coords_downsampled, ply_file, colors)
                
                # Calculate bounding box
                bbox_min = [float(x) for x in world_coords.min(axis=0)]
                bbox_max = [float(x) for x in world_coords.max(axis=0)]
                center = [(bbox_min[i] + bbox_max[i]) / 2 for i in range(3)]
                
                # Store metadata
                bones_metadata.append({
                    'name': bone_name,
                    'label_id': int(label_id),
                    'filename': ply_file.name,
                    'num_voxels': int(len(voxel_coords)),
                    'num_points': int(len(world_coords_downsampled)),
                    'color': list(color),
                    'bounding_box': {
                        'min': bbox_min,
                        'max': bbox_max,
                        'center': center
                    }
                })
                
                logger.info(f"✓ {bone_name}: {len(voxel_coords):,} voxels → {len(world_coords_downsampled):,} points")
        
        # Save metadata
        metadata = {
            'segmentation_shape': [int(x) for x in seg_data.shape],
            'spacing': [float(x) for x in spacing],
            'bones': bones_metadata,
            'total_bones': len(bones_metadata)
        }
        
        metadata_file = output_path / 'metadata.json'
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return metadata
