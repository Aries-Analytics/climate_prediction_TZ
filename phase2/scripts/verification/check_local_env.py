import sys
import importlib

required = [
    'sqlalchemy', 'pydantic', 'dotenv', 'pandas', 'numpy', 'requests'
]

print("Checking local environment...")
missing = []
for pkg in required:
    try:
        importlib.import_module(pkg)
        print(f"[OK] {pkg}")
    except ImportError:
        print(f"[MISSING] {pkg}")
        missing.append(pkg)

if missing:
    print(f"Missing packages: {missing}")
    sys.exit(1)
else:
    print("Local environment ready for test script.")
    sys.exit(0)
