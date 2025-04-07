from django.contrib import admin
from .models import Business, Staff, StoreChallenge, Coupone, LoyaltyPoint, LoyaltyPointsCategory, RefferralCode, Product, ScanCount

# Register your models here.
admin.site.register(Business)
admin.site.register(Staff)
admin.site.register(StoreChallenge)
admin.site.register(Coupone)
admin.site.register(LoyaltyPoint)
admin.site.register(LoyaltyPointsCategory)
admin.site.register(RefferralCode)
admin.site.register(Product)
admin.site.register(ScanCount)