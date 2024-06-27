from django.contrib.auth.models import AbstractUser
from django.db import models
# from .groups_model import Groups

class User(AbstractUser):
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    owed_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    lended_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    first_name = models.CharField(max_length=100,null=False,blank=False)
    last_name = models.CharField(max_length=100,null=True,blank=True)
    telegram_user_id = models.CharField(max_length=255,unique=True)
    user_name = models.CharField(max_length=100,null=True,blank=True)

    