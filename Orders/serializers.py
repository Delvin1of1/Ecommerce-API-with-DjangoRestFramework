from rest_framework import serializers
from .models import Order, OrderItem
from Products.serializers import ProductSerializer

class OrderItemSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source='product', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_details', 'quantity', 'price']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user = serializers.ReadOnlyField(source='user.username')
    
    class Meta:
        model = Order
        fields = ['id', 'user', 'status', 'total_price', 'shipping_address', 
                  'phone', 'items', 'created_at', 'updated_at']
        read_only_fields = ['total_price']

    def create(self, validated_data):
        items_data = self.context.get('items', [])
        total_price = sum(item.get('price', 0) * item.get('quantity', 0) for item in items_data)
        
        validated_data['total_price'] = total_price
        validated_data['user'] = self.context['request'].user
        
        order = Order.objects.create(**validated_data)
        
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
            
            # Update product stock
            product = item_data['product']
            product.stock -= item_data['quantity']
            product.save()
            
        return order
