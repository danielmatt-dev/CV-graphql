from django.db import models
from django.conf import settings

# Create your models here.
class Skill(models.Model):
    skill = models.TextField(default='')
    percent = models.PositiveIntegerField(default=0)
    posted_by  = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)
