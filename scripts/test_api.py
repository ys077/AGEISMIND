import urllib.request
import json
try:
    res = urllib.request.urlopen('http://localhost:8000/api/risk-heatmap/CC1001')
    d = json.loads(res.read())
    print('Top 10:')
    for c in d['candidates'][:10]:
        print(f"Rank {c['rank']}: {c['probability']}")
except Exception as e:
    print(f"Error: {e}")
