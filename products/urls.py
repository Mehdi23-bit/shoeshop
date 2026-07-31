from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('cart/', views.cart, name='cart'),
    path('cart/data/', views.cart_data, name='cart_data'),          # <-- new: JSON for the drawer
    path('cart/add/<int:shoe_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:shoe_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:shoe_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('clear-cart/', views.clear_cart, name='clear_cart'),
    path('api/cart-count/', views.get_cart_count, name='cart_count'),
    path('order/<str:order_number>/', views.order_confirmation, name='order_confirmation'),

]
