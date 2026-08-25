from pathlib import Path

from django import template

register = template.Library()

@register.filter
def replace_ext(url: str, new_ext: str = "webp"):
    base, sep, q = url.partition("?")
    p = Path(base)
    new_url = str(p.with_suffix("." + new_ext))
    return new_url + (sep + q if sep else "")

@register.filter
def add_suffix(url: str, suffix: str):
    # /media/x/y.jpg + '-800' -> /media/x/y-800.jpg
    base, sep, q = url.partition("?")
    p = Path(base)
    new_url = str(p.with_name(p.stem + suffix + p.suffix))
    return new_url + (sep + q if sep else "")
