from django.contrib import admin
from .models import *
# Register your models here.
model_list =[User, Portfolio,NewsItem, Stock, Holding,ClosedTransaction,OpenTransaction]
admin.site.register(model_list)

