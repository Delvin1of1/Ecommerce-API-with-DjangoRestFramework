from rest_framework import viewsets, status, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer
from Cart.models import Cart

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['created_at', 'total_price']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request, 'items': request.data.get('items', [])})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @action(detail=False, methods=['post'])
    def checkout_from_cart(self, request):
        user = request.user
        
        # Get cart
        try:
            cart = Cart.objects.get(user=user)
            if cart.items.count() == 0:
                return Response({"error": "Your cart is empty"}, status=status.HTTP_400_BAD_REQUEST)
        except Cart.DoesNotExist:
            return Response({"error": "Your cart is empty"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate shipping information
        shipping_address = request.data.get('shipping_address')
        phone = request.data.get('phone')
        
        if not shipping_address or not phone:
            return Response({"error": "Shipping address and phone are required"}, 
                        status=status.HTTP_400_BAD_REQUEST)
        
        # Check product stock availability
        for item in cart.items.all():
            if item.product.stock < item.quantity:
                return Response({
                    "error": f"Not enough stock for {item.product.name}. Available: {item.product.stock}"
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create order
        order = Order.objects.create(
            user=user,
            status='pending',
            total_price=cart.total_price,
            shipping_address=shipping_address,
            phone=phone
        )
        
        # Create order items from cart items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )
        
        # We don't clear the cart yet - that happens after successful payment
        
        return Response({
            "message": "Order created successfully. Proceed to payment.",
            "order": OrderSerializer(order).data
        }, status=status.HTTP_201_CREATED)


class OrderItemViewSet(viewsets.ModelViewSet):
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return OrderItem.objects.all()
        return OrderItem.objects.filter(order__user=user)