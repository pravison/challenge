from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Inquiries(models.Model):
    website_url = models.URLField(blank=True, null=True)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone_number = models.CharField(max_length=25)
    plan = models.CharField(max_length=25)
    

    def __str__(self):
        return self.name

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    date_joined = models.DateTimeField(auto_now_add = True)
    def __str__(self):
        return self.user.first_name 
