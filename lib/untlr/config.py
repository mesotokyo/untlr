from tyconf import TyConf
from tyconf.tyconf import TomlWriter

class SystemConfig(TyConf):
    """Untlr system-wide settings"""
    cache: bool
    cache_dir: str
    listen: str
    port: int
    sass_command: str
    sass_timeout: int
    sass_cwd: str
    log_level: str

    def init(self):
        self.add_key("cache", bool, default=True,
                     help="Cache Tumblr API result or not")
        self.add_key("cache_dir", str, default="cache",
                     help="Directory to store caches")
        self.add_key("listen", str, default="", help="IP address to listen")
        self.add_key("port", int, default=8080, help="Port to listen")
        self.add_key("sass_command", str,
                     default="node run_sass/compile_sass.js",
                     help="Command line to execute sass")
        self.add_key("sass_timeout", int, default=3,
                     help="Timeout for sass command execution (sec).")
        self.add_key("sass_cwd", str, default="run_sass",
                     help="Working directry to run the sass command")
        self.add_key("log_level", str, default="info",
                     help="Default log level")


class WatchConfig(TyConf):
    """File watcher settings"""
    enabled: bool
    ignore: list[str]

    def init(self):
        self.add_key("enabled", bool, default=False,
                     help="Watch template files and update render result automatically")
        self.add_key("ignore", list[str], default=[ "^\\.#.*", "^#", ".*~$" ],
                     help="Exclude matched files from watching")


class BlogConfig(TyConf):
    """Blog related settings"""
    id: str

    def init(self):
        self.add_key("id", str, help="Blog ID to retrieve contents")


class APIConfig(TyConf):
    """Tumblr API settings"""
    host: str
    key: str

    def init(self):
        self.add_key("host", str, default="https://api.tumblr.com",
                     help="Tumblr API endpoint")
        self.add_key("key", str, example="abcdefg123456...",
                     required=True,
                     help="Tumblr API key")


class PageConfig(TyConf):
    """Configuration related each pages"""
    before_html: str
    after_html: str
    html_start: str
    html_end: str
    before_head: str
    after_head: str
    head_start: str
    head_end: str
    before_body: str
    after_body: str
    body_start: str
    body_end: str

    def init(self):
        self.add_key("before_html", str, example="foo.html",
                     help="File to insert before html tag")
        self.add_key("after_html", str, example="foo.html",
                     help="File to insert after html tag")
        self.add_key("html_start", str, example="foo.html",
                     help="File to insert to start of   html tag")
        self.add_key("html_end", str, example="foo.html",
                     help="File to insert to end of html tag")

        self.add_key("before_head", str, example="foo.html",
                     help="File to insert before head tag")
        self.add_key("after_head", str, example="foo.html",
                     help="File to insert after head tag")
        self.add_key("head_start", str, example="foo.html",
                     help="File to insert to start of  head tag")
        self.add_key("head_end", str, example="foo.html",
                     help="File to insert to end of head tag")

        self.add_key("before_body", str, example="foo.html",
                     help="File to insert before body tag")
        self.add_key("after_body", str, example="foo.html",
                     help="File to insert after body tag")
        self.add_key("body_start", str, example="foo.html",
                     help="File to insert to start of  body tag")
        self.add_key("body_end", str, example="foo.html",
                     help="File to insert to end of body")
        #self.add_key("", str, example="foo.html", help="File to insert ")


@TyConf.conf(ignore_extra=False)
class DefaultValues(TyConf):
    """Default values to pass the renderer"""
    pass


class UntlrConfig(TyConf):
    theme_dir: str
    theme_file: str
    system: SystemConfig
    watch: WatchConfig
    blog: BlogConfig
    api: APIConfig
    index_page: PageConfig
    post_page: PageConfig
    default_values: DefaultValues

    def init(self):
        self.add_key("theme_dir", str, example="theme",
                     help="Directory contains theme files")
        self.add_key("theme_file", str, example="theme.html",
                     help="Theme file")
        self.add_key("system", SystemConfig)
        self.add_key("watch", WatchConfig)
        self.add_key("blog", BlogConfig)
        self.add_key("api", APIConfig)
        self.add_key("index_page", PageConfig,
                     help="Configuration for rendering index page")
        self.add_key("post_page", PageConfig,
                     help="Configuration for rendering post page")
        self.add_key("default_values", DefaultValues)
