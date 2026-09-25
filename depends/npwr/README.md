# npwr - NPF Web Renderer

## What is this?

`npwr` is a Python library to render [NPF document](https://github.com/tumblr/docs/blob/master/npf-spec.md) to HTML.

## How to use

```
from npwr import NPFWebRenderer

config = {
    "option": RendererOption.SKIP_TITLE | RendererOption.TRUNCATE
}
renderer = NPFWebRenderer(config)
html = renderer.render(npf)
```

## Configuration

You can change the behavior of the renderer with `option` item of the `config` variable.

| Option value | Description |
| -------------- | ------------- |
| SKIP_TITLE | Does not render the title of content. |
| TRUNCATE | Does not render the content after the `truncate_after` block |

## Dependency

This library uses [intervaltree](https://github.com/chaimleib/intervaltree).


