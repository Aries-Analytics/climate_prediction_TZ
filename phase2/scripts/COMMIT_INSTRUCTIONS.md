# Commit Instructions for Phase 2

## Current Branch
You are on: `phase2/feature-expansion`

## Correct Commit Commands

```bash
# 1. Check current branch (should show phase2/feature-expansion)
git branch --show-current

# 2. Stage all changes
git add -A

# 3. Commit with message
git commit -m "feat: Reorganize project structure and complete ML pipeline

- Created pipelines/ for clear entry points
- Organized scripts/ and docs/ folders
- Completed ML pipeline with 98.3% R² (baseline + RF + XGBoost + Ensemble)
- Root directory 56% cleaner (45+ files → 20 files)
- All models exceed 85% target
- Added comprehensive evaluation with seasonal analysis
- Implemented experiment tracking"

# 4. Push to the correct branch
git push origin phase2/feature-expansion
```

## What Will Be Committed

### New Folders
- `pipelines/` - Main entry points
- `scripts/demos/` - Demo scripts
- `scripts/analysis/` - Analysis scripts
- `scripts/verification/` - Verification scripts
- `docs/guides/` - User guides
- `docs/reports/` - Status reports
- `src/` - Ready for source code
- `configs/` - Ready for configs

### New Files
- ML model implementations
- Enhanced evaluation code
- Organized documentation
- Pipeline entry points

### Modified Files
- Updated imports in pipelines
- Enhanced evaluation functions
- Updated documentation

### Deleted Files
- Old markdown files from root (moved to docs/)
- Old script files from root (moved to scripts/)

## After Commit

1. Check GitHub Actions workflows run
2. Verify CI/CD tests pass
3. Create Pull Request to merge into main (if ready)

## Branch Structure

```
main (production)
  └── phase2/feature-expansion (your current branch)
```

**Always push to `phase2/feature-expansion`, NOT to `main`!**
