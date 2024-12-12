from django.db import models
from django.conf import settings

# Create your models here.
class Header(models.Model):
    name   = models.TextField(default='')
    actual_position = models.TextField(default='')
    description = models.TextField(default='')
    profile_picture = models.URLField()
    email = models.EmailField(unique=True)
    cellphone = models.TextField(default='')
    location = models.TextField(default='')
    github = models.TextField(default='')
    posted_by  = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)

    def save (self, *args, **kwargs):
        if Header.objects.exists() and not self.pk:
            raise Exception('Only one header instance is allowed')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name