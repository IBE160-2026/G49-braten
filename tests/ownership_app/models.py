from django.conf import settings
from django.db import models

from core.ownership import OwnedQuerySet


class Note(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)

    objects = OwnedQuerySet.as_manager()
