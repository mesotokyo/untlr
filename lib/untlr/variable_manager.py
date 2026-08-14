from typing import Any
import re
import json

from .posts_response import PostsResponse
from .tumblr_theme_parser import escape_identifier

class VariableManager:
    """manage variables"""
    pr: PostsResponse
    config: dict[str, Any]
    
    def __init__(self, config: dict[str, Any]):
        #source = "posts.json"
        #source = "post_npf.json"
        self.config = config

        post_cache = f"posts{config["system"]["cache_file_postfix"]}"
        with open(post_cache, "rt", encoding="utf-8") as fp:
            data = json.load(fp)
        self.pr = PostsResponse(data)

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
    
    def generate_for_path(self, path: str) -> dict[str, Any]:
        vars: dict[str, Any] = {}
        vars.update(self.pr.blog.to_variables())

        # import default values with escaping
        def_vars = self.config["default_values"]
        for k in def_vars:
            key = escape_identifier(k)
            vars[key]  = def_vars[k]
        #vars.update(self.config["default_values"])

        if path == "/":
            self._generate_for_index(vars)
            self._load_additional_content(vars, "index")
                
        if path.startswith("/post/"):
            m = re.match(r"/post/(\d+)/?", path)
            if m:
                post_id = m.group(1)
                self._generate_for_post(post_id, vars)
            self._load_additional_content(vars, "post")

        return vars
        
    def _generate_for_index(self, vars: dict[str, Any]):
        vars["Posts"] = [p.to_variables("index") for p in self.pr.posts]
        vars["IndexPage"] = True

    def _generate_for_post(self, post_id: str, vars: dict[str, Any]):
        # find post
        for p in self.pr.posts:
            if p.post_id == post_id:
                vars["Posts"] = [p.to_variables("post")]
                break
        vars["IndexPage"] = False
    
