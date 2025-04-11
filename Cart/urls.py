from django.urls import path
from .views import CartViewSet

urlpatterns = [
    path('', CartViewSet.as_view({'get': 'my_cart'}), name='my-cart'),
    path('add/', CartViewSet.as_view({'post': 'add_item'}), name='add-to-cart'),
    path('update/', CartViewSet.as_view({'post': 'update_item'}), name='update-cart-item'),
    path('remove/', CartViewSet.as_view({'post': 'remove_item'}), name='remove-from-cart'),
    path('clear/', CartViewSet.as_view({'post': 'clear'}), name='clear-cart'),
]
