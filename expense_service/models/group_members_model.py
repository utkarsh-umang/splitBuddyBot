import uuid
from django.db import models
from .groups_model import Groups
from .users_model import User

class GroupMembers(models.Model):
    
    group = models.ForeignKey(Groups, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)