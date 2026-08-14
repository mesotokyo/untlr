import urllib.parse
import urllib.request
import json
from typing import Any

API_HOST = "https://api.tumblr.com"
BLOG_ID = "mesotokyo.tumblr.com"
API_PATH = f"/v2/blog/{BLOG_ID}/posts"
API_KEY = "9jzeTeOst7drVpT11bfcBXDQgC8p9BjbpSzGdzZhc9nI7k9sJt"

def get_recent_posts() -> bytes|dict[str, Any]:
    param: dict[str, str|int] = {
        "api_key": API_KEY,
        "limit": 10,
        #"npf": True
    }
    qs = urllib.parse.urlencode(param)
    url: str = f"{API_HOST}{API_PATH}?{qs}"

    #print(url)
    with urllib.request.urlopen(url) as req:
        ctype: str|None = req.headers.get("Content-Type")
        if ctype is not None and ctype.startswith("application/json"):
            raw_result = req.read()
            result = json.loads(raw_result)
            return result

    return req.read()
    
if __name__ == "__main__":
    d = get_recent_posts()
    if isinstance(d, dict):
        print(json.dumps(d, ensure_ascii=False, indent=2))
    else:
        print(d)
