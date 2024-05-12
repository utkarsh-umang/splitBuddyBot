from django.db import models
from .groups import Groups
from .users import User

class GroupMembers(models.Model):
    group = models.ForeignKey(Groups, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)