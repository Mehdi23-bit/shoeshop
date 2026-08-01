from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('cart/', views.cart, name='cart'),
    path('cart/place-order/', views.place_order, name='place_order'),
    path('cart/data/', views.cart_data, name='cart_data'),          # <-- new: JSON for the drawer
    path('cart/add/<int:shoe_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:shoe_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:shoe_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('clear-cart/', views.clear_cart, name='clear_cart'),
    path('api/cart-count/', views.get_cart_count, name='cart_count'),
    path('order/<str:order_number>/', views.order_confirmation, name='order_confirmation'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/orders/', views.admin_orders, name='admin_orders'),
    path('dashboard/orders/<str:order_number>/', views.admin_order_detail, name='admin_order_detail'),
    path('dashboard/products/', views.admin_products, name='admin_products'),
    path('dashboard/products/add/', views.admin_product_form, name='admin_product_add'),
    path('dashboard/products/<int:shoe_id>/edit/', views.admin_product_form, name='admin_product_edit'),
    path('dashboard/products/<int:shoe_id>/delete/', views.admin_product_delete, name='admin_product_delete'),
    path('dashboard/login/', views.admin_login, name='admin_login'),
    path('dashboard/logout/', views.admin_logout, name='admin_logout'),

]
