from .models import Deposits, PiggyBank, Obligation
from rest_framework import serializers
from django.db.models import Sum
from patients.models import Patient


class ObligationSerializerMain(serializers.ModelSerializer):
    class Meta:
        model = Obligation
        fields = ['id', 'amount', 'is_paid', 'when_paid', 'how_paid']
        

class DepositSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deposits
        fields = ['id', 'amount', 'date']


class GetUserHistory(serializers.ModelSerializer):
    deposit = serializers.SerializerMethodField()
    obligations = serializers.SerializerMethodField()
    sum = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = ['obligations', 'deposit', 'sum']

    def get_deposit(self, obj):
        deposit_qs = self.context.get('deposit_qs', [])
        return DepositSerializer(deposit_qs, many=True).data

    def get_obligations(self, obj):
        obligation_qs = self.context.get('obligation_qs', [])
        return ObligationSerializerMain(obligation_qs, many=True).data

    def get_sum(self, obj):
        deposit_qs = self.context.get('deposit_qs', [])
        deposit_sum = deposit_qs.aggregate(total=Sum('amount'))['total'] or 0

        obligation_qs = self.context.get('obligation_qs', [])
        obligation_sum = obligation_qs.filter(to_count=True).aggregate(total=Sum('amount'))['total'] or 0

        return deposit_sum + obligation_sum
    
