from .models import Deposits, PiggyBank, Obligation
from rest_framework import serializers


class ObligationSerializerMain(serializers.ModelSerializer):
    class Meta:
        model = Obligation
        fields = ['id', 'ammount', 'is_paid', 'when_paid', 'how_paid']
        

class DepositSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deposits
        fields = ['id', ]