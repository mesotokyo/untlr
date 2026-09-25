import logging
logger = logging.getLogger(__name__)

# helper function to get handler
def get_handler[T](obj: object, prefix: str, name: str, fallback: T) -> T:
    qn = name.replace("-", "_")
    fname = f"""{prefix}_{qn}"""
    try:
        func: T = getattr(obj, fname)
    except AttributeError:
        msg = f"{prefix} handler for {name} is not implemented"
        logger.debug(msg)
        func = fallback
    return func
