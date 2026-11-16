"""The Location marker format (AD-6): fixed here, in `ai`.

Only non-empty Locations get a marker. The prompt (story 10) puts `marker(index)` before each
Location's text; the Reference check (`studymat.checks`) strips markers from both sides before
comparing, in case the model copied one into a quote.
"""

import re

MARKER_FORMAT = "[[L{index}]]"
MARKER_PATTERN = re.compile(r"\[\[\s*L\s*\d+\s*\]\]", re.IGNORECASE)


def marker(index: int) -> str:
    return MARKER_FORMAT.format(index=index)


def strip_markers(text: str) -> str:
    """`text` with every marker replaced by a space."""
    return MARKER_PATTERN.sub(" ", text)


def marked_text(locations) -> str:
    """The Locations (objects with `index` and `text`) joined, each non-empty one after its marker."""
    return "\n\n".join(f"{marker(loc.index)}\n{loc.text}" for loc in locations if loc.text.strip())
