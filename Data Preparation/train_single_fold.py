"""
Train a single fold of nnU-Net
Useful for testing or resuming interrupted training
"""
import os
import sys
import argparse
import subprocess
from pathlib import Path

def set_environment_variables():
    """Set nnU-Net environment variables"""
    base_path = Path(__file__).parent.absolute()
    
    os.environ['nnUNet_raw'] = str(base_path / 'nnUNet_raw_data')
    os.environ['nnUNet_preprocessed'] = str(base_path / 'nnUNet_preprocessed')
    os.environ['nnUNet_results'] = str(base_path / 'nnUNet_results')

def verify_gpu():
    """Verify GPU availability"""
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        if cuda_available:
            print(f"GPU: {torch.cuda.get_device_name(0)}")
        else:
            print("WARNING: No GPU detected!")
        return cuda_available
    except ImportError:
        print("ERROR: PyTorch not installed!")
        return False

def train_fold(fold, continue_training=False):
    """Train a single fold"""
    print("=" * 60)
    print(f"Training Fold {fold}")
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
        print("Continuing from previous checkpoint...")
    
    try:
        result = subprocess.run(cmd, check=False)
        
        if result.returncode != 0:
            print(f"\nERROR: Training fold {fold} failed!")
            return False
        
        print(f"\nFold {fold} completed successfully!")
        return True
    except KeyboardInterrupt:
        print(f"\nTraining fold {fold} interrupted by user.")
        print("Training progress has been saved. Resume with --continue flag.")
        return False
    except Exception as e:
        print(f"ERROR during training: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Train a single nnU-Net fold')
    parser.add_argument('--fold', type=int, required=True, choices=[0,1,2,3,4],
                       help='Fold number to train (0-4)')
    parser.add_argument('--continue', dest='continue_training', action='store_true',
                       help='Continue training from last checkpoint')
    
    args = parser.parse_args()
    
    # Set environment variables
    # set_environment_variables()
    
    # Verify GPU
    verify_gpu()
    
    # Train fold
    success = train_fold(args.fold, args.continue_training)
    
    if success:
        print(f"\nFold {args.fold} training completed!")
        print(f"Results: {os.environ['nnUNet_results']}/Dataset001_LowerLimb")
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
