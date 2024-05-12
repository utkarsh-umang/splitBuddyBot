from django.db import models
from .users_model import User

class Groups(models.Model):
    group_name = models.CharField(max_length=100)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="group_creator")
    created_at = models.DateTimeField(auto_now_add=True)