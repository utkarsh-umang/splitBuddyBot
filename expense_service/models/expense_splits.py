from django.db import models
from .expenses import Expenses
from .users import User

class ExpenseSplits(models.Model):
    expense = models.ForeignKey(Expenses, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    split_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_settled = models.BooleanField(default=False)
    settled_at = models.DateTimeField(null=True, blank=True)
    expense_type = models.CharField(max_length=10, choices=(('OWED', 'Owed'), ('OWING', 'Owing')))