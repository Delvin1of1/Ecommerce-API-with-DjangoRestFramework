from rest_framework import serializers
from .models import Payment
from Orders.serializers import OrderSerializer

class PaymentSerializer(serializers.ModelSerializer):
    order_details = OrderSerializer(source='order', read_only=True)
    
    class Meta:
        model = Payment
        fields = ['id', 'user', 'order', 'order_details', 'amount', 'reference', 
                  'status', 'paystack_payment_id', 'payment_method', 'created_at', 'updated_at']
        read_only_fields = ['reference', 'status', 'paystack_payment_id', 'payment_method']


class PaymentInitSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    email = serializers.EmailField()
    callback_url = serializers.URLField(required=False)


class PaymentVerificationSerializer(serializers.Serializer):
    reference = serializers.CharField()