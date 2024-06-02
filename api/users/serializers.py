from attr import fields
from rest_framework import serializers
from .models import *



class TransactionSerializer(serializers.ModelSerializer):
   
    stock_id = serializers.SlugRelatedField(
        many= False,
        read_only=True,
        slug_field='stock_id'
    
    )
    # check if buyer has enough money to buy his demanded stock quantity & if seller has enough stocks in his protfolio 


    # portfolio_id = serializers.SlugRelatedField(
    #     many= False,
    #     read_only=True,
    #     slug_field='portfolio_id'
    # )
    # status= '0'
    # if  portfolio_id :
    #     print("not found")
    # print(stock_id)

    class Meta:
        model = OpenTransaction
        exclude=('timestamp',)
    def __init__(self, *args, **kwargs):
        super(TransactionSerializer, self).__init__(*args, **kwargs)