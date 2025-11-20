"""
Check nnU-Net training progress
Shows status of all folds and recent training metrics
"""
import os
import json
from pathlib import Path
from datetime import datetime

def set_environment_variables():
    """Set nnU-Net environment variables"""
    base_path = Path(__file__).parent.absolute()
    os.environ['nnUNet_results'] = str(base_path / 'nnUNet_results')

def check_fold_status(fold_path):
    """Check status of a single fold"""
    fold_name = fold_path.name
    
    # Check for checkpoints
    checkpoint_final = fold_path / "checkpoint_final.pth"
    checkpoint_latest = fold_path / "checkpoint_latest.pth"
    checkpoint_best = fold_path / "checkpoint_best.pth"
    
    if checkpoint_final.exists():
        status = "COMPLETED"
        color = "✓"
        last_update = checkpoint_final.stat().st_mtime
    elif checkpoint_latest.exists():
        status = "IN PROGRESS"
        color = "⟳"
        last_update = checkpoint_latest.stat().st_mtime
    else:
        status = "NOT STARTED"
        color = "○"
        last_update = None
    
    print(f"\n{color} {fold_name}:")
    print(f"  Status: {status}")
    
    if last_update:
        last_update_str = datetime.fromtimestamp(last_update).strftime('%Y-%m-%d %H:%M:%S')
        print(f"  Last update: {last_update_str}")
    
    # Check for training progress
    progress_file = fold_path / "progress.png"
    if progress_file.exists():
        print(f"  Progress plot: Available")
    
    # Check for validation results
    validation_raw = fold_path / "validation_raw"
    if validation_raw.exists():
        print(f"  Validation results: Available")
    
    # Try to read training log for latest metrics
    log_files = sorted(fold_path.glob("training_log*.txt"))
    if log_files:
        latest_log = log_files[-1]
        try:
            with open(latest_log, 'r') as f:
                lines = f.readlines()
                if len(lines) > 5:
                    # Get last few lines with metrics
                    print(f"  Latest log: {latest_log.name}")
                    for line in lines[-5:]:
                        line = line.strip()
                        if line and ('epoch' in line.lower() or 'loss' in line.lower() or 'dice' in line.lower()):
                            print(f"    {line[:80]}")
        except:
            pass
    
    # Check validation summary if completed
    val_summary = fold_path / "validation_raw_postprocessed" / "summary.json"
    if val_summary.exists():
        try:
            with open(val_summary, 'r') as f:
                summary = json.load(f)
                if 'foreground_mean' in summary:
                    print(f"  Validation Dice: {summary['foreground_mean']['Dice']:.4f}")
        except:
            pass
    
    return status

def main():
    print("=" * 60)
    print("nnU-Net Training Progress")
    print("=" * 60)
    
    # Set environment variables
    set_environment_variables()
    
    results_dir = Path(os.environ['nnUNet_results']) / "Dataset001_LowerLimb"
    
    if not results_dir.exists():
        print(f"\nNo training results found.")
        print(f"Expected path: {results_dir}")
        print("\nHave you started training yet?")
        print("  Run: python train_nnunet.py")
        return
    
    # Find trainer directory
    trainer_dirs = list(results_dir.glob("nnUNetTrainer*"))
    if not trainer_dirs:
        print(f"\nNo trainer directories found in {results_dir}")
        return
    
    trainer_dir = trainer_dirs[0]
    print(f"\nTrainer: {trainer_dir.name}")
    
    # Check all folds
    fold_paths = sorted([p for p in trainer_dir.iterdir() if p.is_dir() and p.name.startswith('fold_')])
    
    if not fold_paths:
        print("\nNo folds found. Training hasn't started yet.")
        print("Run: python train_nnunet.py")
        return
    
    print(f"\nFolds found: {len(fold_paths)}")
    
    statuses = {}
    for fold_path in fold_paths:
        status = check_fold_status(fold_path)
        statuses[fold_path.name] = status
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary:")
    completed = sum(1 for s in statuses.values() if s == "COMPLETED")
    in_progress = sum(1 for s in statuses.values() if s == "IN PROGRESS")
    not_started = sum(1 for s in statuses.values() if s == "NOT STARTED")
    
    print(f"  Completed: {completed}/5")
    print(f"  In Progress: {in_progress}/5")
    print(f"  Not Started: {not_started}/5")
    
    if completed == 5:
        print("\n✓ All folds completed!")
        print("\nNext steps:")
        print("  1. Find best configuration:")
        print("     nnUNetv2_find_best_configuration 1 -c 3d_fullres")
        print("  2. Run inference on test data")
    elif in_progress > 0:
        print(f"\n⟳ Training in progress...")
    else:
        print(f"\nℹ Training not started or paused")
        print("  Continue: python train_nnunet.py")
    
    print("\nDetailed logs location:")
    print(f"  {trainer_dir}")
    print("=" * 60)

if __name__ == '__main__':
    main()
