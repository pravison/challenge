from django.urls import path
from . import views
urlpatterns = [
    path('inquire/', views.inquire, name='inquire')
]
   