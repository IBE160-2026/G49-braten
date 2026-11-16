"""Template helpers for Study material: the Reference label (AD-6)."""

from django import template

from studymat import services

register = template.Library()


@register.filter
def location_label(item) -> str:
    """«Side 14 · {kilde}» / «Avsnitt 3 · {kilde}» for an item with a Reference."""
    return services.location_label(item.source, item.location_index)
