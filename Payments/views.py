import json
import uuid
import hmac
import hashlib
import requests
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from Orders.models import Order
from Cart.models import Cart
from .models import Payment, PaystackWebhookData
from .serializers import PaymentSerializer, PaymentInitSerializer, PaymentVerificationSerializer

class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Payment.objects.all()
        return Payment.objects.filter(user=user)
    
    @action(detail=False, methods=['post'])
    def initialize(self, request):
        """Initialize a payment with Paystack"""
        serializer = PaymentInitSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        order_id = serializer.validated_data['order_id']
        email = serializer.validated_data['email']
        callback_url = serializer.validated_data.get('callback_url', '')
        
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if payment already exists for this order
        if Payment.objects.filter(order=order).exists():
            return Response({"error": "Payment already exists for this order"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate unique reference
        reference = f"pay_{uuid.uuid4().hex[:12]}"
        
        # Create payment record
        payment = Payment.objects.create(
            user=request.user,
            order=order,
            amount=order.total_price,
            reference=reference
        )
        
        # Initialize payment with Paystack
        url = f"{settings.PAYSTACK_BASE_URL}/transaction/initialize"
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "email": email,
            "amount": int(order.total_price * 100),  # Paystack expects amount in kobo (100 kobo = 1 Naira)
            "reference": reference,
            "callback_url": callback_url,
            "metadata": {
                "order_id": order.id,
                "user_id": request.user.id
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response_data = response.json()
            
            if response.status_code == 200 and response_data['status']:
                # Update payment with authorization URL
                return Response({
                    "status": "success",
                    "message": "Payment initialized",
                    "payment": PaymentSerializer(payment).data,
                    "authorization_url": response_data['data']['authorization_url'],
                    "access_code": response_data['data']['access_code'],
                    "reference": reference
                })
            else:
                # If Paystack initialization failed, delete the payment
                payment.delete()
                return Response({
                    "status": "failed",
                    "message": "Failed to initialize payment",
                    "paystack_error": response_data.get('message', 'Unknown error')
                }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            # If there was an exception, delete the payment
            payment.delete()
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def verify(self, request):
        """Verify a payment with Paystack"""
        serializer = PaymentVerificationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        reference = serializer.validated_data['reference']
        
        try:
            payment = Payment.objects.get(reference=reference)
        except Payment.DoesNotExist:
            return Response({"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Verify with Paystack
        url = f"{settings.PAYSTACK_BASE_URL}/transaction/verify/{reference}"
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers)
            response_data = response.json()
            
            if response.status_code == 200 and response_data['status']:
                transaction_data = response_data['data']
                
                # Update payment status based on Paystack response
                if transaction_data['status'] == 'success':
                    payment.status = 'success'
                    payment.paystack_payment_id = transaction_data.get('id')
                    payment.payment_method = transaction_data.get('channel')
                    payment.save()
                    
                    # Update order status to processing after successful payment
                    order = payment.order
                    order.status = 'processing'
                    order.save()
                    
                    # Clear the cart after successful payment
                    try:
                        cart = Cart.objects.get(user=request.user)
                        cart.items.all().delete()
                    except Cart.DoesNotExist:
                        pass
                    
                    return Response({
                        "status": "success",
                        "message": "Payment verified successfully",
                        "payment": PaymentSerializer(payment).data
                    })
                else:
                    payment.status = 'failed'
                    payment.save()
                    return Response({
                        "status": "failed",
                        "message": "Payment verification failed",
                        "payment": PaymentSerializer(payment).data
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    "status": "error",
                    "message": "Failed to verify payment",
                    "paystack_error": response_data.get('message', 'Unknown error')
                }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaystackWebhookView(APIView):
    """Handle Paystack webhook notifications"""
    permission_classes = []  
    
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
       
        paystack_signature = request.headers.get('X-Paystack-Signature')
        if not paystack_signature:
            return HttpResponse(status=400)
        
        # Get request body
        payload = request.body
        computed_signature = hmac.new(
            key=settings.PAYSTACK_SECRET_KEY.encode(),
            msg=payload,
            digestmod=hashlib.sha512
        ).hexdigest()
        
        # Verify signature
        if computed_signature != paystack_signature:
            return HttpResponse(status=401)
        
        # Process webhook
        try:
            payload_dict = json.loads(payload)
            event = payload_dict.get('event')
            
            
            webhook_data = PaystackWebhookData.objects.create(
                payload=payload_dict,
                event=event
            )
            
           
            if event == 'charge.success':
                self.process_successful_charge(payload_dict)
                webhook_data.processed = True
                webhook_data.save()
            
            return HttpResponse(status=200)
        
        except Exception as e:
            return HttpResponse(str(e), status=500)
    
    def process_successful_charge(self, payload):
        """Process a successful charge webhook"""
        data = payload.get('data', {})
        reference = data.get('reference')
        
        if not reference:
            return
        
        try:
            payment = Payment.objects.get(reference=reference)
            
            # Update payment status
            payment.status = 'success'
            payment.paystack_payment_id = data.get('id')
            payment.payment_method = data.get('channel')
            payment.save()
            
            # Update order status
            order = payment.order
            order.status = 'processing'
            order.save()
            
            # Clear the user's cart
            try:
                cart = Cart.objects.get(user=payment.user)
                cart.items.all().delete()
            except Cart.DoesNotExist:
                pass
                
        except Payment.DoesNotExist:
            pass