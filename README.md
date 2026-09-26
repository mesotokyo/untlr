# untlr - UNofficial Tumblr Lazy Renderer

## What is this?

`untlr` is a Python-based cli tool that provides features such as:

 - Render Tumblr blog contents to HTML using Tubmlr's "Custom Theme"
 - Run minimal HTTP server for developing and editing Custom Theme
 - Manage splited Custom Theme and build them into a single file

## Requirements

 * Python 3.13.x or later
 * If you want to use [Sass](https://sass-lang.com/), Node.js v16.18.0 for `sass` command.

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

**Note**: If you don't want to use `Sass`, you can skip the steps following `cd run_sass`.

## How to use

### Create configuration file

First, create configuration file. You can generate skelton file with `--config-skelton` option:

```bash
$ python3 untlr_server.py --config-skelton > config.toml
```

### Edit configuration file

You need at least the following configuration keys:

 - `api.key`
 - `blog.id`

#### Set Tumblr API key (`api.key`)

`untlr` uses Tumblr API to retrieve blog contents, and API key ("OAuth consumer key") is needed to call these APIs. If you have Tumblr account, you can issue it after registering your "Applications" on [OAuth Applications](https://www.tumblr.com/oauth/apps) page on Tumblr.

#### Set your blog ID (`blog.id`)

Set your Tumblr blog domain to `blod.id`. For example, when your blog URL is `https://some-domain-name.tumblr.com/`,  set `some-domain-name.tumblr.com`. 

**NOTE**: `untlr` uses public API to retrieve Blog contents, so you can set the blog domain other than you manage to `blog.id`, such as `nihongo.tumblr.com`.

### Run `untlr_server.py`

Run `untlr_server.py` by specifying the theme files as an argument:

```bash

$ python3 untlr_server.py Theme.html
```

For example, you can get `DataTheme` via [https://github.com/tumblr/DataTheme/](https://github.com/tumblr/DataTheme/).

### Access from Web browser

You can view the rendered content by accessing `http://localhost:8080/` in your Web browser.

## Functional limitations

As it stands, `untlr_server.py` does not guarantee that all themes and content will be rendered exactly as provided by the Tumblr. The reasons are as follows:

 - As far as I checked, some of the officially provided theme files appear to use directives that are not publicly documented.
 - When the Tumblr renders content, it does not simply convert it to HTML; it also makes slight structural changes, adds some tags and scripts, and adds classes. These are not documented.
 - `untlr_server.py` uses custom NPF parser (called `npwr`). Currently `npwr` does not support some layout style.

If you encounter any issues while using it, please provide some feedback.

## Features and Configuration

### Content cache

When the `untlr_server.py` receives a request (that is, when you access localhost:8080 in your browser), `untlr_server.py` requeset to Tumblr API server to retrieve blog contents. And to avoid frequent API calls, `unltr_server.py` saves retrieved contents to cache directory (default: `./cache`).

### Theme file and directory

When `untlr_server.py` is executed with a file specified as an argument (For example. `$ python3 untlr_serve.py theme.html`), `untlr_server.py` uses this file as a theme to render contents.

On the other hand, when executed with a directory as an argument (For example. `$ python3 untlr_serve.py theme_dir`), `untlr_server.py` uses `index.html` in the given directory (For example, in this case, `theme_dir/index.html`) as a theme.

Also, you can give them by `theme_dir` and `theme_file` configuration value.

### Managing splited theme files and pre-rendering

When the `untlr_server.py` render blog content, `untlr_server.py` render given theme file as `Jinja2` template first, and then parse as Tumblr theme and render to HTML. We call the first process "pre-rendering", and if the theme file contains instructions for Jinja templates, the template engine processes them appropriately. Since `Jinja2` has features for loading content from other files such as the `{% include %}` directive ([document](https://jinja.palletsprojects.com/en/stable/templates/#include)),  you can use this directive to split your theme files into multiple files for easier management.

**Note:** When loading another file using `{% include %}` directive, the target file will be searched using the diretory speficied by the `theme_directory` configuration value as the current directory. If this configuration value is not set, this value will be set to `.` (current directory).

For more information about `Jinja2`, see [Jinja2 documentation](https://jinja.palletsprojects.com/en/stable/).

### `include_sass` directive for `Jinja2` template

For pre-rendering process, `untlr_server.py` provides a special directive): `{% include_sass <filename> %}`.

This directive load a given `Sass` format file, then convert it to CSS, and renders the result into the theme.

`untlr_server.py` uses Node.js version of the `sass` command internally. Therefore, if you want to use `{% include_sass %}`, Node.js is required.

### Bundle splited theme files to a single file

You can bundle (combine) splitted theme files to a single files with `--render` option:

```bash
$ python3 untlr_server.py --render theme.html index.html
```

### Other command line options

You can check command line options by `--help` option:

```bash
$ python3 untlr_server.py --help
```

## License
 
 GPLv3 ( https://www.gnu.org/licenses/gpl-3.0.html )
