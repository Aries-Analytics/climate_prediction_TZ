"""
Test script to verify climate API endpoints are working
"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

# First, login to get a token
print("1. Logging in...")
login_response = requests.post(
    f"{BASE_URL}/auth/login",
    data={
        "username": "admin",
        "password": "admin123"
    }
)

if login_response.status_code == 200:
    token = login_response.json()["access_token"]
    print(f"✓ Login successful, got token")
else:
    print(f"✗ Login failed: {login_response.status_code}")
    print(login_response.text)
    exit(1)

# Test climate timeseries endpoint
print("\n2. Testing climate timeseries endpoint...")
headers = {"Authorization": f"Bearer {token}"}

for variable in ['temperature', 'rainfall', 'ndvi', 'enso', 'iod']:
    print(f"\n   Testing variable: {variable}")
    response = requests.get(
        f"{BASE_URL}/climate/timeseries",
        params={"variable": variable},
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ {variable}: {len(data.get('data', []))} data points")
        if data.get('data'):
            first_point = data['data'][0]
            last_point = data['data'][-1]
            print(f"     Date range: {first_point['date']} to {last_point['date']}")
    else:
        print(f"   ✗ {variable} failed: {response.status_code}")
        print(f"     Error: {response.text}")

# Test anomalies endpoint
print("\n3. Testing anomalies endpoint...")
response = requests.get(
    f"{BASE_URL}/climate/anomalies",
    params={"variable": "rainfall"},
    headers=headers
)

if response.status_code == 200:
    anomalies = response.json()
    print(f"✓ Anomalies: {len(anomalies)} detected")
else:
    print(f"✗ Anomalies failed: {response.status_code}")
    print(response.text)

# Test correlations endpoint
print("\n4. Testing correlations endpoint...")
response = requests.get(
    f"{BASE_URL}/climate/correlations",
    params={"variables": ["temperature", "rainfall", "ndvi", "enso", "iod"]},
    headers=headers
)

if response.status_code == 200:
    corr_data = response.json()
    print(f"✓ Correlations: {len(corr_data.get('variables', []))} variables")
    print(f"  Matrix size: {len(corr_data.get('matrix', []))}x{len(corr_data.get('matrix', [[]])[0]) if corr_data.get('matrix') else 0}")
else:
    print(f"✗ Correlations failed: {response.status_code}")
    print(response.text)

print("\n" + "="*50)
print("Test complete!")
