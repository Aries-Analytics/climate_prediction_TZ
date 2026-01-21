import requests

# Login
response = requests.post('http://localhost:8000/api/auth/login', json={
    'username': 'admin',
    'password': 'admin123'
})
token = response.json()['access_token']

# Get temperature anomalies
headers = {'Authorization': f'Bearer {token}'}
anomalies = requests.get(
    'http://localhost:8000/api/climate/anomalies?variable=temperature&threshold=2.0',
    headers=headers
).json()

print(f'Total anomalies returned: {len(anomalies)}')
print(f'Unique dates: {len(set(a["date"] for a in anomalies))}')
print(f'Unique locations: {len(set(a.get("location", "") for a in anomalies))}')

# Show sample
print('\nFirst 10 anomalies:')
for i, a in enumerate(anomalies[:10]):
    print(f'{i+1}. {a["date"]} - {a.get("location", "N/A")}: {a["value"]:.2f} (dev: {a["deviation"]:.2f})')

# Group by date
from collections import Counter
date_counts = Counter(a["date"] for a in anomalies)
print(f'\nAnomalies per unique date (max 5 shown):')
for date, count in date_counts.most_common(5):
    print(f'  {date}: {count} occurrences')
