from django.urls import path
from .consumers import *

websocket_urlpatterns = [
    path('notification/news/', NewsConsumer.as_asgi()),
    path('notification/leaderboard/',LeaderboardConsumer.as_asgi()),
    path('notification/portfolio/<str:room_name>/',PortfolioConsumer.as_asgi()),
    path('notification/stocks/',StockPriceConsumer.as_asgi()),
]

