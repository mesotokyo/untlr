from typing import Any
import logging
logger = logging.getLogger(__name__)

from npwr import NPFWebRenderer, RendererConfig, RendererOption

class NPFRenderError(Exception): pass

def render_npf(npf: dict[str, Any], format: str, renderer: str = "") -> str:
        return _render_npf_with_npwr(npf, format)

def _render_npf_with_npwr(npf: dict[str, Any], format: str) -> str:
    option: RendererOption = RendererOption.SKIP_TITLE
    if format == "page":
        option = option | RendererOption.TRUNCATE
    elif format == "post":
        pass
    else:
        pass
    config: RendererConfig = { "option": option }
    renderer = NPFWebRenderer(config)
    html = renderer.render(npf)
    return  html

