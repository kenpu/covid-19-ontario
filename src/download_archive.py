import requests
import subprocess
from pprint import pprint
import time
import os

url = "https://www.ontario.ca/page/2019-novel-coronavirus"

def list_snapshots():
    resp = requests.get(url="http://web.archive.org/cdx/search/cdx",
            params=dict(url=url, output='json'))
    data = resp.json()
    columns = data[0]
    return [dict(zip(columns, row)) for row in reversed(data[1:])]

def wayback_url(t):
    return "https://web.archive.org/web/%s/%s" % (t, url)

def get_snapshot(t, _url=None):
    filename = "%s.html" % t
    if os.path.exists(filename) and os.path.getsize(filename) > 0:
        raise Exception("Skipping %s" % t)

    if not _url:
        _url = wayback_url(t)
    cmd = ['google-chrome',
            '--headless', 
            '--disable-gpu', 
            '--run-all-compositor-stages-before-draw', 
            '--dump-dom', 
            '--virtual-time-budget=10000',
            _url
            ]
            
    p = subprocess.run(cmd, stdout=subprocess.PIPE)
    
    with open(filename, 'w') as f:
        bytes = p.stdout
        f.write(bytes.decode('utf-8'))

def download(limit=10):
    os.chdir('./wayback_dumps')
    snapshots = list_snapshots()
    if limit:
        snapshots = snapshots[:limit]
    for (i,data) in enumerate(snapshots):
        try:
            start = time.time()
            t = data['timestamp']
            get_snapshot(t)
            print("[%d] [%.2f seconds] %s.html" % (i, time.time()-start, t))
        except Exception as e:
            print(str(e))

download()