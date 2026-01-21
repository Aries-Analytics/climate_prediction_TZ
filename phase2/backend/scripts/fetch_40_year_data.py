"""
Fetch 40 Years of Historical Climate Data (1985-2025)

This script fetches data from all 5 sources for the full 40-year period:
1. CHIRPS (Rainfall) - 1985-2025
2. NASA POWER (Temperature, etc.) - 1985-2025
3. ERA5 (Reanalysis) - 1985-2025
4. NDVI (Hybrid AVHRR+MODIS) - 1985-2025
5. Ocean Indices (ENSO/IOD) - 1985-2025

Expected result: ~480 monthly samples (40 years × 12 months)
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import time
from datetime import 