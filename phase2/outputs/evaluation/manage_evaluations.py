"""
Evaluation Archive Management Script

Helps manage evaluation results in outputs/evaluation/
"""

import shutil
from datetime import datetime
from pathlib import Path


def list_archives():
    """List all archived evaluations."""
    archive_dir = Path("outputs/evaluation/archive")
    if not archive_dir.exists():
        print("No archives found.")
        return []
    
    archives = sorted(archive_dir.iterdir(), reverse=True)
    print(f"\n{'='*60}")
    print(f"ARCHIVED EVALUATIONS ({len(archives)} total)")
    print(f"{'='*60}")
    
    for i, archive in enumerate(archives, 1):
        if archive.is_dir():
            file_count = len(list(archive.glob("*")))
            size_mb = sum(f.stat().st_size for f in archive.glob("*")) / (1024 * 1024)
            print(f"{i}. {archive.name}")
            print(f"   Files: {file_count}, Size: {size_mb:.2f} MB")
    
    return archives


def archive_current():
    """Archive current latest/ results with timestamp."""
    latest_dir = Path("outputs/evaluation/latest")
    archive_base = Path("outputs/evaluation/archive")
    
    if not latest_dir.exists() or not list(latest_dir.glob("*")):
        print("No current results to archive.")
        return
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    archive_path = archive_base / timestamp
    archive_base.mkdir(parents=True, exist_ok=True)
    
    shutil.copytree(latest_dir, archive_path)
    print(f"✓ Archived current results to: {archive_path.name}")


def clean_old_archives(keep_last=5):
    """Keep only the N most recent archives."""
    archives = list_archives()
    
    if len(archives) <= keep_last:
        print(f"\n✓ Only {len(archives)} archives. Nothing to clean (keeping last {keep_last}).")
        return
    
    to_delete = archives[keep_last:]
    print(f"\n⚠️  Will delete {len(to_delete)} old archives:")
    for archive in to_delete:
        print(f"  - {archive.name}")
    
    confirm = input(f"\nProceed? (yes/no): ").strip().lower()
    if confirm == 'yes':
        for archive in to_delete:
            shutil.rmtree(archive)
            print(f"  ✓ Deleted {archive.name}")
        print(f"\n✓ Cleaned up {len(to_delete)} archives. Kept last {keep_last}.")
    else:
        print("Cancelled.")


def compare_archives(archive1_name, archive2_name):
    """Compare metrics between two archived evaluations."""
    import json
    
    archive_dir = Path("outputs/evaluation/archive")
    
    def load_summary(name):
        summary_path = archive_dir / name / "evaluation_summary.json"
        if not summary_path.exists():
            return None
        with open(summary_path) as f:
            return json.load(f)
    
    summary1 = load_summary(archive1_name)
    summary2 = load_summary(archive2_name)
    
    if not summary1 or not summary2:
        print("Could not load summaries for comparison.")
        return
    
    print(f"\n{'='*60}")
    print(f"COMPARISON: {archive1_name} vs {archive2_name}")
    print(f"{'='*60}")
    
    for model in ['rf', 'xgb', 'lstm', 'ensemble']:
        if model in summary1.get('models', {}) and model in summary2.get('models', {}):
            m1 = summary1['models'][model]
            m2 = summary2['models'][model]
            
            print(f"\n{model.upper()}:")
            print(f"  R²:   {m1['r2_score']:.4f} → {m2['r2_score']:.4f} "
                  f"({'↑' if m2['r2_score'] > m1['r2_score'] else '↓'} "
                  f"{abs(m2['r2_score'] - m1['r2_score']):.4f})")
            print(f"  RMSE: {m1['rmse']:.4f} → {m2['rmse']:.4f} "
                  f"({'↓' if m2['rmse'] < m1['rmse'] else '↑'} "
                  f"{abs(m2['rmse'] - m1['rmse']):.4f})")


def main():
    """Main menu."""
    print("\n" + "="*60)
    print("EVALUATION ARCHIVE MANAGER")
    print("="*60)
    print("\n1. List all archives")
    print("2. Archive current results")
    print("3. Clean old archives (keep last 5)")
    print("4. Compare two archives")
    print("5. Exit")
    
    choice = input("\nSelect option (1-5): ").strip()
    
    if choice == '1':
        list_archives()
    elif choice == '2':
        archive_current()
    elif choice == '3':
        clean_old_archives(keep_last=5)
    elif choice == '4':
        archives = list_archives()
        if len(archives) >= 2:
            print("\nEnter archive names to compare:")
            arch1 = input("  First archive: ").strip()
            arch2 = input("  Second archive: ").strip()
            compare_archives(arch1, arch2)
        else:
            print("Need at least 2 archives to compare.")
    elif choice == '5':
        print("Goodbye!")
        return
    else:
        print("Invalid choice.")


if __name__ == "__main__":
    main()
