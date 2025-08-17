from django.contrib import admin
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from .models import Household, UserProfile, News, Expense, ExpensePayment, Task, PersonalExpense


admin.site.register(Token)
admin.site.register(Household)  
admin.site.register(UserProfile)
admin.site.register(News)
admin.site.register(Expense)
admin.site.register(ExpensePayment)
admin.site.register(Task)
admin.site.register(PersonalExpense)



