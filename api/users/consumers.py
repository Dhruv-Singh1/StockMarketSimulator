import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import *
from django.core import serializers 
import urllib.parse
from datetime import datetime, timedelta
import time
from api.settings import IPO_END_TIME,IPO_START_TIME

class PortfolioConsumer(AsyncWebsocketConsumer):
    async def connect(self,**kwargs):
        self.room_name = '%s_portfolio' %self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = '%s_group' %self.room_name
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        await self.send(text_data=json.dumps({'status':'connected' }))
        @sync_to_async 
        def portfolio_info():
            list=[]
            try:
                user=User.objects.filter(email=self.scope['url_route']['kwargs']['room_name'].replace('...','@',1)).select_related('portfolio')[0]
                portfolio=user.portfolio
            except:
                pass    
            try:
                j=json.loads(json.dumps({"user":user.first_name,"email":user.email,'value': round(portfolio.value,2),'visible_money':  portfolio.visible_money,'initial_money':  portfolio.initial_money}))
                list.append(j)
            except:
                pass
            return list

        await self.send(text_data=json.dumps({'portfolio': await portfolio_info() }))
    
    
    async def portfolio_updates(self , data):
         portfolio = json.loads(data['payload'])
         await self.send(text_data=json.dumps({'portfolio':portfolio}))
        
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )


class StockPriceConsumer(AsyncWebsocketConsumer):
    async def connect(self,**kwargs):
        self.room_name = 'stock' # %self.scope['url_route']['kwargs']['room_name'].replace(' ','_')
        self.room_group_name = '%s_group' %self.room_name
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
       # await self.send(text_data=json.dumps({'status':'connected' }))
        @sync_to_async
        def all_stocks():
            list1=[]
            stocks=Stock.objects.all()
            for stock in stocks:
                data={}
                data['name']= stock.name
                data['last_traded_price']= stock.last_traded_price
                data['deviation']= 100*(stock.last_traded_price-stock.second_last_traded_price)/stock.second_last_traded_price
                data['total_quantity']=  stock.total_quantity
                data['ask_price']= stock.ask_price
                data['bid_price']=stock.bid_price
                data['ipo']=(time.time()>IPO_START_TIME and time.time()<IPO_END_TIME)
                data['logo']=stock.stock_logo
                data['active']=stock.trading_active
                list1.append(data)

            return list1
        await self.send(text_data=json.dumps({'Stock': await all_stocks() }))
      
        
    async def stock_updates(self , data):
        stock = json.loads(data['payload'])
        await self.send(text_data=json.dumps({'Stock':stock}))
        
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

# class TransactionConsumer(AsyncWebsocketConsumer):
#     async def connect(self,**kwargs):
#         self.room_name = '%s_transaction' %self.scope['url_route']['kwargs']['room_name']
#         self.room_group_name = '%s_group' %self.room_name
#         # Join room group
#         await self.channel_layer.group_add(
#             self.room_group_name,
#             self.channel_name
#         )

#         await self.accept()
#         await self.send(text_data=json.dumps({'status':'connected' }))
#         await self.send(text_data= json.dumps({
#             "transaction": {
#                 "username": "DhruvSingh",
#                 "email": "f20200969@pilani.bits-pilani.ac.in",
#                 "quantity": 40,
#                 "price": 92,
#                 "stop_limit": 80,
#                 "timestamp": "2022-04-01 05:48:53.181931+00:00",
#                 "status": "0",
#                 "transaction_type": "B"
#             }
#         })  )

#     async def transaction_updates(self , data):
#            transaction = json.loads(data['payload'])
#            await self.send(text_data=json.dumps({'transaction':transaction}))
        
#     async def disconnect(self, close_code):
#             # Leave room group
#             await self.channel_layer.group_discard(
#                 self.room_group_name,
#                 self.channel_name
#             )
# class HoldingConsumer(AsyncWebsocketConsumer):
#     async def connect(self,**kwargs):
#         self.room_name = '%s_transaction' %self.scope['url_route']['kwargs']['room_name']
#         self.room_group_name = '%s_group' %self.room_name
#         # Join room group
#         await self.channel_layer.group_add(
#             self.room_group_name,
#             self.channel_name
#         )

#         await self.accept()
#         await self.send(text_data=json.dumps({'status':'connected' }))

#     async def holding_updates(self , data):
#            transaction = json.loads(data['payload'])
#            await self.send(text_data=json.dumps({'holdings':transaction}))
        
#     async def disconnect(self, close_code):
#             # Leave room group
#             await self.channel_layer.group_discard(
#                 self.room_group_name,
#                 self.channel_name
#             )


class LeaderboardConsumer(AsyncWebsocketConsumer):
    async def connect(self,**kwargs):
        self.room_name = 'Leaderboard'#self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'Leaderboard_group'
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
       # await self.send(text_data=json.dumps({'status':'connected' }))
        @sync_to_async
        def get_leaderboard():
            # users = Portfolio.objects.order_by('-value')[:10]
            users=Portfolio.objects.extra(
            select={'fieldsum':'value + visible_money'},
            order_by=('-fieldsum',)
            )[:10]
            channel_layer = get_channel_layer()
            list=[]
            data={}

            #totak of user value and visible_money truncated to 2 digits

            for user in users:
                if not user.user.is_staff:
                    list.append({"username":user.user.first_name,"email":user.user.email,"value":round(user.value+user.visible_money,2)})
            return list
        await self.send(text_data=json.dumps({'Leaderboard': await get_leaderboard()}))

        
    async def leaderboard_list(self , data):
        leaderboard = json.loads(data['payload'])
        await self.send(text_data=json.dumps({'Leaderboard':leaderboard}))
        
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )


class NewsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = 'News' #self.scope['url_route']['kwargs']['stock_name']
        self.room_group_name = 'News_group' #% self.room_name       
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        @sync_to_async
        def get_news():
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
            return list1
      
        await self.send(text_data=json.dumps({ 'News': await get_news() }))

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
     # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'news_updates',
                'payload': text_data
            }
        )
    # Receive message from room group
    async def news_updates(self , new_news):
      #  print("Im in lst phase")
        new_news = json.loads(new_news['payload'])
        await self.send(text_data=json.dumps({'News':new_news}))