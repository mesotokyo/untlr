#!/usr/bin/env python3
"""
posts_response_parser.py:
Parse Tumblr's `/v2/blog/{blog-identifier}/posts`API response

https://www.tumblr.com/docs/en/api/v2#posts--retrieve-published-posts
"""

from typing import Any
from collections.abc import Callable
import json
from datetime import datetime, UTC
from urllib.parse import quote
import sys
import os

import npf_renderer

from .date_parser import parse_timestamp

type Mapper = Callable[[Any], dict[str, Any]]
type PropMap = dict[str, str | Mapper | None]

def _map_props(props: dict[str, Any], mapping: PropMap) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, dest in mapping.items():
        if dest is None:
            continue
        if key in props:
            if callable(dest):
                r = dest(props[key])
                result.update(r)
            else:
                result[dest] = props[key]
    return result

_BLOG_THEME_MAPPING: PropMap = {
    "header_full_width": None,
    "header_full_height": None,
    "avatar_shape": "AvatarShape",
    "background_color": "BackGroundColor",
    "body_font": None,
    "header_bounds": None,
    "header_image": "HeaderImage",
    "header_image_focused": None,
    "header_image_poster": None,
    "header_image_scaled": None,
    "header_stretch": None,
    "link_color": None,
    "show_avatar": "ShowAvatar",
    "show_description": None,
    "show_header_image": None,
    "show_title": None,
    "title_color": "TitleColor",
    "title_font": "TitleFont",
    "title_font_weight": "TitleFontWeight"
}

def _theme_mapper(theme: dict[str, Any]) -> dict[str, Any]:
    return _map_props(theme, _BLOG_THEME_MAPPING)

def _avatar_mapper(avatar: list[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    sizes = [16, 24, 30, 40, 48, 64, 96, 128]
    for av in avatar:
        if not av["width"] in sizes:
            continue
        key = f"PortraitURL-{av["width"]}"
        result[key] = av["url"]
    return result

_BLOG_PROPERTY_MAPPING: PropMap = {
    "ask": "AskEnabled",
    "ask": None,
    "ask_anon": None,
    "ask_page_title": None,
    "asks_allow_media": None,
    "avatar": _avatar_mapper,
    "can_chat": None,
    "can_subscribe": None,
    "description": "Description",
    "is_nsfw": None,
    "likes": "LikeCount",
    "name": "Name",
    "posts": None,
    "share_likes": None,
    "share_replies": None,
    "submission_page_title": None,
    "subscribed": None,
    "theme_id": None,
    "theme": _theme_mapper,
    "title": "Title",
    "total_posts": None,
    "updated": None,
    "url": "BlogURL",
    "uuid": None,
}

_TAG_PREFIX = "/tagged/"

def _timestamp_mapper(timestamp: int) -> dict[str, Any]:
    return parse_timestamp(timestamp)

def _tag_mapper(tags: dict[str, Any]) -> dict[str, Any]:
    result = []
    for tag in tags:
        safe_tag = quote(tag)
        t = {
            "Tag": tag,
            "URLSafeTag": safe_tag,
            "TagURL": _TAG_PREFIX +  safe_tag,
            "TagURLChrono": _TAG_PREFIX +  safe_tag,
        }
        result.append(t)
    return { "Tags": result }
    
_POST_PROPERTY_MAPPING: PropMap = {
    "type": "PostType",
    "is_blocks_post_format": None,
    "blog_name": None,
    "blog": None,
    "id":  "PostID",
    "id_string": None,
    "is_blazed": None,
    "is_blaze_pending": None,
    "can_blaze": None,
    "post_url": "Permalink",
    "slug": None,
    "date": None,
    "timestamp": _timestamp_mapper,
    "state": None,
    "format": None,
    "reblog_key": None,
    "tags": _tag_mapper,
    "short_url": "ShortUrl",
    "summary": "PostSummary",
    "should_open_in_legacy": None,
    "recommended_source": None,
    "recommended_color": None,
    "note_count": "NoteCount",
    "title": "Title",
    "body": "Body",
    "body_abstruct": "",
    "reblog": "None",
    "trail": "None",
    "can_like": "None",
    "interactability_reblog": "None",
    "can_reblog": "None",
    "interactability_blaze": "None",
    "can_send_in_message": "None",
    "can_reply": "None",
    "display_avatar": "None"
}

_REBLOG_BUTTON = """<a href="{url}" class="reblog_button" style="display: block;{size}"><svg width="100%" height="100%" viewBox="0 0 21 21" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" fill="{color}"><path d="M5.01092527,5.99908429 L16.0088498,5.99908429 L16.136,9.508 L20.836,4.752 L16.136,0.083 L16.1360004,3.01110845 L2.09985349,3.01110845 C1.50585349,3.01110845 0.979248041,3.44726568 0.979248041,4.45007306 L0.979248041,10.9999998 L3.98376463,8.30993634 L3.98376463,6.89801007 C3.98376463,6.20867902 4.71892527,5.99908429 5.01092527,5.99908429 Z"></path><path d="M17.1420002,13.2800293 C17.1420002,13.5720293 17.022957,14.0490723 16.730957,14.0490723 L4.92919922,14.0490723 L4.92919922,11 L0.5,15.806 L4.92919922,20.5103758 L5.00469971,16.9990234 L18.9700928,16.9990234 C19.5640928,16.9990234 19.9453125,16.4010001 19.9453125,15.8060001 L19.9453125,9.5324707 L17.142,12.203"></path></svg></a>
"""

_LIKE_BUTTON = """
<div class="like_button interacted" data-post-id="{post_id}" data-blog-name="{blog_name}" id="like_button_{post_id}"><iframe id="like_iframe_{post_id}" src="https://assets.tumblr.com/assets/html/like_iframe.html?_v=c96f30edcf75919c3976e1403422560b#name=mesotokyo&amp;post_id={post_id}&amp;color={color}&amp;rk=Xj6ewlpx&amp;slug={slug}" scrolling="no" width="{size}" height="{size}" frameborder="0" class="like_toggle" allowtransparency="true" name="like_iframe_{post_id}"></iframe></div>
"""

class Blog:
    """Represents `blog` information"""
    raw_data: dict[str, Any]
    
    def __init__(self, d: dict[str, Any]):
        self.raw_data = d

    def to_variables(self) -> dict[str, Any]:
        """Convert Blog information to variables for renderer"""
        return _map_props(self.raw_data, _BLOG_PROPERTY_MAPPING)

    def get(self, key: str, default: Any = None) -> Any:
        return self.raw_data.get(key, default)

class Post:
    """Represents `post` information"""
    raw_data: dict[str, Any]
    post_id: str

    def __init__(self, d: dict[str, Any]):
        self.raw_data = d
        self.post_id = d.get("id_string", "")

    def _parse_text_post(self, format: str) -> dict[str, Any]:
        vars = _map_props(self.raw_data, _POST_PROPERTY_MAPPING)

        if format == "index":
            vars["Body"] = self.raw_data.get("body_abstract", "")
            vars["Date"] = True

        if vars["Tags"] and len(vars["Tags"]):
            vars["HasTags"] = True

        if "NoteCount" in vars:
            vars["NoteCountWithLabel"] = f'{vars["NoteCount"]} reactions'

        vars["ReblogButton"] = self._gen_reblog_btn()
        vars["LikeButton"] = self._gen_like_button()
        vars["RelatedPosts"] = []
        #vars.update(self._parse_npf())

        vars["Text"] = True
        return vars

    def _parse_npf_post(self, format: str) -> dict[str, Any]:
        vars = self._parse_text_post(format)
        c = self.raw_data["content"]
        l = self.raw_data["layout"]
        error, html = npf_renderer.format_npf(c, l)
        body: str = html
        if error:
            print(error)
            return vars

        if format == "index":
            # truncate <details> block
            i = body.find("<details ")
            body = body[0:i] + "</div>"

            # remove `loading="lazy"` attribute
            body = body.replace('''loading="lazy"''', "")

            # add read more block
            rel_url = f"/post/{self.raw_data["id_string"]}/{self.raw_data["slug"]}"
            more = f"""<p class="read_more_container">
            <a href="{rel_url}" class="read_more">read more</a></p>"""
            body += more

        if format == "post":
            pass

        #vars["NPF"] = self.raw_data.get("content")
        vars["Body"] = body
        vars["PostType"] = "text"
        vars["Title"] = ""
        
        return vars

    def to_variables(self, format: str = "") -> dict[str, Any]:
        """Convert Blog information to variables for renderer"""
        vars: dict[str, Any] = {}
        if self.raw_data.get("type") == "text":
            vars = self._parse_text_post(format)
        elif self.raw_data.get("type") == "blocks":
            vars = self._parse_npf_post(format)

        return vars

    def _gen_reblog_btn(self) -> str:
        post_id = self.raw_data.get("id_string")
        if post_id is None:
            return ""

        data = {
            "url": f"https://www.tumblr.com/reblog/mesotokyo/{post_id}/Xj6ewlpx",
            "size": "width:{size}px;height:{size}px;",
            "color": "{color}"
        }        
        return _REBLOG_BUTTON.format_map(data)

    def _gen_like_button(self) -> str:
        post_id = self.raw_data.get("id_string")
        if post_id is None:
            return ""
        data = {
            "post_id": post_id,
            "blog_name": self.raw_data.get("blog_name", ""),
            "color": "{color}",
            "slug": self.raw_data.get("slug", ""),
            "size": "{size}",
        }
        return _LIKE_BUTTON.format_map(data)
        
class PostsResponse:
    """Represents `/v2/blog/{blog-identifier}/posts`API response"""
    raw_data: dict[str, Any]
    blog: Blog
    posts: list[Post]
    
    def __init__(self, d: dict[str, Any]):
        self.raw_data = d
        self._from_dict(d)

    def _from_dict(self, d: dict[str, Any]):
        resp = d.get("response", {})
        self.blog = Blog(resp.get("blog", {}))
        self.posts = []
        for post in resp.get("posts", []):
            self.posts.append(Post(post))
                              
if __name__ == "__main__":
    with open("posts.json", "r") as fp:
        data = json.load(fp)
    pr = PostsResponse(data)
    print(json.dumps(pr.blog.to_variables(), indent=2, ensure_ascii=False))
    for post in pr.posts:
        print(json.dumps(post.to_variables(), indent=2, ensure_ascii=False))
        
    
