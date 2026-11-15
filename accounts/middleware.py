"""Sign-in required everywhere (AD-7), with an HX-Redirect for HTMX requests.

Swapping the sign-in page into a region would break the page, so an HTMX request
gets `HX-Redirect` and htmx loads sign-in as a full page.
"""

from django.contrib.auth.middleware import LoginRequiredMiddleware as DjangoLoginRequiredMiddleware
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import resolve_url
from django.utils.http import url_has_allowed_host_and_scheme
from django_htmx.http import HttpResponseClientRedirect


class LoginRequiredMiddleware(DjangoLoginRequiredMiddleware):
    def handle_no_permission(self, request, view_func):
        htmx = getattr(request, "htmx", None)
        if not htmx:
            return super().handle_no_permission(request, view_func)
        # Return to the page the browser shows, not to the fragment URL htmx asked for.
        next_url = htmx.current_url_abs_path
        if not next_url or not url_has_allowed_host_and_scheme(next_url, allowed_hosts=None):
            next_url = request.get_full_path()
        login = redirect_to_login(
            next_url,
            resolve_url(self.get_login_url(view_func)),
            self.get_redirect_field_name(view_func),
        )
        return HttpResponseClientRedirect(login["Location"])
