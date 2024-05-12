from django.contrib.auth.models import AbstractUser
from django.db import models
from .groups import Groups

class User(AbstractUser):
    phone_number = models.CharField(max_length=15, unique=True, null=False)
    group_id = models.ForeignKey(Groups, on_delete=models.SET_NULL, null=False, blank=False)
    owed_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    lended_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    