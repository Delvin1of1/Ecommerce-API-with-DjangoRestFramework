from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, OrderItemViewSet

router = DefaultRouter()
router.register(r'', OrderViewSet, basename='order')
router.register(r'items', OrderItemViewSet, basename='orderitem')

urlpatterns = [
    path('', include(router.urls)),
    path('checkout-from-cart/', OrderViewSet.as_view({'post': 'checkout_from_cart'}), name='checkout-from-cart'),
]