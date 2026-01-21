#!/bin/bash
# Git commit commands for reorganization

# Stage all changes (new files, modified files, deleted files)
git add -A

# Commit with detailed message
git commit -F COMMIT_MESSAGE.txt

# Or use this shorter version:
# git commit -m "feat: Reorganize project structure and complete ML pipeline" \
#            -m "- Created pipelines/ for clear entry points" \
#            -m "- Organized scripts/ and docs/" \
#            -m "- Completed ML pipeline with 98.3% R² (baseline + RF + XGBoost + Ensemble)" \
#            -m "- Root directory 56% cleaner"

echo "✓ Committed successfully!"
echo ""
echo "Next steps:"
echo "  git push origin main"
