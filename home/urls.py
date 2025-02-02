from django.urls import path, include
from . import views
urlpatterns = [
    path('', views.index, name='index'),
    path('register-user/', views.register_user, name='register_user'),
    path('login-user/', views.login_user, name='login_user'),
    path('logout-user/', views.logout_user, name='logout_user'),
    path('pricing/', views.pricing, name='pricing'),
    path('profile/', views.profile, name='profile'),
    # path('<slug:slug>/landing-page/', views.audience_landing_page, name='audience_landing_page'),
    # path('subscribe-newsleter/', views.subscribe, name='subscribe'),
    # path('privacy-policy/', views.privacy_policy, name='privacy_policy'),

    
    # path('join-our-patnership-team/', views.join_affliate_team, name='join_affliate_team'),
    # path('patners-dashboard/', views.affiliate_dashboard, name='affiliate_dashboard'),

    path('request-reset-code/', views.request_reset_code, name='request_reset_code'),
    path('verify-reset-code/', views.verify_reset_code, name='verify_reset_code'),
    path('reset-password/', views.reset_password, name='reset_password'),
    ]
   