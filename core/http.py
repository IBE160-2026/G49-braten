"""HTMX helpers shared by every app (AD-13, AD-18).

Every URL renders a full page. Under HTMX a view may answer with one named
`{% partialdef %}` partial instead, chosen by `request.htmx.target`, and only for a
request that is not a history restore. Such views carry `vary_on_htmx`, so a cached
fragment is never served as a page.
"""

from functools import wraps

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.shortcuts import redirect, render
from django.utils.cache import patch_vary_headers
from django.utils.http import url_has_allowed_host_and_scheme
from django_htmx.http import HttpResponseLocation

VARY_HEADERS = ("HX-Request", "HX-Target", "HX-History-Restore-Request")

# The one dialog slot in layouts/base.html (AD-18).
DIALOG_TARGET = "dialog"


def vary_on_htmx(view):
    """Adds `Vary: HX-Request, HX-Target, HX-History-Restore-Request` to the response."""

    @wraps(view)
    def wrapped(request, *args, **kwargs):
        response = view(request, *args, **kwargs)
        patch_vary_headers(response, VARY_HEADERS)
        return response

    return wrapped


def htmx_target(request) -> str | None:
    """The HTMX target id this request may get a partial for, or None for a full page."""
    htmx = getattr(request, "htmx", None)
    if not htmx or htmx.history_restore_request:
        return None
    return htmx.target


def render_page(request, template_name, context=None, *, partials=(DIALOG_TARGET,), status=200):
    """The full page, or its partial named like the HTMX target when it has one."""
    target = htmx_target(request)
    if target in partials:
        template_name = f"{template_name}#{target}"
    return render(request, template_name, context, status=status)


def redirect_after_submit(request, url):
    """A valid submit answers with `HX-Location` under HTMX, and a 302 otherwise."""
    if getattr(request, "htmx", None):
        return HttpResponseLocation(url)
    return redirect(url)


def safe_next(request) -> str:
    """`next` when it is a relative URL on this site, otherwise ""."""
    url = request.POST.get(REDIRECT_FIELD_NAME) or request.GET.get(REDIRECT_FIELD_NAME) or ""
    # allowed_hosts=None: any URL naming a host or scheme is refused, so only relative paths pass.
    if url.startswith("/") and url_has_allowed_host_and_scheme(url, allowed_hosts=None):
        return url
    return ""
