"""P01 «Logg inn», P02 «Opprett konto» and sign-out (FR-1)."""

from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME, login
from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render, resolve_url
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters

from accounts.forms import SignInForm, SignUpForm
from core.http import safe_next


class SignInView(LoginView):
    template_name = "accounts/sign_in.html"
    form_class = SignInForm
    redirect_authenticated_user = True

    def get_redirect_url(self):
        return safe_next(self.request)


@login_not_required
@sensitive_post_parameters("password")
@csrf_protect
@never_cache
def sign_up(request):
    if request.user.is_authenticated:
        return redirect(safe_next(request) or resolve_url(settings.LOGIN_REDIRECT_URL))
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        student = form.save()
        if student is not None:
            login(request, student, backend="django.contrib.auth.backends.ModelBackend")
            return redirect(safe_next(request) or resolve_url(settings.LOGIN_REDIRECT_URL))
    next_url = safe_next(request)
    sign_in_url = reverse("accounts:sign_in")
    if next_url:
        sign_in_url += "?" + urlencode({REDIRECT_FIELD_NAME: next_url})
    return render(
        request,
        "accounts/sign_up.html",
        {"form": form, REDIRECT_FIELD_NAME: next_url, "sign_in_url": sign_in_url},
    )


# POST only (Django's LogoutView answers GET with 405); CSRF is checked by the middleware.
# Not sign-in required, so a stale tab's sign-out still lands on P01.
sign_out = login_not_required(LogoutView.as_view())
