"""Template helpers shared by every app: icons and Student-facing messages by code."""

from django import template
from django.templatetags.static import static
from django.utils.html import format_html

from core.messages import MESSAGES

register = template.Library()


@register.simple_tag
def icon(name: str, size: str = ""):
    """An icon from static/icons/sprite.svg (Conventions: Templates). Decorative, so aria-hidden."""
    css = f"icon icon-{size}" if size else "icon"
    return format_html(
        '<svg class="{}" aria-hidden="true" focusable="false"><use href="{}#i-{}"></use></svg>',
        css,
        static("icons/sprite.svg"),
        name,
    )


@register.simple_tag
def message(code: str) -> str:
    """The Norwegian text for an error `code` from core.messages."""
    return MESSAGES[code]
