
import requests
import sys

URLS = [
    "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt",
    "https://psl.noaa.gov/gcos_wgsp/Timeseries/Data/dmi.had.long.data",
    "https://google.com"  # Control
]

def check_connectivity():
    print("Testing network connectivity...")
    for url in URLS:
        print(f"\nChecking {url}...")
        try:
            response = requests.get(url, timeout=10)
            print(f"✅ Status Code: {response.status_code}")
            print(f"   Headers: {response.headers.get('content-type', 'unknown')}")
        except requests.exceptions.SSLError as e:
            print(f"❌ SSL Error: {e}")
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Connection Error: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_connectivity()
