"""
nnU-Net v2 Training Script for Dataset001_LowerLimb
Complete training pipeline in Python
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
    print("nnU-Net Environment Variables Set:")
    print(f"  nnUNet_raw: {os.environ['nnUNet_raw']}")
    print(f"  nnUNet_preprocessed: {os.environ['nnUNet_preprocessed']}")
    print(f"  nnUNet_results: {os.environ['nnUNet_results']}")
    print("=" * 60)

def verify_gpu():
    """Verify GPU availability"""
    print("\n[Verifying GPU...]")
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        print(f"CUDA available: {cuda_available}")
        if cuda_available:
            print(f"GPU: {torch.cuda.get_device_name(0)}")
            print(f"PyTorch version: {torch.__version__}")
            print(f"CUDA version: {torch.version.cuda}")
        else:
            print("WARNING: No GPU detected. Training will be very slow!")
        return cuda_available
    except ImportError:
        print("ERROR: PyTorch not installed!")
        print("Install with: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121")
        return False

def verify_paths():
    """Verify nnU-Net paths"""
    print("\n[Verifying nnU-Net paths...]")
    try:
        from nnunetv2.paths import nnUNet_raw, nnUNet_preprocessed, nnUNet_results
        print(f"nnUNet_raw: {nnUNet_raw}")
        print(f"nnUNet_preprocessed: {nnUNet_preprocessed}")
        print(f"nnUNet_results: {nnUNet_results}")
        
        dataset_path = Path(nnUNet_raw) / "Dataset001_LowerLimb"
        if not dataset_path.exists():
            print(f"ERROR: Dataset not found at {dataset_path}")
            return False
        
        # Check for required dataset files
        images_tr = dataset_path / "imagesTr"
        labels_tr = dataset_path / "labelsTr"
        dataset_json = dataset_path / "dataset.json"
        
        if not images_tr.exists():
            print(f"ERROR: imagesTr folder not found at {images_tr}")
            return False
        if not labels_tr.exists():
            print(f"ERROR: labelsTr folder not found at {labels_tr}")
            return False
        if not dataset_json.exists():
            print(f"ERROR: dataset.json not found at {dataset_json}")
            return False
            
        # Count files
        num_images = len(list(images_tr.glob("*.nii.gz")))
        num_labels = len(list(labels_tr.glob("*.nii.gz")))
        
        print(f"Dataset found: {dataset_path}")
        print(f"  Images: {num_images}")
        print(f"  Labels: {num_labels}")
        
        if num_images == 0 or num_labels == 0:
            print("ERROR: No training data found!")
            return False
        if num_images != num_labels:
            print(f"WARNING: Image count ({num_images}) doesn't match label count ({num_labels})")
            
        return True
    except ImportError:
        print("ERROR: nnunetv2 not installed!")
        print("Install with: pip install nnunetv2")
        return False

def preprocess_dataset():
    """Run nnU-Net preprocessing"""
    print("\n" + "=" * 60)
    print("[Step: Preprocessing Dataset]")
    print("=" * 60)
    
    preprocessed_path = Path(os.environ['nnUNet_preprocessed']) / "Dataset001_LowerLimb"
    
    if preprocessed_path.exists() and any(preprocessed_path.iterdir()):
        print("Preprocessing already completed. Skipping...")
        return True
    
    print("Running preprocessing (this may take a while)...")
    print("This will:")
    print("  - Analyze dataset properties")
    print("  - Create preprocessing plans")
    print("  - Preprocess all training cases")
    print("  - Split data into 5 folds for cross-validation")
    
    cmd = [
        sys.executable, '-m', 'nnunetv2.experiment_planning.plan_and_preprocess_entrypoints',
        '-d', '1',
        '--verify_dataset_integrity',
        '-c', '3d_fullres',
        '-np', '4'  # Use 4 processes for preprocessing
    ]
    
    try:
        result = subprocess.run(cmd, check=False)
        
        if result.returncode != 0:
            print("ERROR: Preprocessing failed!")
            return False
        
        print("\nPreprocessing completed successfully!")
        return True
    except Exception as e:
        print(f"ERROR during preprocessing: {e}")
        return False

def train_fold(fold, continue_training=False):
    """Train a single fold"""
    print("\n" + "=" * 60)
    print(f"[Training Fold {fold}]")
    print("=" * 60)
    
    cmd = [
        'nnUNetv2_train',
        '1',  # dataset id
        '3d_fullres',  # configuration
        str(fold),  # fold
        '--npz'  # save softmax predictions
    ]
    
    if continue_training:
        cmd.append('--c')
    
    try:
        result = subprocess.run(cmd, check=False)
        
        if result.returncode != 0:
            print(f"ERROR: Training fold {fold} failed!")
            return False
        
        print(f"\nFold {fold} completed successfully!")
        return True
    except KeyboardInterrupt:
        print(f"\nTraining fold {fold} interrupted by user.")
        return False
    except Exception as e:
        print(f"ERROR during training fold {fold}: {e}")
        return False

def train_all_folds(start_fold=0):
    """Train all 5 folds"""
    print("\n" + "=" * 60)
    print("[Training All Folds]")
    print("This will take several hours/days depending on your GPU")
    print("You can interrupt training with Ctrl+C and resume later")
    print("=" * 60)
    
    for fold in range(start_fold, 5):
        print(f"\n>>> Starting fold {fold} (fold {fold+1}/5)")
        success = train_fold(fold)
        if not success:
            print(f"\nTraining stopped at fold {fold}.")
            print(f"To resume, run: python train_single_fold.py --fold {fold}")
            return False
    
    print("\n" + "=" * 60)
    print("Training completed for all folds!")
    print(f"Results saved in: {os.environ['nnUNet_results']}/Dataset001_LowerLimb")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Find best configuration: nnUNetv2_find_best_configuration 1 -c 3d_fullres")
    print("  2. Run inference on test data: nnUNetv2_predict [options]")
    return True

def main():
    """Main training pipeline"""
    print("\n" + "=" * 60)
    print("nnU-Net v2 Training Pipeline")
    print("Dataset: 001_LowerLimb")
    print("=" * 60)
    
    # Step 1: Set environment variables
    # set_environment_variables()
    
    # Step 2: Verify GPU
    has_gpu = verify_gpu()
    if not has_gpu:
        response = input("\nNo GPU detected. Training will be VERY slow. Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Training cancelled.")
            return
    
    # Step 3: Verify paths
    if not verify_paths():
        print("\nERROR: Path verification failed. Please check your setup.")
        print("Make sure you have run prepare_for_nnunet.py first.")
        return
    
    # Step 4: Preprocess dataset
    print("\nStarting preprocessing...")
    if not preprocess_dataset():
        print("\nERROR: Preprocessing failed.")
        return
    
    # Step 5: Ask user confirmation before training
    print("\nPreprocessing complete. Ready to start training.")
    response = input("Start training all 5 folds now? (y/n): ")
    if response.lower() != 'y':
        print("Training cancelled. You can start training later with:")
        print("  python train_nnunet.py")
        print("Or train individual folds with:")
        print("  python train_single_fold.py --fold 0")
        return
    
    # Step 6: Train all folds
    train_all_folds()

if __name__ == '__main__':
    main()
