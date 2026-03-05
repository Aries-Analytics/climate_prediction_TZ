"""
Load HewaSense Phase-Based Forecast Data for Dashboard
Populates seasonal forecasts with phase-based model comparison

Run after backend is up:
    python scripts/load_hewasense_forecast.py
"""

import requests
import json
from datetime import datetime, timezone
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

API_BASE = "http://localhost:8000"


def get_auth_token():
    """Login and get authentication token"""
    response = requests.post(
        f"{API_BASE}/api/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed: {response.text}")
        return None


def load_hewasense_forecast_data(token):
    """Load HewaSense phase-based forecast for Morogoro 2026"""
    print("\n" + "=" * 60)
    print("Loading HewaSense Phase-Based Forecast Data")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # HewaSense forecast data for Morogoro Mar-Jun 2026
    # Phase-based coverage model (production)
    forecast_data = {
        "location": "Morogoro",
        "season": "Mar-Jun 2026",
        "predicted_rainfall_mm": 385,
        "drought_probability": 0.35,
        "flood_probability": 0.08,
        "expected_payout_per_farmer": 24.50,
        "risk_level": "MEDIUM",
        
        "phase_breakdown": [
            {
                "phase_name": "Germination",
                "duration_days": 21,
                "rainfall_mm": 58,
                "drought_trigger_mm": 40,
                "drought_payout": 0,
                "flood_payout": 0,
                "total_payout": 0,
                "status": "normal"
            },
            {
                "phase_name": "Vegetative",
                "duration_days": 29,
                "rainfall_mm": 92,
                "drought_trigger_mm": 70,
                "drought_payout": 0,
                "flood_payout": 0,
                "total_payout": 0,
                "status": "normal"
            },
            {
                "phase_name": "Flowering",
                "duration_days": 40,
                "rainfall_mm": 72,
                "drought_trigger_mm": 80,
                "drought_payout": 28,
                "flood_payout": 0,
                "total_payout": 28,
                "status": "drought_risk"
            },
            {
                "phase_name": "Ripening",
                "duration_days": 55,
                "rainfall_mm": 93,
                "drought_trigger_mm": 60,
                "drought_payout": 0,
                "flood_payout": 0,
                "total_payout": 0,
                "status": "normal"
            }
        ]
    }
    
    # Store in database or file system
    # For now, save to JSON file for dashboard to read
    output_file = project_root / 'outputs' / 'dashboard' / 'hewasense_forecast.json'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(forecast_data, f, indent=2)
    
    print(f"[OK] Saved forecast to: {output_file}")
    print(f"\nForecast Summary:")
    print(f"  Location: {forecast_data['location']}")
    print(f"  Season: {forecast_data['season']}")
    print(f"  Predicted Rainfall: {forecast_data['predicted_rainfall_mm']}mm")
    print(f"  Drought Risk: {forecast_data['drought_probability']*100:.0f}%")
    print(f"  Risk Level: {forecast_data['risk_level']}")
    print(f"\nPhase-Based Coverage (Production Model):")
    for phase in forecast_data['phase_breakdown']:
        status_icon = "⚠️" if "risk" in phase['status'] else "✅"
        print(f"  {status_icon} {phase['phase_name']}: {phase['rainfall_mm']}mm → ${phase['total_payout']}")
    
    return forecast_data


def main():
    """Main function"""
    print("=" * 60)
    print("HEWASENSE PHASE-BASED FORECAST LOADER")
    print("=" * 60)
    print(f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get auth token
    print("\nAuthenticating...")
    token = get_auth_token()
    if not token:
        print("[FAIL] Failed to authenticate")
        return
    
    print("[OK] Authenticated successfully")
    
    try:
        # Load forecast data
        forecast_data = load_hewasense_forecast_data(token)
        
        print("\n" + "=" * 60)
        print("HEWASENSE FORECAST LOADED!")
        print("=" * 60)
        print("\n✅ Dashboard can now display:")
        print("   - Phase-based model comparison")
        print("   - 4-phase breakdown visualization")
        print("   - Risk assessment by growth stage")
        print("\n📊 View at: http://localhost:3000/risk-management")
        
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
