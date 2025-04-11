from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet, PaystackWebhookView

router = DefaultRouter()
router.register(r'', PaymentViewSet, basename='payment')

urlpatterns = [
    path('', include(router.urls)),
    path('initialize/', PaymentViewSet.as_view({'post': 'initialize'}), name='initialize-payment'),
    path('verify/', PaymentViewSet.as_view({'post': 'verify'}), name='verify-payment'),
    path('webhook/', PaystackWebhookView.as_view(), name='paystack-webhook'),
]