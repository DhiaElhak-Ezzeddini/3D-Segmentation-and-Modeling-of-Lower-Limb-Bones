"""
Run only nnU-Net preprocessing
Useful for verifying dataset before starting training
"""
import os
import sys
import subprocess
from pathlib import Path

def set_environment_variables():
    """Set nnU-Net environment variables"""
    base_path = Path(__file__).parent.absolute()
    
    os.environ['nnUNet_raw'] = str(base_path / 'nnUNet_raw_data')
    os.environ['nnUNet_preprocessed'] = str(base_path / 'nnUNet_preprocessed')
    os.environ['nnUNet_results'] = str(base_path / 'nnUNet_results')
    
    print("=" * 60)
    print("nnU-Net Preprocessing")
    print("=" * 60)
    print(f"nnUNet_raw: {os.environ['nnUNet_raw']}")
    print(f"nnUNet_preprocessed: {os.environ['nnUNet_preprocessed']}")

def verify_dataset():
    """Verify dataset exists and is valid"""
    try:
        from nnunetv2.paths import nnUNet_raw
        
        dataset_path = Path(nnUNet_raw) / "Dataset001_LowerLimb"
        if not dataset_path.exists():
            print(f"ERROR: Dataset not found at {dataset_path}")
            return False
        
        images_tr = dataset_path / "imagesTr"
        labels_tr = dataset_path / "labelsTr"
        dataset_json = dataset_path / "dataset.json"
        
        if not all([images_tr.exists(), labels_tr.exists(), dataset_json.exists()]):
            print("ERROR: Dataset structure incomplete!")
            print(f"  imagesTr exists: {images_tr.exists()}")
            print(f"  labelsTr exists: {labels_tr.exists()}")
            print(f"  dataset.json exists: {dataset_json.exists()}")
            return False
        
        num_images = len(list(images_tr.glob("*.nii.gz")))
        num_labels = len(list(labels_tr.glob("*.nii.gz")))
        
        print(f"\nDataset: {dataset_path}")
        print(f"  Images: {num_images}")
        print(f"  Labels: {num_labels}")
        
        if num_images == 0 or num_labels == 0:
            print("ERROR: No training data found!")
            return False
        
        return True
    except ImportError:
        print("ERROR: nnunetv2 not installed!")
        return False

def run_preprocessing():
    """Run preprocessing"""
    print("\n" + "=" * 60)
    print("Running Preprocessing")
    print("=" * 60)
    print("This will:")
    print("  - Verify dataset integrity")
    print("  - Analyze dataset properties (spacing, sizes, etc.)")
    print("  - Create preprocessing plans")
    print("  - Preprocess all training cases")
    print("  - Create 5-fold cross-validation splits")
    print("\nThis may take 10-30 minutes depending on dataset size...")
    
    cmd = [
        sys.executable, '-m', 'nnunetv2.experiment_planning.plan_and_preprocess_entrypoints',
        '-d', '1',
        '--verify_dataset_integrity',
        '-c', '3d_fullres',
        '-np', '4'
    ]
    
    try:
        result = subprocess.run(cmd, check=False)
        
        if result.returncode != 0:
            print("\nERROR: Preprocessing failed!")
            return False
        
        print("\n" + "=" * 60)
        print("Preprocessing completed successfully!")
        print(f"Preprocessed data: {os.environ['nnUNet_preprocessed']}/Dataset001_LowerLimb")
        print("=" * 60)
        print("\nNext steps:")
        print("  1. Start training: python train_nnunet.py")
        print("  2. Or train single fold: python train_single_fold.py --fold 0")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    # Set environment variables
    set_environment_variables()
    
    # Verify dataset
    print("\nVerifying dataset...")
    if not verify_dataset():
        print("\nDataset verification failed!")
        print("Make sure you have run prepare_for_nnunet.py first.")
        sys.exit(1)
    
    # Run preprocessing
    success = run_preprocessing()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
