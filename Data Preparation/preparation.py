import nrrd # type: ignore
import numpy as np
import os

def extract_segments(nrrd_file, output_folder="segmentations_extracted_new"):
    """
    Extracts the different segmentations from an NRRD file and saves them separately.
    
    Args:
        nrrd_file: Path to the NRRD file
        output_folder: Folder where to save the extracted segmentations
    """
    
    # Create the output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Read the NRRD file
    print(f"Reading file: {nrrd_file}")
    data, header = nrrd.read(nrrd_file)
    
    print(f"Data dimensions: {data.shape}")
    print(f"Data type: {data.dtype}")
    
    # Extract segment information from the header
    segments_info = {}
    segment_idx = 0
    
    while f'Segment{segment_idx}_Name' in header:
        segment_info = {
            'name': header.get(f'Segment{segment_idx}_Name', f'Segment_{segment_idx}'),
            'label_value': int(header.get(f'Segment{segment_idx}_LabelValue', segment_idx + 1)),
            'color': header.get(f'Segment{segment_idx}_Color', 'N/A'),
            'id': header.get(f'Segment{segment_idx}_ID', f'Segment_{segment_idx}'),
            'extent': header.get(f'Segment{segment_idx}_Extent', 'N/A')
        }
        segments_info[segment_idx] = segment_info
        segment_idx += 1
    
    print(f"\n{len(segments_info)} segments found:")
    print("-" * 60)
    
    # Display segment information
    for idx, info in segments_info.items():
        print(f"Segment {idx}: {info['name']}")
        print(f"  Label value: {info['label_value']}")
        print(f"  RGB Color: {info['color']}")
        print(f"  ID: {info['id']}")
        print(f"  Extent: {info['extent']}")
        print()
    
    # Extract and save each segmentation
    print("\nExtracting individual segmentations...")
    print("-" * 60)
    
    for idx, info in segments_info.items():
        label_value = info['label_value']
        segment_name = info['name']
        
        # Create a binary mask for this segment
        segment_mask = (data == label_value).astype(np.uint8)
        
        # Count the number of voxels
        num_voxels = np.sum(segment_mask)
        
        print(f"Segment: {segment_name} (Label {label_value})")
        print(f"  Voxels: {num_voxels}")
        
        if num_voxels > 0:
            # Create a new header for this segment
            segment_header = header.copy()
            
            # Clean the header from other segments' information
            keys_to_remove = [k for k in segment_header.keys() if k.startswith('Segment')]
            for key in keys_to_remove:
                del segment_header[key]
            
            # Save the segment
            file_name = f"{segment_name}_label{label_value}.nrrd"
            output_path = os.path.join(output_folder, file_name)
            
            nrrd.write(output_path, segment_mask, segment_header)
            print(f"  Saved: {output_path}")
        else:
            print(f"  WARNING: No voxels found for this segment!")
        
        print()
    
    # Also create a summary file
    with open(os.path.join(output_folder, "segments_info.txt"), 'w', encoding='utf-8') as f:
        f.write("SEGMENTATION SUMMARY\n")
        f.write("=" * 60 + "\n\n")
        
        for idx, info in segments_info.items():
            label_value = info['label_value']
            segment_mask = (data == label_value)
            num_voxels = np.sum(segment_mask)
            
            f.write(f"Segment {idx}: {info['name']}\n")
            f.write(f"  Label value: {label_value}\n")
            f.write(f"  RGB Color: {info['color']}\n")
            f.write(f"  ID: {info['id']}\n")
            f.write(f"  Number of voxels: {num_voxels}\n")
            f.write(f"  File: {info['name']}_label{label_value}.nrrd\n")
            f.write("\n")
    
    print(f"Summary saved: {os.path.join(output_folder, 'segments_info.txt')}")
    print("\nExtraction finished!")
    
    return segments_info, data, header


def scan_dataset(dataset_root: str):
    """Scans the entire dataset to extract segmentations.

    Searches for folders whose name starts with 'SMIR.' and, in each,
    files whose name contains 'Segmentation' and ends with '.seg.nrrd'.
    For each SMIR folder, creates an output folder named
    '<SMIRName>_Extracted_Segs' (at the same level) and stores the extracts there.

    Args:
        dataset_root: Path to the root folder (e.g., 'D:/.../CV Dataset').
    """
    if not os.path.isdir(dataset_root):
        print(f"Error: root folder not found: {dataset_root}")
        return

    print(f"\n--- STARTING DATASET SCAN ---\nRoot: {dataset_root}\n")
    total_smirs = 0
    total_seg_files = 0
    total_success = 0
    errors = []

    for dirpath, dirnames, filenames in os.walk(dataset_root):
        folder_name = os.path.basename(dirpath)
        if not folder_name.startswith("SMIR."):
            continue
        total_smirs += 1

        # Target files in this folder
        seg_files = [f for f in filenames if "Segmentation" in f and f.endswith(".seg.nrrd")]
        if not seg_files:
            continue

        print("=" * 80)
        print(f"SMIR Folder: {dirpath}")
        print(f"Segmentation files found: {len(seg_files)}")

        # Create output folder for this SMIR folder
        output_folder_base = os.path.join(os.path.dirname(dirpath), f"{folder_name}_Extracted_Segs")
        os.makedirs(output_folder_base, exist_ok=True)

        for seg_file in seg_files:
            total_seg_files += 1
            seg_path = os.path.join(dirpath, seg_file)
            print(f"\nProcessing file: {seg_path}")
            # Subfolder per file (if multiple) to avoid collisions
            name_without_ext = os.path.splitext(os.path.splitext(seg_file)[0])[0]
            output_folder = os.path.join(output_folder_base, name_without_ext)
            os.makedirs(output_folder, exist_ok=True)
            try:
                segments_info, data, header = extract_segments(seg_path, output_folder)
                unique_labels = np.unique(data)
                print(f"Unique labels: {unique_labels}")
                for label in unique_labels:
                    count = int(np.sum(data == label))
                    percentage = (count / data.size) * 100 if data.size else 0
                    print(f"  Label {label}: {count} voxels ({percentage:.2f}%)")
                total_success += 1
            except Exception as e:
                err_msg = f"ERROR extracting '{seg_path}': {e}"
                print(err_msg)
                errors.append(err_msg)

    print("\n--- OVERALL SUMMARY ---")
    print(f"SMIR folders visited: {total_smirs}")
    print(f"Segmentation files detected: {total_seg_files}")
    print(f"Successful extractions: {total_success}")
    if errors:
        print(f"Errors: {len(errors)}")
        for e in errors:
            print(f"  - {e}")
    else:
        print("No errors encountered.")
    print("--- SCAN FINISHED ---\n")


if __name__ == "__main__":
    # Root path of the dataset to scan
    dataset_root = r"D:\3D-Segmentation-and-Modeling-of-Lower-Limb-Bones\CV Dataset"
    scan_dataset(dataset_root)