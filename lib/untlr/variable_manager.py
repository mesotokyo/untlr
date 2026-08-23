from typing import Any
import re
import json
from pathlib import Path
import logging
import math
from urllib.error import HTTPError
logger = logging.getLogger(__name__)

from .posts_response import PostsResponse
from .tumblr_theme_parser import escape_identifier
from .tumblr_client import TumblrClient

class NotFoundError(Exception):
    pass

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
    _partials: dict[str, dict[str, str]]
    
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.post_per_page = config["system"].get("post_per_page", 10)
        self.client = CachedClient(config)
        self._load_partials()

    def _load_partials(self):
        self._partials = {}
        try:
            base_dir = Path(self.config["theme_dir"])
        except KeyError:
            base_dir = Path(".")

        for page_type in ("index", "post"):
            logger.info(f"find partials for {page_type}...")
            self._partials[page_type] = {}
            section = f"{page_type}_page"
            try:
                conf = self.config[section]
            except KeyError:
                continue
            for tag in ("html", "head", "body"):
                for k in (f"before_{tag}", f"after_{tag}", f"{tag}_start", f"{tag}_end"):
                    try:
                        fname = base_dir / str(conf[k])
                    except KeyError:
                        continue
                    try:
                        with fname.open(encoding="utf-8") as fp:
                            logger.info(f"partial {fname} for {k} found")
                            content = fp.read()
                    except IOError:
                        continue
                    self._partials[page_type][k] = f"<!-- {k} -->\n{content}<!-- end of {k} -->\n"

    def _set_default_values(self, vars: dict[str, Any]):
        # import default values with escaping
        def_vars = self.config["default_values"]
        for k in def_vars:
            key = escape_identifier(k)
            vars[key]  = def_vars[k]

    def _load_additional_content(self, vars: dict[str, Any], page_type: str):
        if page_type == "page":
            t = "index"
        else:
            t = page_type
        try:
            d = self._partials[t]
        except KeyError:
            logger.info(f"partials for {t} do not found")
            return
        logger.debug(f"used partials: {d.keys()}")
        vars.update(d)
        
    def generate_for_path(self, path: str) -> dict[str, Any]:
        vars: dict[str, Any] = {}

        if path == "/":
            self._generate_for_index(vars)
            self._set_default_values(vars)
            self._load_additional_content(vars, "page")

        if path.startswith("/page/"):
            m = re.match(r"/page/(\d+)/?", path)
            if m:
                page_num = m.group(1)
                self._generate_for_page(page_num, vars)
            self._set_default_values(vars)
            self._load_additional_content(vars, "page")
            
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
            msg = f"invalid page number: {page_num}"
            logger.error(msg)
            raise NotFoundError(msg)

        offset = self.post_per_page * (page-1)
        data = self.client.get_posts(offset, self.post_per_page)
        pr = PostsResponse(data)
        # posts
        posts = pr.blog.get("posts")
        
        vars.update(pr.blog.to_variables())
        d = {
            "Posts": [p.to_variables("page") for p in pr.posts],
            "IndexPage": True,
            "Pagination": True,
            "NextPage":  f"/page/{page+1}",
            "CurrentPage": page,
            "TotalPages": math.ceil(posts / self.post_per_page),
            #"RelatedPosts": [],
        }
        if page > 1:
            d["PreviousPage"] = f"/page/{page-1}"

        vars.update(d)

    def _generate_for_post(self, post_id: str, vars: dict[str, Any]):
        try:
            the_id = int(post_id)
        except ValueError:
            the_id = 0

        if the_id == 0:
            msg = f"invalid page ID: {post_id}"
            logger.error(msg)
            raise NotFoundError(msg)

        c = TumblrClient(self.config)
        data = self.client.get_post(the_id)
        
        pr = PostsResponse(data)
        vars["Posts"] = [pr.posts[0].to_variables("post")]
        vars["IndexPage"] = False
    
