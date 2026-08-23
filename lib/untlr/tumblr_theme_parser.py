"""
Tumblr custom theme parser
"""

import re
import sys
from html.parser import HTMLParser
from typing import Any
import logging
logger = logging.getLogger(__name__)

from .keywords import KW_ITERATOR, KW_VARS, KW_NEGATIVE_CONDITIONS

_REX_PLACEHOLDER = re.compile(r'{\s*(?P<is_end>/)?\s*(?P<prefix>[A-Za-z]+:)?(?P<rest>[^{}]+?)\s*}')
_REX_LOCALIZE = re.compile(r"[A-Za-z][A-Za-z0-9 .-]+")
_ESCAPE_TABLE = str.maketrans(":- ", "___")
_THEME_OPTIONS = set(("color", "font", "select", "if", "select", "text", "image"))
_FILTERS = ("Plaintext", "JS", "JSPlaintext", "URLEncoded", "RGB")


def escape_identifier(s: str) -> str:
    """escape variable name to match Python's identifier rule"""
    return s.translate(_ESCAPE_TABLE)

def _to_camel_case(text:str) -> str:
    """convert snake_case like string to CamelCase string"""
    words:list[str] = re.split(r'[-_\s]+', text)
    return ''.join(word[0].upper() + word[1:] for word in words)

class TumblrThemeParser(HTMLParser):
    """Parse Tumbler Custom HTML theme and convert to Jinja Template"""
    _keywords: set
    _iterative_keywords: dict[str, str]
    _output: list[str]
    _result: str

    _custom_vars: dict[str, str | bool]
    #_custom_blocks: dict[str, str | bool]
    _iterate_block_stack: list[str]

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._keywords = set(KW_VARS)
        self._iterative_keywords = KW_ITERATOR
        self._output= []

        self._custom_vars = {}
        self._custom_blocks = {}
        self._iterate_block_stack = []
        self._result = ""

    def get_custom_vars(self) -> dict[str, Any]:
        result = {}
        for kw in self._custom_vars:
            v = self._custom_vars[kw]
            kw = escape_identifier(kw)
            result[kw] =  v
        for k in self._custom_blocks:
            if k.startswith("block:"):
                name = k[6:]
                result[name] = self._custom_blocks[k]
        return result

    def _localize_key(self, key: str) -> str:
        # {lang:...} is for i18n.
        # remove brace and `lang:`
        return key.removeprefix("lang:")

    def _replace_brace(self, text: str) -> str:
        def replacer(match: re.Match[str]) -> str:
            """function for re.sub to relace `{ ... }` block (tag) to `{{ ... }}`"""
            #print(match.group(0))
            prefix = match["prefix"]
            unprefix_keyword = match["rest"]
            if prefix:
                prefix = prefix.lower()
                keyword = prefix + unprefix_keyword
            else:
                keyword = unprefix_keyword

            # check if this is end tag
            if match["is_end"] is not None:
                if prefix is None:
                    # this case is like `{/hoge}`, but this form is not in specification...
                    return match.group(0)
                if keyword in self._iterative_keywords:
                    return f"{{% endimportprops %}}{{% endfor %}}"
                if keyword in self._keywords:
                    return f"{{% endif %}}"
                if keyword in KW_NEGATIVE_CONDITIONS:
                    return f"{{% endif %}}"
                if unprefix_keyword.startswith("IfNot"):
                    kw = unprefix_keyword[5:]
                elif unprefix_keyword.startswith("If"):
                    kw = unprefix_keyword[2:]
                else:
                    kw = unprefix_keyword
                if kw in self._keywords:
                    return f"{{% endif %}}"
                return match.group(0)

            if prefix == "lang:":
                # special case: `lang:` is used for localization.
                # see https://help.tumblr.com/knowledge-base/localizing-themes/
                if _REX_LOCALIZE.match(keyword):
                    return f'{{{{ localize("{unprefix_keyword}") }}}}'
                return match.group(0)

            if prefix is not None and prefix != "block:":
                # this tag uses theme option.
                if keyword in self._keywords:
                    var_name = escape_identifier(keyword)
                    return f"{{{{ {var_name} }}}}"
                return match.group(0)

            # if prefix is None or "block:", the tag may have argument(s).
            items = re.split(r"\s+", unprefix_keyword)
            unprefix_keyword = items.pop(0)
            var_name = escape_identifier(unprefix_keyword)
            argument = ", ".join([f"'{x}'" for x in items])

            if prefix is None:
                # check filters
                kw_pre = ""
                kw_post = ""
                for filter in _FILTERS:
                    if var_name.startswith(filter):
                        var_name = var_name[len(filter):]
                        unprefix_keyword = unprefix_keyword[len(filter):]
                        kw_pre = f'transform("{filter}", '
                        kw_post = ")"
                        break
                if not unprefix_keyword in self._keywords:
                    return match.group(0)
                if len(argument):
                    var_name = f'proc_arguments("{var_name}", {var_name}, ({argument},))'
                return f"{{{{ {kw_pre}{var_name}{kw_post} }}}}"

            # process block tag (prefix == "block:")
            # assumes: block tag does not have prefix to transform
            keyword = prefix + unprefix_keyword
            if keyword in self._iterative_keywords:
                k = self._iterative_keywords[keyword]
                return f"{{% for {k} in {var_name} %}}{{% importprops {k} %}}"

            if keyword in self._keywords \
               or unprefix_keyword in self._keywords:
                return f"{{% if {var_name} %}}"
                
            # tag is not iterative. in this case, we need consider `If` and `IfNot` prefix.
            if var_name.startswith("IfNot"):
                kw = var_name[5:]
                pre_kw = "not "
            elif var_name.startswith("If"):
                kw = var_name[2:]
                pre_kw = ""
            else:
                kw = var_name
                pre_kw = ""

            if kw in self._keywords:
                return f"{{% if {pre_kw}{kw} %}}"

            if keyword in KW_NEGATIVE_CONDITIONS:
                # negative conditions are starting with "No"
                kw = var_name[2:]
                return f"{{% if not {kw} %}}"

            return match.group(0)

        return _REX_PLACEHOLDER.sub(replacer, text)

    def _parse_custom_meta_tag(self, tag: str, attrs: list[tuple[str, str]]) -> bool:
        """Parse Tumblr's custom meta tag and extract them.

        Tumblr's custom theme can use meta tag to define custom variables and
        default value of them.
        ( https://www.tumblr.com/docs/ja/custom_themes#theme-options )
        This method parse these custom meta tag, and save it's default value
        with variable name.

        This method returns True is this meta tag is custom meta tag.
        Otherwise, False.
        """
        attr = dict(attrs)

        # check if both "name" and "content" attribute exist
        if not "name" in attr or not "content" in attr:
            return False

        # check if value of "name" attribute is tumbler custom tag format
        m = re.match(r"(\w+):", attr["name"])
        if not m or not m.group(1) in _THEME_OPTIONS:
            return False
        opt_type = m.group(1)
        opt_name = attr["name"]

        # check if content value exists
        if len(attr["content"]):
            opt_value = self._replace_brace(attr["content"])
        else:
            opt_value = ""

        # in case of `<meta name="if:....">`, only refered as `{block:If...}` format
        if opt_type == "if":
            k = _to_camel_case(opt_name[3:])
            self._keywords.add(k)
            self._custom_vars[k] = (opt_value == "1")
        else:
            self._custom_vars[opt_name] = opt_value
            self._keywords.add(opt_name)
            k = _to_camel_case(opt_name[len(opt_type)+1:])
            self._keywords.add(k)
            self._custom_vars[k] = (len(opt_value) > 0)
        return True

    def handle_starttag(self, tag: str, attrs: list[tuple]):
        if tag == "meta":
            if self._parse_custom_meta_tag(tag, attrs):
                return
        attr_list: list[str] = [tag, ]
        for (name, value) in attrs:
            if not value:
                attr_list.append(name)
                continue
            value = self._replace_brace(value)
            if '"' in value:
                attr_list.append(f"{name}='{value}'")
            else:
                attr_list.append(f'{name}="{value}"')
        attrs_str = " ".join(attr_list)

        # insert tags to insert special codes to specific position
        before = ""
        after = ""
        if tag in ("html", "head", "body"):
            before = f"before_{tag}"
            after = f"{tag}_start"
            
        if before:
            self._output.append(f"{{{{- {before} -}}}}")
        self._output.append(f'<{attrs_str}>')
        if after:
            self._output.append(f"{{{{- {after} -}}}}")

    def handle_startendtag(self, tag: str, attrs: list[tuple]):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str):
        # insert tags to insert special codes to specific position
        before = ""
        after = ""
        before = ""
        after = ""
        if tag in ("html", "head", "body"):
            before = f"{tag}_end"
            after = f"after_{tag}"

        if before:
            self._output.append(f"{{{{- {before} -}}}}")
        self._output.append(f'</{tag}>')
        if after:
            self._output.append(f"{{{{- {after} -}}}}")

    def handle_data(self, data: str):
        self._output.append(self._replace_brace(data))

    def get_html(self) -> str:
        return ''.join(self._output)

    def convert(self, input_html: str):
        self.feed(input_html)
        self.close()
        self._result = self._replace_brace(input_html)

    def insert_partials(self):
        # insert variables to render special content before specified tags
        html_rex = re.compile(r"""<("[^"]*"|\'[^\']*\'|[^\'">])*>""", re.S)
        tag_rex = re.compile(r"""[a-zA-Z]+""")

        def _replacer(m: re.Match) -> str:
            tag: str = m.group(0)
            tag_body = tag.strip("< ")
            tag_is_end = tag_body.startswith("/")
            if tag_is_end:
                tag_body = tag_body[1:]
            try:
                tag_name = tag_rex.match(tag_body).group(0)
            except AttributeError:
                return m.group(0)

            if tag_name in ("html", "head", "body"):
                if tag_is_end:
                    t =f"{{{{- {tag_name}_end -}}}}\n{m.group(0)}\n{{{{- after_{tag_name} }}}}"
                    return t
                else:
                    t =f"{{{{- before_{tag_name} -}}}}\n{m.group(0)}\n{{{{- {tag_name}_start }}}}"
                    return t
                
            return m.group(0)
        
        t = html_rex.sub(_replacer, self._result)
        self._result = t
        
    def get_result(self) -> str:
        return self._result

def convert_tumblr_to_jinja(input_html: str, log: bool = False) -> str:
    parser = TumblrThemeParser()
    #parser.feed(input_html)
    #parser.close()
    parser.convert(input_html)
    log = True
    if log:
        logger.info("---")
        for v in parser._custom_blocks:
            logger.info(f"{v}: {parser._custom_blocks[v]}")
        for v in parser._custom_vars:
            logger.info(f"{v}: {parser._custom_vars[v]}")
            
    return parser.get_result()

if __name__ == "__main__":
    try:
        target = sys.argv[1]
    except IndexError:
        print(f"{sys.argv[0]} target_file", file=sys.stderr)
        sys.exit(-1)

    with open(target, "rt", encoding="utf8") as fp:
            t = fp.read()

    s = convert_tumblr_to_jinja(t, True)
    print(s)
