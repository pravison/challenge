from django.urls import path
from . import views
urlpatterns = [
    path('add-business/', views.add_business, name='add_business'),
    path('add-coupon/', views.add_coupon, name='add_coupon'),
    path('<slug:slug>/view_coupon/', views.view_coupon, name='view_coupon'),
    # path('generate-coupon/', views.generate_coupon, name='generate_coupon'),
    path('', views.business, name='business'),
    path('<slug:slug>/', views.dashboard, name='dashboard'),
    path('<slug:slug>/add-staff', views.add_staff, name='add_staff'),
    path('<slug:slug>/customers/', views.customers, name='customers'),
    path('<slug:slug>/add-customer/', views.add_customer, name='add_customer'),
    path('<slug:slug>/create-coupones/', views.create_coupones, name='create_coupones'),
    path('<slug:slug>/coupones/', views.coupones, name='coupones'),
    path('<slug:slug>/create-store-Challenge/', views.create_store_challenge, name='create_store_challenge'),
    path('<slug:slug>/store-challenges/', views.store_challenges, name='store_challenges'),
    path('<slug:slug>/view-store-challenge/', views.view_store_challenge, name='view_store_challenge'),
    path('<slug:slug>/loyalty-points-category/', views.loyalty_points_category, name='loyalty_points_category'),
    path('<slug:slug>/edit-loyalty-category/', views.edit_loyalty_category, name='edit_loyalty_category'),
    path('<slug:slug>/add-loyalty-points-to-customer/', views.add_loyalty_points_to_customer, name='add_loyalty_points_to_customer'),
    path('<slug:slug>/loyalty-points/', views.loyalty_points, name='loyalty_points'),
    path('<slug:slug>/redeemed-loyalty-points/', views.redeemed_loyalty_points, name='redeemed_loyalty_points'),
]