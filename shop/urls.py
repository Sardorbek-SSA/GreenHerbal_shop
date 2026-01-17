from django.urls import path
from . import views

app_name = 'shop' 

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),

    path('add-to-cart/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:pk>/', views.remove_from_cart, name='remove_from_cart'),
    path('clear-cart/', views.clear_cart, name='clear_cart'),
    path('cart/', views.cart_view, name='cart_view'),

    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),

    path('checkout/', views.checkout, name='checkout'),
    
    path('order-confirmation/', views.order_confirmation, name='order_confirmation'),
    
    path('track-order/', views.track_order, name='track_order'),
    path('my-orders/', views.my_orders, name='my_orders'),
]