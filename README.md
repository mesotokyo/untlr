# untlr - UNofficial Tumblr Lazy Renderer

## What is this?

`untlr` is a Python-based cli tool that provides features such as:

 - Render Tumblr blog contents using Tubmlr's "Custom Theme"
 - Run minimal HTTP server for developing Custom Theme
 - Manage splited Custom Theme and build them into single file
 
 ## Install 
 
 ```bash
 $ git clone --recursive https://github.com/mesotokyo/untlr/
 $ cd untlr
 $ python3 -m venv venv
 $ . venv/bin/activate
 $ pip3 install -r requirements.txt
 $ cd run_sass
 $ npm i
 $ cd ..
 ```
 
 ## How to use
 
First, create configuration file. You can generate skelton file with `--config-skelton` option:
 
```bash
$ python3 untlr_server.py --config-skelton > config.toml
```

Run `untlr_server.py` by specifying the theme files as an argument:

```bash

$ python3 untlr_server.py Theme.html
```

For example, you can get `DataTheme` via [https://github.com/tumblr/DataTheme/](https://github.com/tumblr/DataTheme/).

## Configuration

You need at least the following configuration keys:

 - `api.key`
 - `blog.id`
 
 ### `api.key`
`untlr` uses Tumblr API to retrieve blog contents, and API key ("OAuth consumer key") is needed to call these APIs. If you have Tumblr account, you can issue it after registering your "Applications" on [OAuth Applications](https://www.tumblr.com/oauth/apps) page on Tumblr.

### `blog.id`

Give your Tumblr blog domain. For example, when your blog URL is `https://some-domain-name.tumblr.com/`,  set `some-domain-name.tumblr.com`. 

**NOTE**: `untlr` uses public API to retrieve Blog contents, so you can set the blog domain other than you manage to `blog.id`, such as `nihongo.tumblr.com`.


## License
 
 GPLv3 ( https://www.gnu.org/licenses/gpl-3.0.html )
