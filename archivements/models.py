# Create your models here.
from django.db import models
from django.conf import settings
from django.utils.timezone import now

# Create your models here.
class Archivements(models.Model):
    archivementName = models.TextField(default='')
    year            = models.PositiveIntegerField(default=2024)
    posted_by       = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)