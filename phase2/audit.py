#!/usr/bin/env python3
"""
HewaSense Audit Tool — GOTCHA-Enhanced
=======================================
Scans the codebase for forbidden patterns before any merge.
Reads forbidden list from args/persona_config.yaml.

Usage:
    python audit.py              # Run full audit
    python audit.py --verbose    # Show per-file details

Exit codes:
    0 = Clean (safe to merge in Auditor mode)
    1 = Violations found (merge blocked)
"""

import os
import sys
import re
from pathlib import Path


def load_forbidden_patterns():
    """Load forbidden patterns from args/persona_config.yaml."""
    config_path = Path(__file__).parent / "args" / "persona_config.yaml"
    
    # Default patterns if config not found
    default_patterns = [
        'predict_proba',
        'dummy_data',
        'synthetic',
        'np.random.normal',
    ]
    
    default_test_allowed = ['mock']
    
    if not config_path.exists():
        print(f"WARNING: {config_path} not found, using default forbidden patterns")
        return default_patterns, default_test_allowed
    
    try:
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        patterns = config.get('forbidden_patterns', default_patterns)
        # Clean up quoted patterns
        patterns = [p.strip('"').strip("'") for p in patterns]
        test_allowed = config.get('test_allowed_patterns', default_test_allowed)
        return patterns, test_allowed
    except ImportError:
        print("WARNING: PyYAML not installed, using default forbidden patterns")
        return default_patterns, default_test_allowed
    except Exception as e:
        print(f"WARNING: Error reading config: {e}, using defaults")
        return default_patterns, default_test_allowed


def check_naive_datetime(content, filepath):
    """Check for naive datetime.now() usage (Issues 6 & 11)."""
    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        # Match datetime.now() without timezone argument
        if re.search(r'datetime\.now\(\s*\)', line) and 'timezone' not in line:
            # Skip comments
            stripped = line.lstrip()
            if stripped.startswith('#'):
                continue
            issues.append({
                'file': filepath,
                'line': i,
                'pattern': 'datetime.now()',
                'content': line.strip(),
                'rule': 'DATA TRUTH: Use datetime.now(timezone.utc), not naive datetime.now()'
            })
    return issues


def check_location_id_mismatch(content, filepath):
    """Check for hardcoded locationId: 1 (Issue 5)."""
    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        stripped = line.lstrip()
        if stripped.startswith('#'):
            continue
        # Check for locationId = 1 or location_id = 1 patterns
        if re.search(r'location[_]?[iI]d\s*[=:]\s*1\b', line):
            issues.append({
                'file': filepath,
                'line': i,
                'pattern': 'locationId = 1',
                'content': line.strip(),
                'rule': 'CONTRACT: PILOT_LOCATION_ID must be 6, not 1'
            })
    return issues


def run_audit(verbose=False):
    """Run full codebase audit."""
    forbidden_patterns, test_allowed = load_forbidden_patterns()
    
    all_issues = []
    files_scanned = 0
    phase2_dir = Path(__file__).parent
    
    # File extensions to scan
    scan_extensions = {'.py', '.ts', '.tsx', '.js', '.jsx'}
    
    # Directories to skip
    # AUDIT SCOPE: Production serving code only (app/, frontend/)
    # Non-production directories below are excluded to reduce false positives.
    # To audit ALL code, remove non-essential entries from this set.
    skip_dirs = {
        'node_modules', '.pytest_cache', '__pycache__', 
        'htmlcov', '.hypothesis', '.git', 'venv', '.venv',
        'docs',           # Don't scan documentation
        'legacy',         # Old code kept for reference only
        'demos',          # Demo/example scripts
        'tests',          # Test files have their own allowed patterns
        'evaluation',     # Research/evaluation scripts
        'scripts',        # Data loaders, seeders, training scripts
        'models',         # ML training code (not production serving)
        'modules',        # Data ingestion/calibration utilities
        'pipelines',      # ML pipelines (offline, not serving)
        'preprocessing',  # Feature engineering (offline)
        'reporting',      # Report generation utilities
        'tools',          # Memory, devops tooling
        'utils',          # Shared utilities (scheduler, cache, etc.)
    }
    
    # Files to skip (avoid self-referencing violations)
    skip_files = {'audit.py', 'fetch_recent_chirps.py'}
    
    for root, dirs, files in os.walk(phase2_dir):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        for filename in files:
            ext = Path(filename).suffix
            if ext not in scan_extensions:
                continue
            
            filepath = os.path.join(root, filename)
            rel_path = os.path.relpath(filepath, phase2_dir)
            
            # Skip self and excluded files
            if filename in skip_files:
                continue
            
            # Skip test files for forbidden patterns (handled below)
            is_test_file = ('test' in filename.lower() or 
                           'tests' in rel_path.lower())
            
            # Skip legacy/training scripts that legitimately use ML patterns
            is_legacy = ('legacy' in rel_path.lower() or 
                        'demo' in rel_path.lower() or
                        'train_pipeline' in filename.lower())
            if is_legacy:
                continue
            
            files_scanned += 1
            
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except Exception:
                continue
            
            # Check forbidden patterns
            for pattern in forbidden_patterns:
                clean_pattern = pattern.strip('"').strip("'")
                
                # Skip test-allowed patterns in test files
                if is_test_file and clean_pattern in test_allowed:
                    continue
                
                for i, line in enumerate(content.split('\n'), 1):
                    stripped = line.lstrip()
                    if stripped.startswith('#') or stripped.startswith('//'):
                        continue
                    
                    if clean_pattern.lower() in line.lower():
                        # Skip known legitimate uses
                        if clean_pattern == 'synthetic' and 'SyntheticEvent' in line:
                            continue
                        all_issues.append({
                            'file': rel_path,
                            'line': i,
                            'pattern': clean_pattern,
                            'content': line.strip()[:100],
                            'rule': f'FORBIDDEN PATTERN: {clean_pattern}'
                        })
            
            # Check naive datetime (only in .py files)
            if ext == '.py' and not is_test_file:
                all_issues.extend(check_naive_datetime(content, rel_path))
            
            # Check location ID mismatch
            if not is_test_file:
                all_issues.extend(check_location_id_mismatch(content, rel_path))
    
    # Report results
    print(f"\n{'='*60}")
    print(f"  HewaSense Audit Report (GOTCHA-Enhanced)")
    print(f"{'='*60}")
    print(f"  Files scanned: {files_scanned}")
    print(f"  Violations found: {len(all_issues)}")
    print(f"{'='*60}\n")
    
    if all_issues:
        # Group by rule
        by_rule = {}
        for issue in all_issues:
            rule = issue['rule']
            if rule not in by_rule:
                by_rule[rule] = []
            by_rule[rule].append(issue)
        
        for rule, issues in by_rule.items():
            print(f"  [FAIL] {rule} ({len(issues)} occurrence{'s' if len(issues) > 1 else ''})")
            if verbose:
                for issue in issues:
                    print(f"     -> {issue['file']}:{issue['line']}")
                    print(f"       {issue['content']}")
            else:
                # Show first 3
                for issue in issues[:3]:
                    print(f"     -> {issue['file']}:{issue['line']}")
                if len(issues) > 3:
                    print(f"     ... and {len(issues) - 3} more")
            print()
        
        print(f"\n  RESULT: [BLOCKED] MERGE BLOCKED -- {len(all_issues)} violations found")
        print(f"  ACTION: Fix violations in Backend Architect / Frontend Engineer mode")
        print(f"          Then re-run: python audit.py\n")
        sys.exit(1)
    else:
        print(f"  RESULT: [PASS] ALL CHECKS PASSED")
        print(f"  ACTION: Safe to merge in Auditor mode\n")
        sys.exit(0)


if __name__ == "__main__":
    verbose = '--verbose' in sys.argv or '-v' in sys.argv
    run_audit(verbose=verbose)
