from django.db import models
from django.utils.timezone import now
from datetime import datetime, date , timedelta
from django.contrib.auth.models import User
from customers.models import Customer
import uuid

# Create your models here.
class Business(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    business_name = models.CharField(max_length=250, unique=True)
    slug = models.CharField(max_length=250, unique=True)
    phone_number = models.CharField(max_length=250)
    location = models.CharField(max_length=250)
    address = models.TextField(max_length=1000)
    description = models.TextField(blank=True, help_text='describe what you do')
    subscription_plan = models.CharField(max_length=250, blank=True)
    customers = models.ManyToManyField(Customer, blank=True)
    date_joined = models.DateTimeField(auto_now_add = True)

    def __str__(self):
        return self.business_name
    
class  Staff(models.Model):
    user = models.ForeignKey(User, on_delete= models.CASCADE, related_name='staff')
    business = models.ForeignKey(Business, on_delete= models.CASCADE, related_name='staff')
    date_joined = models.DateTimeField(auto_now_add = True)
    def __str__(self):
        return f'{self.user.first_name} - {self.business.business_name}'

# class staffAdd(models.Model):
#     code = models.CharField(max_length=10, editable=False, unique=True)
#     created_at = models.DateTimeField(default=now)

#     user = models.OneToOneField(User, on_delete=models.CASCADE)    is_valid = models.BooleanField(default=True)

#     def is_expired(self):
#         # Expire the code after 10 minutes (adjust as needed)
#         return (now() - self.created_at).total_seconds() > 1200

#     class Meta:
#         constraints = [
#             models.UniqueConstraint(
#                 fields=['user'], condition=models.Q(is_valid=True), name='unique_valid_code_per_user'
#             )
#         ]




class Coupone(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='coupone')
    customer = models.ForeignKey(Customer, blank=True, null=True, on_delete=models.SET_NULL, related_name='coupone')
    code = models.CharField(max_length=8, unique=True)
    coupone_type = models.CharField(max_length=100, choices=(('redeemed individually', 'redeemed individually'), ('stacked up', 'stacked up'), ('direct ticket to a challenge', 'direct ticket to a challenge'),))
    discount = models.IntegerField(default=10, help_text='percentage discount')
    date_created = models.DateField(auto_now_add=True)
    expiry_in = models.IntegerField(default=6, help_text='number of days before coupone expires')
    used = models.BooleanField(default=False)
    created_by = models.ForeignKey(Staff, blank=True, null=True, on_delete=models.SET_NULL)
    
    def __str__(self):
        return self.code
    
    @property
    def expiry_date(self):
        return self.date_created + timedelta(days=self.expiry_in)
    @property
    def time_remaining(self):
        now = datetime.now()
        expiry_datetime = datetime.combine(self.expiry_date, datetime.max.time()) # expirey at 23:59:59
        remaining_seconds = (expiry_datetime - now).total_seconds()
        if remaining_seconds > 86400: # more than a day
            return f" {int(remaining_seconds//86400)} days"
        elif remaining_seconds > 0:
            return f" {int(remaining_seconds//3600)} hours"
        else:
            return 'Expired'
    
    



class StoreChallenge(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='challenges')
    challenge_type = models.CharField(max_length=100, choices=(('daily challenge', 'daily challenge'), ('weekly challenge', 'weekly challenge'), ('monthly challenge', 'monthly challenge'), ('yearly challenge', 'yearly challenge')))
    challenge_name = models.CharField(max_length=200)
    challenge_reward = models.CharField(max_length=500, help_text='whats the reward for the challenge')
    target_winners = models.IntegerField(help_text='how many winners do you want for this challenge')
    day_of_the_challenge = models.DateField(auto_now_add=True)
    participants = models.ManyToManyField(Coupone, blank=True, related_name='participants')
    winners = models.ManyToManyField(Coupone, blank=True, related_name='winners')
    closed = models.BooleanField(default=False)
    date_created = models.DateField(auto_now_add=True)
    created_by = models.ForeignKey(Staff, blank=True, null=True, on_delete=models.SET_NULL)
    
    def __str__(self):
        return self.challenge_name


class LoyaltyPoint(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='business')
    customer = models.ForeignKey(Customer, blank=True, null=True, on_delete=models.SET_NULL)
    purchase_value = models.IntegerField()
    average_purchase_per_point = models.IntegerField(default=100) 
    points_earned = models.IntegerField()
    def __str__(self):
        return f'{self.customer.user.first_name} {self.customer.user.first_name} points earned: {self.points_earned}'


