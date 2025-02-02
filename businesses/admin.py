from django.contrib import admin
from .models import Business, Staff, StoreChallenge, Coupone

# Register your models here.
admin.site.register(Business)
admin.site.register(Staff)
admin.site.register(StoreChallenge)
admin.site.register(Coupone)