# from django.db import transaction
# from .models import User, Groups, Expenses, ExpenseSplits
# from .utils import get_group_members

# @transaction.atomic
# def add_expense_to_db(user_id, group_id, amount, description, currency):
#     try:
#         # Fetching the user and the group
#         user = User.objects.get(id=user_id)
#         group = Groups.objects.get(id=group_id)
#         # Creating entry in expense table
#         expense = Expenses.objects.create(
#             amount = amount,
#             description = description,
#             paid_by = user,
#             currency = currency,
#             group = group
#         )
#         # Getting other group members 
#         members = get_group_members(group_id)
#         # Adding split is Expense Split for all members
#         split_amount = amount / members.count()
#         for member in members:
#             ExpenseSplits.objects.create(
#                 expense=expense,
#                 user=member,
#                 split_amount=split_amount,
#                 expense_type='OWING' if member != user else 'OWED'
#             )
#         return True
#     except Exception as e:
#         return str(e)
