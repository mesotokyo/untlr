from typing import Any
import re
import json
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

from .posts_response import PostsResponse, Post
from .tumblr_theme_parser import escape_identifier
from .tumblr_client import TumblrClient

class CachedClient:
    cache_enabled: bool
    cache_dir: Path | None

    def __init__(self, config):
        self.config = config

        try:
            self.cache_enabled = config["system"]["cache"]
            self.cache_dir = Path(config["system"]["cache_dir"])
        except KeyError:
            self.cache_enabled = False
            self.cache_dir = None

        self._ensure_cache_dir()

    def _get_from_cache(self, cache_name: str) -> dict[str, Any]:
        if self.cache_dir is None:
            msg = "cache_dir not set"
            raise FileNotFoundError(msg)
        fn = self.cache_dir / f"{cache_name}.json"
        with fn.open("rt", encoding="utf-8") as fp:
            data = json.load(fp)
        return data

    def _ensure_cache_dir(self):
        if not self.cache_dir:
            msg = "cache_dir is not set"
            raise FileNotFoundError(msg)
        if not self.cache_dir.exists():
            self.cache_dir.mkdir()
            return
        if self.cache_dir.is_dir():
            return
        msg = f'"{self.cache_dir}" is not a directory'
        raise NotADirectoryError(msg)

    def _save_cache(self, cache_name: str, data: dict[str, Any]):
        if self.cache_dir is None:
            msg = "cache_dir not set"
            raise FileNotFoundError(msg)
        fn = self.cache_dir / f"{cache_name}.json"
        with fn.open("wt", encoding="utf-8") as fp:
            json.dump(data, fp, indent=2)
        
    def get_posts(self, offset: int, limit: int) -> dict[str, Any]:
        fname = f"posts_{offset}_{limit}"
        if self.cache_enabled:
            try:
                data = self._get_from_cache(fname)
                return data
            except FileNotFoundError as e:
                logger.info(f"{e}: cache is not available")

        c = TumblrClient(self.config)
        data = c.get_recent_posts(limit, offset)

        if self.cache_enabled:
            try:
                self._save_cache(fname, data)
            except FileNotFoundError as e:
                logger.info(f"{e}: cache is not available")
        return data

    def get_post(self, post_id: int) -> dict[str, Any]:
        fname = f"post_{post_id}"
        if self.cache_enabled:
            try:
                data = self._get_from_cache(fname)
                return data
            except FileNotFoundError as e:
                logger.info(f"{e}: cache is not available")

        c = TumblrClient(self.config)
        data = c.get_post(post_id)

        if self.cache_enabled:
            try:
                self._save_cache(fname, data)
            except FileNotFoundError as e:
                logger.info(f"{e}: cache is not available")
        return data
        

class VariableManager:
    """manage variables"""
    #pr: PostsResponse
    config: dict[str, Any]
    post_per_page: int
    client: CachedClient
    
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.post_per_page = config["system"].get("post_per_page", 10)
        self.client = CachedClient(config)

    def _load_additional_content(self, vars: dict[str, Any], page_type: str):
        section = f"{page_type}_page"
        if not section in self.config:
            return

        cfg = self.config[section]

        for c_type in ("head_prepend",):
            try:
                fn = cfg[c_type]
            except KeyError:
                continue

            with open(fn, encoding="utf-8") as fp:
                content = fp.read()

            key = f"_{c_type}_"
            vars[key]  = content

    def _set_default_values(self, vars: dict[str, Any]):
        # import default values with escaping
        def_vars = self.config["default_values"]
        for k in def_vars:
            key = escape_identifier(k)
            vars[key]  = def_vars[k]
            
    def generate_for_path(self, path: str) -> dict[str, Any]:
        vars: dict[str, Any] = {}

        if path == "/":
            self._generate_for_index(vars)
            self._set_default_values(vars)
            self._load_additional_content(vars, "index")

        if path.startswith("/page/"):
            m = re.match(r"/page/(\d+)/?", path)
            if m:
                page_num = m.group(1)
                self._generate_for_page(page_num, vars)
            self._set_default_values(vars)
            self._load_additional_content(vars, "post")
            
        if path.startswith("/post/"):
            m = re.match(r"/post/(\d+)/?", path)
            if m:
                post_id = m.group(1)
                self._generate_for_post(post_id, vars)
            self._set_default_values(vars)
            self._load_additional_content(vars, "post")

        return vars
    
    def _generate_for_index(self, vars: dict[str, Any]):
        self._generate_for_page("1", vars)
       
    def _generate_for_page(self, page_num: str, vars: dict[str, Any]):
        try:
            page = int(page_num)
        except ValueError:
            page = 0
        if page < 1:
            logger.error(f"invalid page number: {page_num}")
            return 

        offset = self.post_per_page * (page-1)
        data = self.client.get_posts(offset, self.post_per_page)
        pr = PostsResponse(data)

        vars.update(pr.blog.to_variables())
        d = {
            "Posts": [p.to_variables("index") for p in pr.posts],
            "IndexPage": True,
            "Pagination": True,
            "NextPage":  f"/page/{page+1}",
            "CurrentPage": page,
            "TotalPages": "28",
        }
        if page > 2:
            d["PreviousPage"] = f"/page/{page-1}"

        vars.update(d)

    def _generate_for_post(self, post_id: str, vars: dict[str, Any]):
        try:
            the_id = int(post_id)
        except ValueError:
            the_id = 0

        if the_id == 0:
            logger.error(f"invalid page number: {post_id}")
            return 

        c = TumblrClient(self.config)
        data = self.client.get_post(the_id)
        pr = PostsResponse(data)
        vars["Posts"] = [pr.posts[0].to_variables("post")]
        vars["IndexPage"] = False
    
