"""Placeholder Home: somewhere for sign-in to land. Story 3 replaces it with P03."""

from django.shortcuts import render


def home(request):
    return render(request, "web/home.html")
