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

## License
 
 GPLv3 ( https://www.gnu.org/licenses/gpl-3.0.html )
