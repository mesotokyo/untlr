import urllib.parse
import urllib.request
import json
from typing import Any
import logging

logger = logging.getLogger(__name__)

type Config = dict[str, Any]
class InvalidResponseError(Exception):
    pass

class TumblrClient:
    _api_key: str
    _blog_id : str
    _api_path: str
    
    def __init__(self, config: Config):
        try:
            self._api_key = config["api"]["key"]
            host = config["api"]["host"]
            blog_id = config["blog"]["id"]
        except KeyError as e:
            msg = f"config key not found: {e}"
            raise KeyError(msg)
        self._api_path = f"{host}/v2/blog/{blog_id}"

    def get_post(self, post_id: int) -> dict[str, Any]:
        param: dict[str, str|int] = {
            "api_key": self._api_key,
            "id": post_id,
            "npf": True
        }
        qs = urllib.parse.urlencode(param)
        url: str = f"{self._api_path}/posts?{qs}"
        return self._get_request(url)

    def get_recent_posts(self, limit: int = 10, offset: int = 0) -> dict[str, Any]:
        param: dict[str, str|int] = {
            "api_key": self._api_key,
            "limit": limit,
            "offset": offset,
            "npf": True
        }
        qs = urllib.parse.urlencode(param)
        url: str = f"{self._api_path}/posts?{qs}"
        return self._get_request(url)

    def _get_request(self, url: str) -> dict[str, Any]:
        logger.debug(f'request url: {url}')
        with urllib.request.urlopen(url) as req:
            ctype: str|None = req.headers.get("Content-Type")
            raw_result = req.read()
            if ctype is not None and ctype.startswith("application/json"):
                result = json.loads(raw_result)
                return result

        msg = f"invalid response: {raw_result}"
        raise InvalidResponseError(msg)
    

if __name__ == "__main__":
    config = {
        "api": {
            "key": "9jzeTeOst7drVpT11bfcBXDQgC8p9BjbpSzGdzZhc9nI7k9sJt",
            "host": "https://api.tumblr.com"
        },
        "blog": {
            "id": "mesotokyo.tumblr.com"
        }
    }
    c = TumblrClient(config)
    d = c.get_recent_posts()
    if isinstance(d, dict):
        print(json.dumps(d, ensure_ascii=False, indent=2))
    else:
        print(d)
