from django.urls import path
from .views import *
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('PlaceOrder/', PlaceOrderView.as_view(), name='register_transaction'),
    path('ActiveOrders/', CurrentActiveOrders.as_view(), name='test'),
    path('IPO/', IPOView.as_view(), name='ipo'),
    path('OrderHistory/', OrderHistory.as_view(), name='order_history'),
    path('CurrentHoldings/', CurrentHoldings.as_view(), name='current_holdings'),
    # path('ListLeastFamousStock/',ListLeastFamousStock.as_view(), name='ListLeastFamousStock'),
    # path('ListMostDeviatedStocks/', ListMostDeviatedStocks.as_view(), name='ListMostDeviatedStocks'),
    path('CancelOrderView/', CancelOrderView.as_view(), name='cancel_transaction'),
    path('UpdateStocks/', UpdateStocks.as_view(), name='update_stocks'),
    path('TestSheet/', TestSheet.as_view(), name='test_sheet'),
    path('AddToWatchList/', AddToWatchList.as_view(), name='add_to_watch_list'),
    path('RemoveFromWatchList/', RemoveFromWatchList.as_view(), name='remove_from_watch_list'),
    path('ReturnWatchList/', ReturnWatchList.as_view(), name='return_watch_list'),
    path('InIPO/', InIPO.as_view(), name='in_ipo'),
    path('Favourite/', Favourite.as_view(), name='favourite'),
]








