import urllib.request
import ssl
import sys

ctx = ssl._create_unverified_context()
for i in range(1, 7):
    url = f"http://www.aueb.gr/users/ion/data/enron-spam/preprocessed/enron{i}.tar.gz"
    try:
        req = urllib.request.urlopen(url, context=ctx, timeout=10)
        size_mb = int(req.headers.get("Content-Length", 0)) / (1024 * 1024)
        print(f"enron{i}: HTTP {req.status}, size={size_mb:.2f} MB")
    except Exception as e:
        print(f"enron{i} error: {e}")

