from django.shortcuts import render
from rest_framework.views import APIView, Response
from rest_framework import status
from .models import *
from users.models import User,Stock,Holding,Portfolio
from django.contrib.auth import login
from rest_framework.authtoken.models import Token
from django.http import JsonResponse
from rest_framework.permissions import AllowAny
from .serializers import *
import json
from channels.layers import get_channel_layer
from django.core import serializers
import csv
from datetime import datetime, timedelta
from django.views.decorators.csrf import csrf_exempt
from asgiref.sync import async_to_sync
from api.settings import IPO_START_TIME, IPO_END_TIME
import time
# from __future__ import print_function
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from django.db import connection
from django.db import transaction as tran

#TESTED, change if needed #integrated
class LoginView(APIView):
    """
        The user is redirected to this view
        once the google login is successfull.
        We then create a corressponding portfolio object
        with the user ID.
    """
    permission_classes = [AllowAny]
    @csrf_exempt
    def post(self, request):
        email=request.data['email']
        userimage_url = request.data['userimage_url']
        try:
            name=request.data['name']
            #convert to string
            name=str(name)
        except:
            name='default'
        user=User.objects.filter(email=email)
        #if user is not present in the database
        if not user:
            
            user=User.objects.create(email=email,first_name=name, userimage_url=null)
            user.save() 
            portfolio=Portfolio.objects.create(user=user)
            portfolio.save()
            #create all stock holdings for the user

            for stock in Stock.objects.all():
                Holding.objects.create(portfolio_id=portfolio,stock_id=stock,quantity=0,price=0)
            token = Token.objects.create(user=user)
            return JsonResponse({'token':token.key}, status=status.HTTP_200_OK)
        else:
            user=user[0]
            token = Token.objects.filter(user=user)[0]
            return JsonResponse({'token':token.key}, status=status.HTTP_200_OK)

#TESTED, change if needed #integrated
class OrderHistory(APIView):
    """
        This view is used to fetch the order history
        of the logged in user. (ClosedTransactions)
    """
    @csrf_exempt
    def get(self, request):
        # portfolio=Portfolio.objects.filter(user=request.user)[0]
        user=request.user
        portfolio=user.portfolio
        orders=portfolio.closedtransaction_set.all()
        data=[]
        for order in orders:
            data.append({
                'stock_name':order.stock_id.name,
                'quantity':order.quantity,
                'price':order.price,
                'timestamp':order.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                'transaction_type':order.transaction_type
            })
        data={"history":data}
        #IMPORTANT: AFTER PARTIAL STOCK PROCESSING, HISTORY??? CANCELLATION???
        return Response(data, status=status.HTTP_200_OK)

#TESTED, change if needed #integrated
class CurrentActiveOrders(APIView):
    """
        This view is used to fetch the current active orders
        of the logged in user. (OpenTransactions)
    """
    @csrf_exempt
    def get(self, request):
        # portfolio=Portfolio.objects.filter(user=request.user)[0]
        user=request.user
        portfolio=user.portfolio

        orders=portfolio.opentransaction_set.all()
        data=[]
        for order in orders:
            
            data.append({
                    'id':order.id,
                    'stock_name':'%s'%order.stock_id.name,
                    'quantity':order.quantity,
                    'price':order.price,
                    'timestamp':order.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'transaction_type':order.transaction_type,
            })
        data={"active":data}
        return Response(data, status=status.HTTP_200_OK)

#TESTED, change if needed #integrated
class CurrentHoldings(APIView):
    """
        This view is used to fetch the current holdings
        of the logged in user.
    """
    @csrf_exempt
    def get(self, request):
        user=request.user
        portfolio=user.portfolio
        # portfolio=Portfolio.objects.filter(user=request.user)[0]
        holdings=portfolio.holding_set.all()
        # connection.close()
        data=[]
        for holding in holdings:
            
            if holding.quantity>0:
                stock=holding.stock_id
                data.append({
                        'stock_name':"%s"%holding.stock_id.name,
                        'quantity':holding.quantity,
                        'price':holding.price,
                        'deviation':100*(stock.last_traded_price-stock.second_last_traded_price)/stock.second_last_traded_price
                    })
        responsedata={"holdings":data}
        return Response(responsedata, status=status.HTTP_200_OK)

#TESTED to some extent #Integrated
class PlaceOrderView(APIView):
    """Create a Transaction and add it to the processing queue for buying"""
    @csrf_exempt
    def post(self, request):
            
        time_left=(timedelta(minutes=3)-ceil_dt(datetime.now(),timedelta(minutes=3))).total_seconds()
        if(time_left<10):
            return Response({'msg': 'Cannot Place orders less than 15 seconds before processing'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        elif(time_left>150):
            return Response({'msg': 'Currently Processing orders, please try again after sometime'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        try:
            stock = Stock.objects.filter(name=(request.data['stock_name']))[0]
            user = request.user
            # portfolio = Portfolio.objects.filter(user=user)[0]
            portfolio=user.portfolio
            quantity = int(request.data['quantity'])
            try:
                price=float(request.data['price'])
            except:
                price=stock.last_traded_price

            if(quantity<=0):
                return Response({'msg': 'Quantity must be greater than 0'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            if(price<=0):
                return Response({'msg': 'Price must be greater than 0'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            if(stock.trading_active==False):
                return Response({'msg': 'Stock not currently active'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            
            transaction_type=request.data['transaction_type']
            
           

            if(abs(price-stock.last_traded_price)/stock.last_traded_price>0.1):
                return Response({'msg': 'Price must be within 10% of last traded price'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            if time.time()>IPO_START_TIME and time.time()<IPO_END_TIME:
                if(transaction_type=='S'):
                    return Response({'msg': 'Cannot Sell stocks during IPO'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                if(portfolio.visible_money>=stock.last_traded_price*quantity*1.001):
                    if(stock.total_quantity<quantity):
                        return Response({'msg': 'Insufficient quantity'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    
                    else:
                        portfolio.visible_money-=stock.last_traded_price*quantity*1.001
                        portfolio.save()
                        transaction = OpenTransaction(stock_id=stock, portfolio_id=portfolio, quantity=quantity, price=stock.last_traded_price,transaction_type='B')
                        transaction.save()
                        return Response({'msg': 'Order Placed, at current IPO Price', 'order_id':transaction.id}, status=status.HTTP_200_OK)
                else:
                    return Response({'msg': 'Insufficient balance'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            if(transaction_type=='B'):

                if(portfolio.visible_money>=price*quantity*1.001):      
                    portfolio.visible_money=portfolio.visible_money-price*quantity*1.001
                    portfolio.save()
                    
                    transaction = OpenTransaction(stock_id=stock, portfolio_id=portfolio, quantity=quantity, price=price,transaction_type=transaction_type)
                    transaction.save()
                else:
                    return Response({'msg': 'Insufficient balance'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            elif (transaction_type=='S'):
                holding = Holding.objects.filter(portfolio_id=portfolio, stock_id=stock)[0]
               
                if(holding.quantity>=quantity):

                    holding.quantity=holding.quantity-quantity
                    holding.save()
                    transaction = OpenTransaction(stock_id=stock, portfolio_id=portfolio, quantity=quantity, price=price,transaction_type=transaction_type)
                    transaction.save()
                    
                else:
                    return Response({'msg': 'Insufficient quantity'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({'msg': 'Order Placed', 'order_id':transaction.id}, status=status.HTTP_200_OK)
        except:
            return Response({'msg': 'Something went wrong. Please try again.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class IPOView(APIView):
    """
        This view will be used during the initial 6 hours 
        of the event where only buying of stocks will be 
        allowed from the "market" user. 
    """
    @csrf_exempt
    def post(self, request):
        try:
            stock = Stock.objects.filter(name=request.data['stock_name'])[0]
            user = request.user
            # portfolio = Portfolio.objects.filter(user=user)[0]
            portfolio=user.portfolio

            quantity = int(request.data['quantity'])
            #check if person has enough money to buy that much quantity
            if(portfolio.visible_money>=stock.last_traded_price*quantity*1.001):
                if(stock.total_quantity<quantity):
                    return Response({'msg': 'Insufficient quantity'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    
                else:
                    transaction = OpenTransaction(stock_id=stock, portfolio_id=portfolio, quantity=quantity, price=stock.last_traded_price,transaction_type='B')
                    transaction.save()
                    portfolio.visible_money-=stock.last_traded_price*quantity*1.001
                    portfolio.save()
                    return Response({'msg': 'Order Placed', 'order_id':transaction.id}, status=status.HTTP_200_OK)
            else:
                return Response({'msg': 'Insufficient balance'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except:
            return Response({'msg': 'Something went wrong. Please try again.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    

#Helper Function, tested
def ceil_dt(dt, delta):
    return  -(datetime.min - dt) % delta

# #TESTED
class ListLeastFamousStock(APIView):
    """
        This view is used to fetch the least famous stocks
    """
    @csrf_exempt
    def get(self, request):
        stocks=Stock.objects.all()
        data=[]
        #sort the stocks by fame_counter
        stocks=stocks.order_by('fame_counter')
        # print(stocks)
        for stock in stocks:
            data.append({
                'deviation_percentage':stock.deviation_percentage,
                'id':stock.id,
                'name':stock.name,
                'last_traded_price':stock.last_traded_price,
                'fame_counter':stock.fame_counter,
                })
        return Response(data, status=status.HTTP_200_OK)

#TESTED
class ListMostDeviatedStocks(APIView):
    """
        This view is used to fetch the most deviated stocks
    """
    @csrf_exempt
    def get(self, request):
        stocks=Stock.objects.all()
        data=[]
        #sort the stocks by fame_counter
        stocks=stocks.order_by('-deviation_percentage')
        for stock in stocks:
            data.append({
                'id':stock.id,
                'name':stock.name,
                'last_traded_price':stock.last_traded_price,
                'second_last_traded_price':stock.second_last_traded_price,
                'third_last_traded_price':stock.third_last_traded_price,
                'fourth_last_traded_price':stock.fourth_last_traded_price,
                'deviation_percentage':stock.deviation_percentage,
                'fame_counter':stock.fame_counter,
                })
        return Response(data, status=status.HTTP_200_OK)

#TESTED to some extent #integrated
class CancelOrderView(APIView):
    """Cancel an order"""
    @csrf_exempt
    def post(self, request):
        time_left=(timedelta(minutes=3)-ceil_dt(datetime.now(),timedelta(minutes=3))).total_seconds()
        if(time_left<10):
            return Response({'msg': 'Cannot cancel orders less than 15 seconds before processing'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        elif(time_left>150):
            return Response({'msg': 'Cannot cancel order right now, please try again later'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        try:
            user = request.user
            # portfolio = Portfolio.objects.filter(user=user)[0]
            portfolio=user.portfolio

            transaction = OpenTransaction.objects.filter(portfolio_id=portfolio, id=int(request.data['id']))
            if(transaction.count()==0):
                return Response({'msg': 'Transaction not found'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                transaction = transaction[0]
            try:
                if(transaction.transaction_type=='B'):
                    portfolio.visible_money+=transaction.price*transaction.quantity*1.001
                    portfolio.save()
                else:
                    holding = Holding.objects.filter(portfolio_id=portfolio, stock_id=transaction.stock_id)[0]
                    holding.quantity+=transaction.quantity
                    holding.save()
                transaction.delete()
                return Response({'msg': 'Order Deleted'}, status=status.HTTP_200_OK)
            except:
                return Response({'msg': 'Order cannot be cancelled'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except:
            return Response({'msg': 'Something went wrong. Please try again.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class TestSheet(APIView):
    # If modifying these scopes, delete the file token.json.
    # permission_classes
    permission_classes = [AllowAny]
    def get(self,request):
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        # The ID and range of a sample spreadsheet.
        SPREADSHEET_ID = '17WS_og33PQyyCdh6sNOv5TMmp1_ljk0Y0xWCHnVawQo'
        
        creds=None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        #create list of 60 values
        sheet_append=[[]]
        #add 60 values to first list
        for i in range(60):
            sheet_append[0].append(i)
        try:
            service = build('sheets', 'v4', credentials=creds)
            # Call the Sheets API
            sheet = service.spreadsheets()
            #append the list of values into the sheet
            result = sheet.values().append(spreadsheetId=SPREADSHEET_ID, range='A1:A60',
                                                valueInputOption='RAW', body={'values': sheet_append}).execute()                            
        except HttpError as err:
            # print(err)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response({'msg':'done'},status=status.HTTP_200_OK)
    

class AddToWatchList(APIView):
    @csrf_exempt
    def post(self,request):
        try:
            user=request.user
            # portfolio=Portfolio.objects.filter(user=user)[0]
            portfolio=user.portfolio

            stock=Stock.objects.filter(name=request.data['stock_name'])
            if(stock.count()==0):
                return Response({'msg':'Stock not found'},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            stock=stock[0]
            if(stock in portfolio.watchlist.all()):
                return Response({'msg':'Already in watch list'},status=status.HTTP_200_OK)
            portfolio.watchlist.add(stock)
            portfolio.save()
            return Response({'msg':'Added to watch list'},status=status.HTTP_200_OK)
        except:
            return Response({'msg':'Something went wrong. Please try again.'},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ReturnWatchList(APIView):
    @csrf_exempt
    def get(self,request):
        try:
            user=request.user
            # portfolio=Portfolio.objects.filter(user=user)[0]
            portfolio=user.portfolio

            stock_list=portfolio.watchlist.all()
            stocks=[]
            for stock in stock_list:
                data={}
                data['name']= stock.name
                data['last_traded_price']= stock.last_traded_price
                data['deviation']= 100*(stock.last_traded_price-stock.second_last_traded_price)/stock.second_last_traded_price
                data['total_quantity']=  stock.total_quantity
                data['ask_price']= stock.ask_price
                data['bid_price']=stock.bid_price
                data['ipo']=(time.time()>IPO_START_TIME and time.time()<IPO_END_TIME)
                data['logo']=stock.stock_logo

                stocks.append(data)
            return Response({"watchlist":stocks},status=status.HTTP_200_OK)
        except:
            return Response({'msg':'Something went wrong. Please try again.'},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RemoveFromWatchList(APIView):
    @csrf_exempt
    def post(self,request):
        try:
            user=request.user
            # portfolio=Portfolio.objects.filter(user=user)[0]
            portfolio=user.portfolio
            
            stock=Stock.objects.filter(name=request.data['stock_name'])
            if(stock.count()==0):
                return Response({'msg':'Stock not found'},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            stock=stock[0]
            if(stock not in portfolio.watchlist.all()):
                return Response({'msg':'Not in watch list'},status=status.HTTP_200_OK)
            portfolio.watchlist.remove(stock)
            portfolio.save()
            return Response({'msg':'Removed from watch list'},status=status.HTTP_200_OK)
        except:
            return Response({'msg':'Something went wrong. Please try again.'},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#TESTED, Change the default 0's over here
class UpdateStocks(APIView):
    permission_classes = [AllowAny]
    def get(self,request):
        with open("./stocks.csv", mode='r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            for row in reader:
                
                # print(row)
                _,created = Stock.objects.update_or_create(
                        name=row[0],
                        defaults={
                        'total_quantity':row[1],
                        'last_traded_price':row[2],
                        'second_last_traded_price':row[3],
                        'ask_price':row[4],
                        'bid_price':row[5],
                        'stock_logo':row[6]
                        }
                    )
        return Response({'success': 'Stocks Updated'}, status=status.HTTP_200_OK)


class InIPO(APIView):
    def get(self,request):
        if time.time()>IPO_START_TIME and time.time()<IPO_END_TIME:
            return Response({'IPO':'1'})
        else:
            return Response({'IPO':'0'})

class Favourite(APIView):
    def post(self,request):
        user=request.user
        portfolio=user.portfolio
        stock=Stock.objects.filter(name=request.data['stock_name'])[0]
        if stock in portfolio.watchlist.all():
            return Response({'msg':True})
        else:
            return Response({'msg':False})


def calculate_portfolio_values():
    #updating holding prices to current price
    for stock in Stock.objects.all():
        Holding.objects.filter(stock_id=stock).update(price=stock.last_traded_price)
    portfolios = Portfolio.objects.all()
    for portfolio in portfolios:
        holdings = Holding.objects.filter(portfolio_id=portfolio)
        sumt=0
        for holding in holdings:
            sumt += holding.quantity * holding.stock_id.last_traded_price
        portfolio.value=sumt
        portfolio.save()
    #update average price of holdings
    leaderboard_generator()
    

def leaderboard_generator():
    # users = Portfolio.objects.order_by('-value')[:10]
    users=Portfolio.objects.extra(
            select={'fieldsum':'value'},
            order_by=('-fieldsum',)
            )[:10]
    channel_layer = get_channel_layer()
    list=[]

    for user in users:
        if not user.user.is_staff : 
            list.append({"username":user.user.first_name,"email":user.user.email,"value":round(user.value+user.visible_money,2)})
    
    async_to_sync(channel_layer.group_send)(
        'Leaderboard_group', 
        {
            'type':'leaderboard_list', 
            'payload': json.dumps(list)
        }
    )


def stock_list_generator():
    channel_layer = get_channel_layer()
    list=[]
    stocks=Stock.objects.all()
    for stock in stocks:
        data={}
        data['name']= stock.name
        data['total_quantity']=  stock.total_quantity
        data['last_traded_price']= stock.last_traded_price
        data['deviation']= 100*(stock.last_traded_price-stock.second_last_traded_price)/stock.second_last_traded_price
        data['ask_price']= stock.ask_price
        data['bid_price']=stock.bid_price
        data['ipo']=(time.time()>IPO_START_TIME and time.time()<IPO_END_TIME)
        data['logo']=stock.stock_logo

        list.append(data)
    async_to_sync( channel_layer.group_send)(
        'stock_group',
        {
            'type':'stock_updates', 
            'payload': json.dumps(list)
        }
        )
    
