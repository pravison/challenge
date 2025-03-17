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


class Coupone(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='coupone')
    customer = models.ForeignKey(Customer, blank=True, null=True, on_delete=models.SET_NULL, related_name='coupone')
    code = models.CharField(max_length=8, unique=True)
    coupone_apply_to = models.CharField(max_length=100, choices=(('all products', 'all products'), ('specific products', 'specific products')))
    coupone_type = models.CharField(max_length=100, choices=(('redeemed individually', 'redeemed individually'), ('stacked up', 'stacked up'), ('direct ticket to a challenge', 'direct ticket to a challenge'), ('refferal coupon', 'refferal coupon'))) #, ('buy x get y product free coupon', 'buy x get y product free coupon')
    # conditions for coupon to apply
    # spend_x = models.IntegerField(default=10, null=True, blank=True, help_text='purchase value required for coupon to apply')
    # buy_x = models.IntegerField(default=10, null=True, blank=True, help_text='number of products customers has to buy for coupon to apply')
    # get_y = models.IntegerField(default=10, null=True, blank=True, help_text='number of products customer gets for free ') 
    # leave get_y empty if you want discount to be applied only if customer purchases certain number of product 
    # if spend_x and buy_x are empty the dicount will be applied without conditions
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

#because i hade earlier associated business with cutomers with many to many relationship using customers field in Business model
# will update the code to use this table    
class BusinessCustomer(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE) 
    total_loyal_points = models.IntegerField(default=0)
    reffered_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, help_text='user who reffered customer')
    refferal_code = models.CharField(max_length=8, unique=True, null=True, blank=True, help_text='code customer will use to reffer other customers')
    def __str__(self):
        return f'{self.customer} - {self.total_loyal_points}'      

class StoreChallenge(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='challenges')
    challenge_type = models.CharField(max_length=100, choices=(('daily challenge', 'daily challenge'), ('weekly challenge', 'weekly challenge'), ('monthly challenge', 'monthly challenge'), ('yearly challenge', 'yearly challenge')))
    challenge_name = models.CharField(max_length=200)
    challenge_reward = models.CharField(max_length=500, help_text='whats the reward for the challenge')
    target_winners = models.IntegerField(help_text='how many winners do you want for this challenge')
    day_of_the_challenge = models.DateField(auto_now_add=True)
    participants = models.ManyToManyField(Coupone, blank=True, related_name='participants')
    winners = models.ManyToManyField(Coupone, blank=True, related_name='winners')
    featured = models.BooleanField(default=False)
    closed = models.BooleanField(default=False)
    date_created = models.DateField(auto_now_add=True)
    created_by = models.ForeignKey(Staff, blank=True, null=True, on_delete=models.SET_NULL)
    
    def __str__(self):
        return self.challenge_name


class LoyaltyPointsCategory(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='points_category')
    category = models.CharField(max_length=100, choices=(('points on purchases made', 'points on purchases made'), ('points on visiting the store', 'points on visiting the store'), ('points on refferal sales', 'points on refferal sales'), ('points on bringing friends to the store', 'points on bringing friends to the store')))
    total_value_for_a_point = models.IntegerField( help_text=" for purchase made what purchase value equals a point, for visits how many visits eaquals apoint, for refferal sales whats sales value equals a point, and for friends brought to the store how many friends equals a point")
    redemed_at_how_much_per_point = models.FloatField(default=0.50)
    edited_by = models.ForeignKey(Staff, blank=True, null=True, on_delete=models.SET_NULL)
    def __str__(self):
        return self.category


class LoyaltyPoint(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='points')
    customer = models.ForeignKey(Customer, blank=True, null=True, on_delete=models.SET_NULL)
    category = models.ForeignKey(LoyaltyPointsCategory, blank=True, null=True, on_delete=models.SET_NULL)
    purchase_value = models.IntegerField()
    points_earned = models.IntegerField()
    added_by = models.CharField(max_length=200)

    def __str__(self):
        return f'{self.customer.user.first_name} {self.customer.user.first_name} points earned: {self.points_earned}'

class RefferralCode(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='refferal')
    customer = models.ForeignKey(Customer, blank=True, null=True, on_delete=models.SET_NULL)
    code = models.CharField(max_length=8, unique=True)
    def __str__(self):
        return f'{self.customer} - {self.code}'
