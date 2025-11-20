import os
import nrrd
import nibabel as nib
import numpy as np
import json
import re
from collections import OrderedDict

# Target labels to include (only these will be processed)
ALLOWED_LABELS = {
    'Femur_L',
    'Femur_R',
    'Hip_L',
    'Hip_R',
    'Patella_L',
    'Patella_R',
    'Sacrum',
    'Threshold-200-MAX'
}

def iter_subject_ids(cv_dataset_root):
    """
    Yields subject IDs (top-level directories) in 'CV Dataset'.
    """
    for name in os.listdir(cv_dataset_root):
        full = os.path.join(cv_dataset_root, name)
        if os.path.isdir(full):
            yield name

def find_transformed_folders_in_subject(subject_root):
    """
    Returns a list of paths to '*_Segs_Transformed' folders inside a subject root (recursive).
    """
    results = []
    for root, dirs, _ in os.walk(subject_root):
        for d in dirs:
            if d.endswith('_Segs_Transformed'):
                results.append(os.path.join(root, d))
    return results

def extract_label_name(filename):
    """
    Extract label name from filename like 'Femur_L_label3.nii.gz' -> 'Femur_L'
    Handles patterns: *_label.nii.gz or *_label[0-9]+.nii.gz
    """
    # Remove .nii.gz extension
    name = filename.replace('.nii.gz', '')
    # Split by _label and take the first part
    name = name.split('_label')[0]
    return name

def has_exact_labels(case_folder):
    """
    Check if case_folder contains EXACTLY the 8 allowed labels - no more, no less.
    Returns True only if all 8 labels are present and no other labels exist.
    """
    label_files = [f for f in os.listdir(case_folder) if f.endswith('.nii.gz')]
    found_labels = set(extract_label_name(f) for f in label_files)
    return found_labels == ALLOWED_LABELS

def find_case_folders(transformed_folder):
    """
    Returns a list of case folders under a transformed folder. Prefer subfolders ending with
    '_Segmentation'. If none exist, and .nii.gz files are directly in the transformed folder,
    treat the transformed folder itself as one case.
    """
    subdirs = [os.path.join(transformed_folder, d) for d in os.listdir(transformed_folder)
               if os.path.isdir(os.path.join(transformed_folder, d))]
    case_folders = [p for p in subdirs if os.path.basename(p).endswith('_Segmentation')]
    if case_folders:
        return case_folders
    # Fallback: if no subfolders, but nii.gz present directly, treat as a single case
    has_labels = any(f.endswith('.nii.gz') for f in os.listdir(transformed_folder))
    return [transformed_folder] if has_labels else []

def find_raw_ct_for_case(case_folder, subject_root):
    """
    For a case folder named like 'SMIR.*.Pelvis-Thighs_Segmentation', find the corresponding
    raw study folder. Returns path to raw .nrrd file if found.
    """
    case_name = os.path.basename(case_folder)
    base_name = case_name[:-13] if case_name.endswith('_Segmentation') else case_name
    candidates = [base_name]
    if '-' in base_name:
        candidates.append(base_name.split('-', 1)[0])

    raw_study_dir = None
    # Search only within this subject
    for cand in candidates:
        # Try direct child first
        direct = os.path.join(subject_root, cand)
        if os.path.isdir(direct):
            raw_study_dir = direct
            break
        # Otherwise search recursively for a directory with this name
        for root, dirs, _ in os.walk(subject_root):
            if cand in dirs:
                raw_study_dir = os.path.join(root, cand)
                break
        if raw_study_dir:
            break

    if not raw_study_dir:
        print(f"  -> ERROR: Could not find raw study directory for '{case_name}' in subject '{os.path.basename(subject_root)}'")
        return None

    # Find raw NRRD file (non-segmentation) directly inside the raw study directory
    nrrd_files = [f for f in os.listdir(raw_study_dir) if f.endswith('.nrrd') and '_Segmentation' not in f]
    if not nrrd_files:
        print(f"  -> ERROR: No raw .nrrd file found in {raw_study_dir}")
        return None
    return os.path.join(raw_study_dir, sorted(nrrd_files)[0])

def merge_labels_from_case(case_folder, name_to_id, reference_shape=None, reference_affine=None):
    """
    Merge all label .nii.gz files in case_folder using a GLOBAL name->id map.
    FILTERED: Only processes labels in ALLOWED_LABELS set.
    If reference_shape and reference_affine provided, resample to match reference geometry.
    Returns (nifti_img, used_label_names:set[str]).
    """
    label_files = [f for f in os.listdir(case_folder) if f.endswith('.nii.gz')]
    # Filter to only allowed labels
    label_files = [f for f in label_files if extract_label_name(f) in ALLOWED_LABELS]
    
    if not label_files:
        return None, set()
    
    first = nib.load(os.path.join(case_folder, label_files[0]))
    
    # Use reference shape if provided, otherwise use first label's shape
    if reference_shape is not None:
        target_shape = reference_shape
        target_affine = reference_affine if reference_affine is not None else first.affine
    else:
        target_shape = first.shape
        target_affine = first.affine
    
    merged_dtype = np.uint16 if len(name_to_id) > 255 else np.uint8
    merged = np.zeros(target_shape, dtype=merged_dtype)
    used_names = set()
    
    for fname in label_files:
        name = extract_label_name(fname)
        class_id = name_to_id.get(name)
        if class_id is None:
            continue
        
        label_img = nib.load(os.path.join(case_folder, fname))
        data = label_img.get_fdata()
        
        # Resample if shapes don't match
        if data.shape != target_shape:
            from scipy import ndimage
            zoom_factors = np.array(target_shape) / np.array(data.shape)
            data = ndimage.zoom(data, zoom_factors, order=0)  # nearest neighbor
            
            # Ensure exact match (handle rounding)
            if data.shape != target_shape:
                temp = np.zeros(target_shape, dtype=data.dtype)
                slices = tuple(slice(0, min(data.shape[i], target_shape[i])) for i in range(3))
                temp[slices] = data[slices]
                data = temp
        
        mask = data > 0
        if np.any(mask):
            merged[mask] = class_id
            used_names.add(name)
    
    if not used_names:
        return None, set()
    return nib.Nifti1Image(merged, target_affine, first.header), used_names

def nrrd_to_nifti(nrrd_path):
    data, header = nrrd.read(nrrd_path)
    affine = np.eye(4)
    try:
        sd = header.get('space directions')
        so = header.get('space origin')
        if sd is not None and so is not None:
            affine[:3, :3] = np.array(sd).T
            affine[:3, 3] = np.array(so)
    except Exception as e:
        print(f"    - WARNING: Failed to compute affine for {os.path.basename(nrrd_path)}: {e}")
    return nib.Nifti1Image(data.astype(np.float32), affine)

def collect_all_label_names(cv_root):
    """
    Scan all *_Segs_Transformed cases (filtered to Pelvis-Thighs only) across all subjects
    to collect unique LABEL NAMES that are in ALLOWED_LABELS.
    Returns a set of label name strings.
    """
    all_names = set()
    for subject_id in iter_subject_ids(cv_root):
        subject_root = os.path.join(cv_root, subject_id)
        transformed_folders = find_transformed_folders_in_subject(subject_root)
        for transformed in transformed_folders:
            case_folders = find_case_folders(transformed)
            for case_folder in case_folders:
                label_files = [f for f in os.listdir(case_folder) if f.endswith('.nii.gz')]
                for fname in label_files:
                    name = extract_label_name(fname)
                    if name in ALLOWED_LABELS:
                        all_names.add(name)
    return all_names

def build_name_to_id_map(label_names):
    """
    Assigns integer IDs 1..N to label names in sorted order for global consistency.
    """
    sorted_names = sorted(label_names)
    return {name: idx for idx, name in enumerate(sorted_names, start=1)}

def prepare_for_nnunet():
    print('Starting nnU-Net preparation (Pelvis-Thighs dataset with filtered labels)...')
    script_dir = os.path.dirname(__file__)
    project_root = os.path.abspath(os.path.join(script_dir, '..'))
    cv_root = os.path.join(project_root, 'CV Dataset')
    # Output to a different dataset folder
    task_dir = os.path.join(script_dir, 'nnUNet_raw_data_new', 'Dataset001_PelvisThighs')
    images_tr = os.path.join(task_dir, 'imagesTr')
    labels_tr = os.path.join(task_dir, 'labelsTr')
    os.makedirs(images_tr, exist_ok=True)
    os.makedirs(labels_tr, exist_ok=True)
    print(f"nnU-Net target: {task_dir}")

    # --- PRE-SCAN: collect all label NAMES to build a consistent global mapping ---
    print("\nCollecting label names across dataset for global, consistent IDs ...")
    print(f"Allowed labels: {ALLOWED_LABELS}")
    all_label_names = collect_all_label_names(cv_root)
    print(f"  - Found {len(all_label_names)} unique label names across dataset.")
    print(f"  - Names: {all_label_names}")
    if not all_label_names:
        print("WARNING: No labels discovered in the dataset. JSON will contain only background.")
    name_to_id = build_name_to_id_map(all_label_names)
    print(f"  - Built name->id map with {len(name_to_id)} entries.")
    print(f"  - Mapping: {name_to_id}")

    training = []
    case_idx = 1

    for subject_id in iter_subject_ids(cv_root):
        subject_root = os.path.join(cv_root, subject_id)
        transformed_folders = find_transformed_folders_in_subject(subject_root)
        if not transformed_folders:
            continue
        print(f"\nSubject {subject_id}: {len(transformed_folders)} transformed sets found")

        for transformed in transformed_folders:
            case_folders = find_case_folders(transformed)
            if not case_folders:
                continue
            for case_folder in case_folders:
                case_name = os.path.basename(case_folder)
                
                # Filter: only process Pelvis-Thighs cases with exactly 8 labels
                if 'Pelvis-Thighs' not in case_name:
                    continue
                if not has_exact_labels(case_folder):
                    continue
                    
                print(f"  - Case: {case_name}")
                
                # Find raw CT within this subject only
                raw_ct = find_raw_ct_for_case(case_folder, subject_root)
                if not raw_ct:
                    print("    * Missing raw CT, skipping this case")
                    continue

                # Convert raw CT to get reference shape and affine
                raw_ct_nifti = nrrd_to_nifti(raw_ct)
                reference_shape = raw_ct_nifti.shape
                reference_affine = raw_ct_nifti.affine
                
                # Merge labels for this case using global name->id map WITH spatial alignment
                merged_label_img, used_names = merge_labels_from_case(
                    case_folder, name_to_id, 
                    reference_shape=reference_shape, 
                    reference_affine=reference_affine
                )
                if merged_label_img is None:
                    print("    * Failed to merge labels, skipping")
                    continue

                # Save outputs
                case_id = f"PELVISTHIGHS_{case_idx:03d}"
                img_out = os.path.join(images_tr, f"{case_id}_0000.nii.gz")
                lbl_out = os.path.join(labels_tr, f"{case_id}.nii.gz")
                nib.save(raw_ct_nifti, img_out)
                nib.save(merged_label_img, lbl_out)
                training.append({"image": f"./imagesTr/{case_id}_0000.nii.gz", "label": f"./labelsTr/{case_id}.nii.gz"})
                print(f"    * Saved {case_id} with labels: {used_names}")
                case_idx += 1

    if not training:
        print("\nCRITICAL: No training cases created. Check folder structure and inputs.")
        return

    # Build dataset.json using the global name->id mapping (complete set)
    labels_json = {"background": 0}
    for name, cid in sorted(name_to_id.items(), key=lambda x: x[1]):
        labels_json[name] = cid

    ds = {
        "channel_names": {
            "0": "CT"
        },
        "labels": labels_json,
        "numTraining": len(training),
        "file_ending": ".nii.gz"
    }
    
    os.makedirs(task_dir, exist_ok=True)
    json_path = os.path.join(task_dir, 'dataset.json')
    with open(json_path, 'w') as f:
        json.dump(ds, f, indent=4)
    
    print(f"\nDone. Wrote {len(training)} cases and dataset.json to {task_dir}")
    print(f"Dataset has {len(labels_json)-1} classes (excluding background)")
    print(f"Allowed labels: {ALLOWED_LABELS}")
    print(f"\nReady for preprocessing! Run:")
    print(f"  nnUNetv2_plan_and_preprocess -d 2 -c 3d_fullres")

if __name__ == '__main__':
    prepare_for_nnunet()
