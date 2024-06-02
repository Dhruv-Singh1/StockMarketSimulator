from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from celery.decorators import periodic_task, task
from celery.schedules import crontab
import requests
from celery.utils.log import get_task_logger

logger = get_task_logger('__name__')
channel_layer = get_channel_layer()
import json
from users.models import *
import csv
from datetime import datetime, timedelta
from .views import calculate_portfolio_values,stock_list_generator,leaderboard_generator
# from __future__ import print_function
import os.path
from django.db import transaction as tran
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from api.settings import IPO_START_TIME, IPO_END_TIME
import time
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate('api/users/sms-23-b5b14-firebase-adminsdk-vudsg-d692c4667a.json')
app = firebase_admin.initialize_app(cred)
db = firestore.client()

@shared_task(name = "update_price")
def updateTask():
    stocks = Stock.objects.all()
    for stock in stocks:
        stock.second_last_traded_price = stock.last_traded_price


""" @shared_task(name = "print_msg_main")
def processTransaction():
    if time.time()>IPO_START_TIME and time.time()<IPO_END_TIME:
        stocks=Stock.objects.all()
        for stock in stocks:
           if(stock.trading_active==True):
            transactions=OpenTransaction.objects.filter(stock_id=stock).order_by('timestamp')
            
            for transaction in transactions:
                with tran.atomic():
                    if(transaction.quantity<=stock.total_quantity):
                        stock.total_quantity=stock.total_quantity-transaction.quantity
                        transaction.delete()
                        closed_transaction=ClosedTransaction(stock_id=stock,portfolio_id=transaction.portfolio_id,quantity=transaction.quantity,price=transaction.price,transaction_type='B')
                        closed_transaction.save()
                        holding = Holding.objects.filter(portfolio_id=transaction.portfolio_id, stock_id=stock)[0]
                        holding.quantity+=transaction.quantity
                        holding.save()
                    stock.save()
        return
    stocks = Stock.objects.all()
    for stock in stocks:
       if(stock.trading_active==True):
        #store last traded price
        last_traded_price=stock.last_traded_price
        second_last_traded_price=last_traded_price
        buy_transactions = OpenTransaction.objects.filter(stock_id=stock,transaction_type='B').order_by('-price','timestamp')
        sell_transactions = OpenTransaction.objects.filter(stock_id=stock,transaction_type='S').order_by('price','timestamp')

        flag=0
        if(len(buy_transactions)==0 or len(sell_transactions)==0):
            flag=1

        if(flag==0):
            lowest_sell_price = sell_transactions[0].price
            highest_buy_price = buy_transactions[0].price
            
            buy_transactions = list(buy_transactions.filter(price__gte=lowest_sell_price))
            sell_transactions = list(sell_transactions.filter(price__lte=highest_buy_price))
            
            
            for buy_transaction in buy_transactions:
                buy_quantity = buy_transaction.quantity
                processed=0
                accumulated=0
                edited=0
                while(len(sell_transactions)>0 and buy_transaction.price>=sell_transactions[0].price and buy_transaction.quantity>0):
                    sell_quantity = sell_transactions[0].quantity
                    if(buy_transaction.portfolio_id==sell_transactions[0].portfolio_id):
                        sell_transactions.pop(0)

                    elif(sell_quantity<buy_transaction.quantity):
                        edited=1
                        with tran.atomic():
                            buy_transaction.quantity -= sell_quantity
                            buy_transaction.save()
                            stock.last_traded_price=buy_transaction.price
                            stock.save()
                            closed_transaction = ClosedTransaction(stock_id=stock, portfolio_id=sell_transactions[0].portfolio_id, quantity=sell_quantity, price=buy_transaction.price, transaction_type='S')
                            closed_transaction.save()
                            sell_portfolio = Portfolio.objects.filter(id=closed_transaction.portfolio_id.id)[0]
                            sell_transactions[0].delete()
                            sell_portfolio.visible_money += sell_quantity * stock.last_traded_price * 0.999
                            sell_portfolio.save()
                            sell_transactions.pop(0)
                            buy_portfolio=Portfolio.objects.filter(id=buy_transaction.portfolio_id.id)[0]
                            buy_portfolio_holding=Holding.objects.filter(portfolio_id=buy_portfolio, stock_id=stock)[0]
                            buy_portfolio_holding.quantity +=sell_quantity
                            buy_portfolio_holding.save()
                            accumulated+=sell_quantity

                    elif(sell_quantity>buy_transaction.quantity):
                        with tran.atomic():    
                            sell_transactions[0].quantity -= buy_transaction.quantity
                            sell_transactions[0].save()
                            closed_transaction = ClosedTransaction(stock_id=stock, portfolio_id=sell_transactions[0].portfolio_id, quantity=buy_transaction.quantity, price=buy_transaction.price, transaction_type='S')
                            
                            closed_transaction.save()
                            stock.last_traded_price=buy_transaction.price
                            stock.save()
                            closed_transaction = ClosedTransaction(stock_id=stock, portfolio_id=buy_transaction.portfolio_id, quantity=buy_quantity, price=buy_transaction.price, transaction_type='B')
                            closed_transaction.save()
                            buy_transaction.delete()
                            buy_portfolio = Portfolio.objects.filter(id=buy_transaction.portfolio_id.id)[0]
                        
                            buy_portfolio_holding=Holding.objects.filter(portfolio_id=buy_portfolio, stock_id=stock)[0]
                            buy_portfolio_holding.quantity+=buy_transaction.quantity
                            buy_portfolio_holding.save()
                        
                            sell_portfolio = Portfolio.objects.filter(id=buy_transaction.portfolio_id.id)[0]
                            #supressed here
                            sell_portfolio.visible_money =sell_portfolio.visible_money+ buy_transaction.quantity * stock.last_traded_price * 0.999
                            sell_portfolio.save()   
                        
                        processed=1
                        break

                    else:
                        with tran.atomic():
                            closed_transaction = ClosedTransaction(stock_id=stock, portfolio_id=buy_transaction.portfolio_id, quantity=buy_quantity, price=buy_transaction.price, transaction_type='B')
                            closed_transaction.save()
                            closed_transaction = ClosedTransaction(stock_id=stock, portfolio_id=sell_transactions[0].portfolio_id, quantity=sell_quantity, price=buy_transaction.price, transaction_type='S')
                            closed_transaction.save()
                            sell_portfolio = Portfolio.objects.filter(id=sell_transactions[0].portfolio_id.id)[0]
                            sell_portfolio.visible_money += sell_quantity * stock.last_traded_price *0.999
                            sell_portfolio.save()
                            stock.last_traded_price=buy_transaction.price
                            stock.save()
                            buy_portfolio = Portfolio.objects.filter(id=buy_transaction.portfolio_id.id)[0]
                            buy_portfolio_holding=Holding.objects.filter(portfolio_id=buy_portfolio, stock_id=stock)[0]
                            buy_portfolio_holding.quantity +=sell_quantity
                            buy_portfolio_holding.save()

                            buy_transaction.delete()
                            sell_transactions[0].delete()
                            
                            sell_transactions.pop(0)
                        processed=1
                        break


                if(processed==0 and edited==1):
                    with tran.atomic():
                        closed_transaction=ClosedTransaction(stock_id=stock, portfolio_id=buy_transaction.portfolio_id, quantity=accumulated, price=buy_transaction.price, transaction_type='B')
                        closed_transaction.save()
                        buy_transaction.save()
        # sheet_append[0].append(stock.last_traded_price)
        #get highest buy price
        try:
            stock.bid_price=OpenTransaction.objects.filter(stock_id=stock,transaction_type='B').order_by('-price')[0].price
        except:
            stock.bid_price=stock.last_traded_price
        try:
            stock.ask_price=sell_transactions[0].price
        except:
            stock.ask_price=stock.last_traded_price
        
        # To shutdown the stock if there is a 20 percent loss or gain
        price_change_perc = ((stock.last_traded_price - stock.second_last_traded_price)/stock.second_last_traded_price) * 100
        if abs(price_change_perc) >= 20:
            stock.trading_active = False
        

        stock.save()
        Holding.objects.filter(stock_id=stock).update(price=stock.last_traded_price)
        #update all holding value price to its stock last traded price
        

    calculate_portfolio_values()
    stock_list_generator()
    #also suppress portfolio saves above """


def processTransaction(num_chunks, skip):
    if time.time()>IPO_START_TIME and time.time()<IPO_END_TIME:
        stocks=Stock.objects.all()
        paginated_stocks = stocks.limit(num_chunks).offset(skip * num_chunks)

        for stock in paginated_stocks:
           if(stock.trading_active==True):
            transactions=OpenTransaction.objects.filter(stock_id=stock).order_by('timestamp')
            
            for transaction in transactions:
                with tran.atomic():
                    if(transaction.quantity<=stock.total_quantity):
                        stock.total_quantity=stock.total_quantity-transaction.quantity
                        transaction.delete()
                        closed_transaction=ClosedTransaction(stock_id=stock,portfolio_id=transaction.portfolio_id,quantity=transaction.quantity,price=transaction.price,transaction_type='B')
                        closed_transaction.save()
                        holding = Holding.objects.filter(portfolio_id=transaction.portfolio_id, stock_id=stock)[0]
                        holding.quantity+=transaction.quantity
                        holding.save()
                    stock.save()
        return
    
    stocks = Stock.objects.all()
    paginated_stocks = stocks.limit(num_chunks).offset(skip * num_chunks)

    for stock in paginated_stocks:
       if(stock.trading_active==True):
        #store last traded price
        last_traded_price=stock.last_traded_price
        second_last_traded_price=last_traded_price
        buy_transactions = OpenTransaction.objects.filter(stock_id=stock,transaction_type='B').order_by('-price','timestamp')
        sell_transactions = OpenTransaction.objects.filter(stock_id=stock,transaction_type='S').order_by('price','timestamp')

        flag=0
        if(len(buy_transactions)==0 or len(sell_transactions)==0):
            flag=1

        if(flag==0):
            lowest_sell_price = sell_transactions[0].price
            highest_buy_price = buy_transactions[0].price
            
            buy_transactions = list(buy_transactions.filter(price__gte=lowest_sell_price))
            sell_transactions = list(sell_transactions.filter(price__lte=highest_buy_price))
            
            
            for buy_transaction in buy_transactions:
                buy_quantity = buy_transaction.quantity
                processed=0
                accumulated=0
                edited=0
                while(len(sell_transactions)>0 and buy_transaction.price>=sell_transactions[0].price and buy_transaction.quantity>0):
                    sell_quantity = sell_transactions[0].quantity
                    if(buy_transaction.portfolio_id==sell_transactions[0].portfolio_id):
                        sell_transactions.pop(0)

                    elif(sell_quantity<buy_transaction.quantity):
                        edited=1
                        with tran.atomic():
                            buy_transaction.quantity -= sell_quantity
                            buy_transaction.save()
                            stock.last_traded_price=buy_transaction.price
                            stock.save()
                            closed_transaction = ClosedTransaction(stock_id=stock, portfolio_id=sell_transactions[0].portfolio_id, quantity=sell_quantity, price=buy_transaction.price, transaction_type='S')
                            closed_transaction.save()
                            sell_portfolio = Portfolio.objects.filter(id=closed_transaction.portfolio_id.id)[0]
                            sell_transactions[0].delete()
                            sell_portfolio.visible_money += sell_quantity * stock.last_traded_price * 0.999
                            sell_portfolio.save()
                            sell_transactions.pop(0)
                            buy_portfolio=Portfolio.objects.filter(id=buy_transaction.portfolio_id.id)[0]
                            buy_portfolio_holding=Holding.objects.filter(portfolio_id=buy_portfolio, stock_id=stock)[0]
                            buy_portfolio_holding.quantity +=sell_quantity
                            buy_portfolio_holding.save()
                            accumulated+=sell_quantity

                    elif(sell_quantity>buy_transaction.quantity):
                        with tran.atomic():    
                            sell_transactions[0].quantity -= buy_transaction.quantity
                            sell_transactions[0].save()
                            closed_transaction = ClosedTransaction(stock_id=stock, portfolio_id=sell_transactions[0].portfolio_id, quantity=buy_transaction.quantity, price=buy_transaction.price, transaction_type='S')
                            
                            closed_transaction.save()
                            stock.last_traded_price=buy_transaction.price
                            stock.save()
                            closed_transaction = ClosedTransaction(stock_id=stock, portfolio_id=buy_transaction.portfolio_id, quantity=buy_quantity, price=buy_transaction.price, transaction_type='B')
                            closed_transaction.save()
                            buy_transaction.delete()
                            buy_portfolio = Portfolio.objects.filter(id=buy_transaction.portfolio_id.id)[0]
                        
                            buy_portfolio_holding=Holding.objects.filter(portfolio_id=buy_portfolio, stock_id=stock)[0]
                            buy_portfolio_holding.quantity+=buy_transaction.quantity
                            buy_portfolio_holding.save()
                        
                            sell_portfolio = Portfolio.objects.filter(id=buy_transaction.portfolio_id.id)[0]
                            #supressed here
                            sell_portfolio.visible_money =sell_portfolio.visible_money+ buy_transaction.quantity * stock.last_traded_price * 0.999
                            sell_portfolio.save()   
                        
                        processed=1
                        break

                    else:
                        with tran.atomic():
                            closed_transaction = ClosedTransaction(stock_id=stock, portfolio_id=buy_transaction.portfolio_id, quantity=buy_quantity, price=buy_transaction.price, transaction_type='B')
                            closed_transaction.save()
                            closed_transaction = ClosedTransaction(stock_id=stock, portfolio_id=sell_transactions[0].portfolio_id, quantity=sell_quantity, price=buy_transaction.price, transaction_type='S')
                            closed_transaction.save()
                            sell_portfolio = Portfolio.objects.filter(id=sell_transactions[0].portfolio_id.id)[0]
                            sell_portfolio.visible_money += sell_quantity * stock.last_traded_price *0.999
                            sell_portfolio.save()
                            stock.last_traded_price=buy_transaction.price
                            stock.save()
                            buy_portfolio = Portfolio.objects.filter(id=buy_transaction.portfolio_id.id)[0]
                            buy_portfolio_holding=Holding.objects.filter(portfolio_id=buy_portfolio, stock_id=stock)[0]
                            buy_portfolio_holding.quantity +=sell_quantity
                            buy_portfolio_holding.save()

                            buy_transaction.delete()
                            sell_transactions[0].delete()
                            
                            sell_transactions.pop(0)
                        processed=1
                        break


                if(processed==0 and edited==1):
                    with tran.atomic():
                        closed_transaction=ClosedTransaction(stock_id=stock, portfolio_id=buy_transaction.portfolio_id, quantity=accumulated, price=buy_transaction.price, transaction_type='B')
                        closed_transaction.save()
                        buy_transaction.save()
        # sheet_append[0].append(stock.last_traded_price)
        #get highest buy price
        try:
            stock.bid_price=OpenTransaction.objects.filter(stock_id=stock,transaction_type='B').order_by('-price')[0].price
        except:
            stock.bid_price=stock.last_traded_price
        try:
            stock.ask_price=sell_transactions[0].price
        except:
            stock.ask_price=stock.last_traded_price
        
        # To shutdown the stock if there is a 20 percent loss or gain
        price_change_perc = ((stock.last_traded_price - stock.second_last_traded_price)/stock.second_last_traded_price) * 100
        if abs(price_change_perc) >= 20:
            stock.trading_active = False
        

        stock.save()
        Holding.objects.filter(stock_id=stock).update(price=stock.last_traded_price)
        #update all holding value price to its stock last traded price
        

    calculate_portfolio_values()
    stock_list_generator()
    #also suppress portfolio saves above


@shared_task(name = "print_msg_main")
def processTransaction_call():
    stocks = Stock.objects.all()
    total_stocks = stocks.count()

    #each chunk will contain 1 stock
    num_chunks = 1

    quo, remainder = divmod(total_stocks, num_chunks)
    jobs = quo

    if remainder:
        jobs = jobs + 1
    
    skip = 0
    for i in range(jobs):
        processTransaction.delay(num_chunks, skip)

        skip = skip + 1


@shared_task(name = "print_msg_main_x")
def processChannels():
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
    users=Portfolio.objects.extra(
            select={'fieldsum':'value+visible_money'},
            order_by=('-fieldsum',)
            )[:10]
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
    

    
@shared_task(name = "log_sheet")
def sheet_update():
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    SPREADSHEET_ID = '17WS_og33PQyyCdh6sNOv5TMmp1_ljk0Y0xWCHnVawQo'
    creds=None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    stocks=Stock.objects.all()
    for stock in stocks:
        i = stock.last_traded_price
        doc_ref = db.collection(u'graphs').document(stock.name)
        try:
            doc_ref.update({u'prices': firestore.ArrayUnion([i])})
        except:
            doc_ref.set({u'prices': [i]})

""" @shared_task(name = "log_sheet")
def sheet_update():
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    SPREADSHEET_ID = '17WS_og33PQyyCdh6sNOv5TMmp1_ljk0Y0xWCHnVawQo'
    creds=None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    sheet_append=[[]]
    stocks=Stock.objects.all()
    for stock in stocks:
        sheet_append[0].append(stock.last_traded_price)
    try:
        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()
        result = sheet.values().append(spreadsheetId=SPREADSHEET_ID,range='A1:A60',
                                            valueInputOption='RAW', body={'values': sheet_append}).execute()        
    except HttpError as err:
        print(err) """



