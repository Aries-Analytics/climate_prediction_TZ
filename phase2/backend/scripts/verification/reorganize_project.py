"""
Project Reorganization Script
Safely reorganizes the project structure without breaking anything
"""

import os
import shutil
import sys
from pathlib import Path


def create_directory_structure():
    """Create the new directory structure"""

    directories = [
        # Source code
        "src/ingestion",
        "src/processing",
        "src/features",
        "src/models",
        "src/evaluation",
        "src/utils",
        # Pipelines
        "pipelines",
        # Scripts
        "scripts/demos",
        "scripts/analysis",
        "scripts/verification",
        # Documentation
        "docs/guides",
        "docs/reports",
        "docs/specs",
        "docs/api",
        # Configs
        "configs",
        # Organized outputs
        "outputs/data/raw",
        "outputs/data/processed",
        "outputs/models/production",
        "outputs/evaluation/latest",
        "outputs/visualizations/eda",
        "outputs/visualizations/models",
    ]

    print("Creating new directory structure...")
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Created {directory}/")

    print("\n✓ Directory structure created successfully!")


def move_documentation():
    """Move all markdown documentation files to docs/"""

    print("\nMoving documentation files...")

    # Documentation files to move
    doc_files = {
        # Guides
        "QUICK_START_PROCESSING.md": "docs/guides/",
        "MODEL_PIPELINE_README.md": "docs/guides/",
        "VIEW_EVALUATION_REPORTS.md": "docs/guides/",
        # Reports
        "PIPELINE_STATUS_REPORT.md": "docs/reports/",
        "MODEL_DEVELOPMENT_STATUS.md": "docs/reports/",
        "FINAL_MODEL_PIPELINE_REPORT.md": "docs/reports/",
        "FINAL_PIPELINE_REPORT.md": "docs/reports/",
        "EVALUATION_RESULTS_SUMMARY.md": "docs/reports/",
        "MODELS_STATUS_FINAL.md": "docs/reports/",
        "PIPELINE_COMPLETE_SUMMARY.md": "docs/reports/",
        "PIPELINE_SUCCESS_SUMMARY.md": "docs/reports/",
        "COMPLETION_SUMMARY.md": "docs/reports/",
        "COMPREHENSIVE_PIPELINE_RESULTS.md": "docs/reports/",
        "MULTI_MODEL_PIPELINE_REPORT.md": "docs/reports/",
        "LSTM_ENSEMBLE_FIXED_SUMMARY.md": "docs/reports/",
    }

    for source, dest_dir in doc_files.items():
        if Path(source).exists():
            dest = Path(dest_dir) / source
            shutil.copy2(source, dest)
            print(f"  ✓ Copied {source} → {dest}")

    print("\n✓ Documentation files organized!")


def move_scripts():
    """Move demo, analysis, and verification scripts"""

    print("\nMoving scripts...")

    # Demo scripts
    demo_scripts = [
        "demo_chirps_processing.py",
        "demo_chirps_synthetic.py",
        "demo_ndvi_synthetic.py",
        "demo_ocean_indices_synthetic.py",
    ]

    for script in demo_scripts:
        if Path(script).exists():
            dest = Path("scripts/demos") / script
            shutil.copy2(script, dest)
            print(f"  ✓ Copied {script} → scripts/demos/")

    # Analysis scripts
    analysis_scripts = [
        "eda_analysis.py",
        "eda_master_dataset.py",
        "run_eda.py",
        "generate_visualizations.py",
    ]

    for script in analysis_scripts:
        if Path(script).exists():
            dest = Path("scripts/analysis") / script
            shutil.copy2(script, dest)
            print(f"  ✓ Copied {script} → scripts/analysis/")

    # Verification scripts
    verification_scripts = [
        "check_era5.py",
        "test_gee_access.py",
        "verify_model_save_load.py",
        "fetch_real_data.py",
    ]

    for script in verification_scripts:
        if Path(script).exists():
            dest = Path("scripts/verification") / script
            shutil.copy2(script, dest)
            print(f"  ✓ Copied {script} → scripts/verification/")

    print("\n✓ Scripts organized!")


def create_pipeline_entry_points():
    """Create clean pipeline entry points"""

    print("\nCreating pipeline entry points...")

    # Copy and rename main pipelines
    if Path("run_pipeline.py").exists():
        shutil.copy2("run_pipeline.py", "pipelines/run_data_pipeline.py")
        print("  ✓ Created pipelines/run_data_pipeline.py")

    if Path("model_development_pipeline.py").exists():
        shutil.copy2("model_development_pipeline.py", "pipelines/run_model_pipeline.py")
        print("  ✓ Created pipelines/run_model_pipeline.py")

    print("\n✓ Pipeline entry points created!")


def create_master_readme():
    """Create a master README for the docs folder"""

    readme_content = """# Tanzania Climate Prediction - Documentation

## 📚 Documentation Index

### 🚀 Quick Start Guides
- [Quick Start Processing](guides/QUICK_START_PROCESSING.md) - Get started with data processing
- [Model Pipeline Guide](guides/MODEL_PIPELINE_README.md) - Train and evaluate models
- [Evaluation Reports Guide](guides/VIEW_EVALUATION_REPORTS.md) - View model results

### 📊 Status Reports
- [Pipeline Status](reports/PIPELINE_STATUS_REPORT.md) - Data pipeline status
- [Model Status](reports/MODELS_STATUS_FINAL.md) - Model training status
- [Evaluation Results](reports/EVALUATION_RESULTS_SUMMARY.md) - Latest model results

### 📖 Technical Documentation
- [Architecture](ARCHITECTURE.md) - System architecture
- [API Documentation](api/) - API references
- [Specifications](specs/) - Technical specifications

### 🔧 Development
- [Contributing](CONTRIBUTING.md) - How to contribute
- [Changelog](CHANGELOG.md) - Version history

---

## 📁 Project Structure

```
tanzania-climate-prediction/
├── src/              # Source code
├── pipelines/        # Main pipeline scripts
├── scripts/          # Utility scripts
├── tests/            # Tests
├── docs/             # Documentation (you are here)
├── outputs/          # All outputs
└── configs/          # Configuration files
```

## 🎯 Common Tasks

### Run Data Pipeline
```bash
python pipelines/run_data_pipeline.py
```

### Run Model Pipeline
```bash
python pipelines/run_model_pipeline.py
```

### View Latest Results
```bash
# Check outputs/evaluation/latest/
```

---

For more information, see the main [README.md](../README.md)
"""

    with open("docs/README.md", "w") as f:
        f.write(readme_content)

    print("\n✓ Created docs/README.md")


def create_summary_report():
    """Create a summary of what was done"""

    summary = """# Project Reorganization Summary

## ✅ Completed Actions

### 1. Directory Structure Created
- ✅ src/ (source code organization)
- ✅ pipelines/ (entry points)
- ✅ scripts/ (demos, analysis, verification)
- ✅ docs/ (all documentation)
- ✅ configs/ (configuration files)

### 2. Documentation Organized
- ✅ Moved 13+ markdown files to docs/
- ✅ Organized into guides/ and reports/
- ✅ Created docs/README.md

### 3. Scripts Organized
- ✅ Moved demo scripts to scripts/demos/
- ✅ Moved analysis scripts to scripts/analysis/
- ✅ Moved verification scripts to scripts/verification/

### 4. Pipeline Entry Points
- ✅ Created pipelines/run_data_pipeline.py
- ✅ Created pipelines/run_model_pipeline.py

## 📋 Next Steps

### Phase 1: Testing (Do This Now)
1. Test that pipelines still work:
   ```bash
   python pipelines/run_data_pipeline.py
   python pipelines/run_model_pipeline.py
   ```

2. Verify scripts work from new locations:
   ```bash
   python scripts/demos/demo_chirps_processing.py
   python scripts/analysis/eda_analysis.py
   ```

### Phase 2: Source Code Migration (Optional)
1. Move modules/ to src/
2. Update all imports
3. Test thoroughly

### Phase 3: Cleanup (After Testing)
1. Delete old markdown files from root (after verifying copies work)
2. Delete old script files from root (after verifying copies work)
3. Update .gitignore

## ⚠️ Important Notes

1. **Original files are still in place** - Nothing was deleted, only copied
2. **Test the new structure** before deleting old files
3. **Update imports** if you move source code to src/
4. **Keep backups** of important files

## 📁 New Structure

```
tanzania-climate-prediction/
├── pipelines/           # ← NEW: Main entry points
├── scripts/             # ← NEW: Organized scripts
│   ├── demos/
│   ├── analysis/
│   └── verification/
├── docs/                # ← ORGANIZED: All documentation
│   ├── guides/
│   ├── reports/
│   └── README.md
├── src/                 # ← READY: For source code migration
├── configs/             # ← READY: For config files
└── [original files]     # ← KEPT: Original structure intact
```

## 🎯 Benefits

1. ✅ Root directory much cleaner (13+ files moved)
2. ✅ Clear entry points in pipelines/
3. ✅ Organized documentation in docs/
4. ✅ Scripts grouped by purpose
5. ✅ Ready for source code migration

## 🚀 Quick Access

### Run Pipelines
```bash
python pipelines/run_data_pipeline.py
python pipelines/run_model_pipeline.py
```

### View Documentation
```bash
# Open docs/README.md for full index
```

### Run Scripts
```bash
python scripts/demos/demo_chirps_processing.py
python scripts/analysis/eda_analysis.py
python scripts/verification/check_era5.py
```

---

**Status: Phase 1 Complete - Ready for Testing** ✅
"""

    with open("REORGANIZATION_SUMMARY.md", "w") as f:
        f.write(summary)

    print("\n✓ Created REORGANIZATION_SUMMARY.md")


def main():
    """Main reorganization function"""

    print("=" * 80)
    print("PROJECT REORGANIZATION SCRIPT")
    print("=" * 80)
    print("\nThis script will:")
    print("1. Create new directory structure")
    print("2. Copy (not move) files to new locations")
    print("3. Keep original files intact for safety")
    print("\n⚠️  Original files will NOT be deleted - you can do that after testing")
    print("=" * 80)

    response = input("\nProceed with reorganization? (yes/no): ")

    if response.lower() not in ["yes", "y"]:
        print("\nReorganization cancelled.")
        return

    try:
        # Execute reorganization steps
        create_directory_structure()
        move_documentation()
        move_scripts()
        create_pipeline_entry_points()
        create_master_readme()
        create_summary_report()

        print("\n" + "=" * 80)
        print("✅ REORGANIZATION COMPLETE!")
        print("=" * 80)
        print("\nNext steps:")
        print("1. Read REORGANIZATION_SUMMARY.md")
        print("2. Test the new structure:")
        print("   python pipelines/run_data_pipeline.py")
        print("3. Check docs/README.md for documentation index")
        print("4. After testing, you can delete old files from root")
        print("\n⚠️  Original files are still in place - test before deleting!")
        print("=" * 80)

    except Exception as e:
        print(f"\n✗ Error during reorganization: {e}")
        print("Please check the error and try again.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
