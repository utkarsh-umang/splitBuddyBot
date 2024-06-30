from django.db import models
from .groups_model import Groups
from .users_model import User

class Expenses(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    category = models.CharField(max_length=100, blank=True, null=True)
    paid_by = models.ForeignKey(User, on_delete=models.CASCADE)
    currency = models.CharField(max_length=3)
    group = models.ForeignKey(Groups, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.description} - {self.amount}"
    