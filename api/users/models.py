
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db.models.signals import post_save, post_delete, m2m_changed
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
import uuid
import urllib.parse
from django.core import serializers as core_serializers
import requests
import time
from api.settings import IPO_END_TIME,IPO_START_TIME
from datetime import datetime
# Create your models here.

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError(_('The email must be set'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user
    
    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        _('username'),
        max_length=150,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[username_validator],
        null=True
    )
    email = models.EmailField(_('email address'), blank=True, unique=True)
    userimage_url = models.URLField(default='/media/default.jpg')
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = CustomUserManager()


class Portfolio(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    value = models.FloatField(default=0)
    visible_money=models.FloatField(default=100000)
    initial_money = models.FloatField(default=100000) #for appD to calculate Net Profit/Loss
    # list_of_holdings accessed by portfolio.holding_set.all()
    watchlist=models.ManyToManyField('Stock',blank=True)

    class Meta:
        ordering = ['-value']
    def __str__(self):
        return f"{self.user.email}'s Portfolio"

class Stock(models.Model):
    name=models.CharField(max_length=100,unique=True)
    total_quantity=models.IntegerField()

    last_traded_price=models.FloatField(default=0)
    second_last_traded_price=models.FloatField(default=0)

    ask_price=models.FloatField(default=0)
    bid_price=models.FloatField(default=0)
    trading_active=models.BooleanField(default=True)
    stock_logo=models.CharField(max_length=200,blank=True)
    # misc=models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name

   
class AbstractTransaction(models.Model):
    quantity=models.IntegerField()
    price=models.FloatField()
    timestamp=models.DateTimeField(auto_now_add=True)
    transaction_type=models.CharField(max_length=1)
   
    def __str__(self):
        return f"{self.portfolio_id.user.email}'s {self.stock_id.name} transaction."
    class Meta:
        abstract=True
        


class OpenTransaction(AbstractTransaction):
    stock_id=models.ForeignKey(Stock,on_delete=models.CASCADE)
    portfolio_id=models.ForeignKey(Portfolio,on_delete=models.CASCADE)
    def delete(self, **kwargs):
        self.type = kwargs.get('type')
        super(OpenTransaction, self).delete()


class ClosedTransaction(AbstractTransaction):
    stock_id=models.ForeignKey(Stock,on_delete=models.CASCADE)
    portfolio_id=models.ForeignKey(Portfolio,on_delete=models.CASCADE)
    
    
class Holding(models.Model):
    portfolio_id=models.ForeignKey(Portfolio,on_delete=models.CASCADE)
    stock_id=models.ForeignKey(Stock,on_delete=models.CASCADE)
    quantity=models.IntegerField()
    price=models.FloatField()
 #here the price is average cost price, holding is basically the total holding of a particular stock

    def __str__(self):
        return f"{self.portfolio_id.user.email}'s {self.stock_id.name} holding."


class NewsItem(models.Model):
    title=models.CharField(max_length=1000)
    content=models.TextField()
    media_links=models.TextField(blank=True) # or file field?
    timestamp=models.DateTimeField()
    related_stocks=models.CharField(max_length=100, default="All")

    def __str__(self):
        return self.title


#Below all are signals to send updates to the channels when the model data is saved
@receiver(post_save, sender=NewsItem )
def news_updates_handler(sender, instance ,created, **kwargs):
    channel_layer = get_channel_layer()
    token='key=AAAAJMaxMGg:APA91bGCKR4MnNu1fOGefV-fCSdBcCjUR8trc819FKovrnfC0-FZ0aOYojFmh-tCS2FFdoT_S0WDhC4Y7LDO_yN4OQyxG14OxGfOOxeenEjD4lUYYpcirNTlPGtkT2ouu4rbLns74Yoq'
    url = 'https://fcm.googleapis.com/fcm/send'
    headers = {'Content-Type': 'application/json','Authorization':token}

    payload={
        "to": "/topics/News",
        "collapse_key": "type_a",
        "notification": {
            "title": instance.title,
            "body": instance.content,
            "link": instance.media_links,
        }
    }
    r = requests.post(url, data=json.dumps(payload), headers=headers)
    #send all news
    list1=[]
    result=NewsItem.objects.all()
    for news in result:
        data={}
        data['title']= news.title
        data['content']= news.content
        data['media_links']= news.media_links
        data['related_stocks']=  news.related_stocks
        data['timestamp']= news.timestamp.__str__()
        list1.append(data)
    async_to_sync( channel_layer.group_send)(
                'News_group',
                {
                    'type':'news_updates', 
                    'payload': json.dumps(list1)
                }
            )

   

@receiver(post_save, sender=Portfolio )
def Portfolio_updates(sender, instance ,created, **kwargs):
        channel_layer = get_channel_layer()
        data={"user":instance.user.first_name,"email":instance.user.email,'value': round(instance.value,2),'visible_money':  instance.visible_money,"initial_money":instance.initial_money}
        list=[]
        list.append(data)
        async_to_sync( channel_layer.group_send)(
            '%s_portfolio_group' %instance.user.email.replace('@','...',1), 
            {
                'type':'portfolio_updates', 
                'payload': json.dumps(list)
            }
        )



# @receiver(post_save, sender=Stock )
# def Stock_updates_handler(sender, instance ,created, **kwargs):
#         channel_layer = get_channel_layer()
#         data={}
#         data['name']= instance.name
#         data['total_quantity']=  instance.total_quantity
#         data['last_traded_price']= instance.last_traded_price
#         data['second_last_traded_price']= instance.second_last_traded_price
#         data['ask_price']= instance.ask_price
#         data['bid_price']=instance.bid_price
#         list=[]
#         list.append(data)
#         async_to_sync( channel_layer.group_send)(
#             'stock_group',# %instance.name.replace(' ','_'),
#             { 
#                 'type':'stock_updates', 
#                 'payload': json.dumps( list )
#             }
#         )


# @receiver(post_save, sender=OpenTransaction )
# def Transaction_updates_handler(sender, instance ,created, **kwargs):
#         channel_layer = get_channel_layer()
#         data={}
#         data['username']= instance.portfolio_id.user.username
#         data['email']= instance.portfolio_id.user.email
#         data['quantity']=instance.quantity
#         data['price']=instance.price
#         data['timestamp']= instance.timestamp.__str__()

#         async_to_sync( channel_layer.group_send)(
#             '%s_transaction_group'  %instance.portfolio_id.email.replace('@','-'),
#             {
#                 'type':'transaction_updates', 
#                 'payload': json.dumps(data)
#             }
#         )  


# @receiver(post_save, sender=ClosedTransaction )
# def Transaction_updates_handler(sender, instance ,created, **kwargs):
#         channel_layer = get_channel_layer()
#         data={}
#         data['username']= instance.portfolio_id.user.username
#         data['email']= instance.portfolio_id.user.email
#         data['quantity']=instance.quantity
#         data['price']=instance.price
#         data['timestamp']= instance.timestamp.__str__()
#         data['status']=  "Order Poccessed"
#         async_to_sync( channel_layer.group_send)(
#             '%s_transaction_group'  %instance.portfolio_id.email.replace('@','-'),
#             {
#                 'type':'transaction_updates', 
#                 'payload': json.dumps(data)
#             }
#         )  
    
# @receiver(post_delete, sender=OpenTransaction )
# def Transaction_updates_handler(sender, instance, **kwargs):
#         channel_layer = get_channel_layer()
#         if(instance.type=='no_notif'):
#             return
#         data={}
#         data['username']= instance.portfolio_id.user.username
#         data['email']= instance.portfolio_id.user.email
#         data['quantity']=instance.quantity
#         data['price']=instance.price
#         data['timestamp']= instance.timestamp.__str__()
#         data['status']=  instance.status
#         async_to_sync( channel_layer.group_send)(
#             '%s_transaction_group'  %instance.user.email.replace('@','-'),
#             {
#                 'type':'transaction_updates', 
#                 'payload': json.dumps(data)
#             }
#         )




# @receiver(post_save, sender=Holding)
# def Holding_updates_handler(sender, instance ,created, **kwargs):
#         channel_layer = get_channel_layer()
#         data={}
#         data['stockname']=instance.stock_id.name
#         data['username']= instance.portfolio_id.user.username
#         data['email']= instance.portfolio_id.user.email
#         data['quantity']=instance.quantity
#         data['price']=instance.price
        
#         portfolio_id=models.ForeignKey(Portfolio,on_delete=models.CASCADE)

#     #price=models.FloatField()

#         async_to_sync( channel_layer.group_send)(
#             '%s_transaction_group'  %instance.portfolio_id.email.replace('@','-'),
#             {
#                 'type':'transaction_updates', 
#                 'payload': json.dumps(data)
#             }
#         )  
    