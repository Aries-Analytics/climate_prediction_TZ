import sys
import os
print("Starting diagnostic...", flush=True)

try:
    print("Importing ocean...", flush=True)
    from modules.ingestion.ocean_indices_ingestion import fetch_ocean_indices_data
    print("Imported ocean.", flush=True)
except Exception as e:
    print(f"Ocean failed: {e}", flush=True)

try:
    print("Importing logger...", flush=True)
    from utils.logger import get_logger
    print("Imported logger.", flush=True)
except Exception as e:
    print(f"Logger failed: {e}", flush=True)

try:
    print("Importing orchestrator...", flush=True)
    import modules.ingestion.orchestrator as orch
    print("Imported orchestrator.", flush=True)
except Exception as e:
    print(f"Orchestrator import failed: {e}", flush=True)

print("Done.", flush=True)
