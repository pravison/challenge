from django.shortcuts import render, redirect
from django.db import models
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import date, timedelta
from django.contrib.auth.models import User
import uuid
from django.utils.text import slugify
from .models import Business, Staff, Coupone, StoreChallenge
from customers.models import Customer
from .decorators import team_member_required

# Create your views here.

@login_required(login_url="/login-user/")
def add_business(request):
    pricing_plan = request.GET.get('pricing_plan') or ''
    if pricing_plan == '':
        messages.success(request, 'Choose Pricing Plan First')
        return redirect('pricing')
    context = {
         'pricing_plan': pricing_plan
    }
    if request.method == "POST":
        business_name = request.POST.get('business_name')
        phone_number = request.POST.get('phone_number')
        location = request.POST.get('location')
        address = request.POST.get('address')
        description = request.POST.get('description')

        if Business.objects.filter(business_name=business_name).exists():
            messages.success(request, 'Business Name  already exists.')
            messages.success(request, 'Choose another name or add some letters!')
            return redirect('add_business')

        owner =request.user
        slug=slugify(business_name)
        subscription_plan = pricing_plan
        business = Business.objects.create(business_name=business_name, slug=slug, phone_number=phone_number, location=location, address=address, description=description, owner=owner, subscription_plan=subscription_plan)
        
        # login user
        customer = Customer.objects.filter(user=request.user).first()
        if not customer:
            customer = Customer.objects.create(user=request.user)
        business.customers.add(customer) 
        if not Staff.objects.filter(user=request.user, business=business).exists():
                Staff.objects.create(
                    user=request.user,
                    business=business
                )
        messages.success(request, 'Business Account Created Successfuly')  
        return redirect('dashboard', slug)
    
    return render(request, 'business/add-business.html', context)

@login_required(login_url="/login-user/")
def add_coupon(request):
    if request.method == "POST":
        coupon_code = request.POST.get('coupon_code')
        if Coupone.objects.filter(code=coupon_code).exists():
            coupon = Coupone.objects.filter(code=coupon_code).first()
            business = coupon.business
            staff = Staff.objects.filter(business=business, user=request.user).first()
            if staff is None:
                if coupon.customer:
                    messages.success(request, 'Sorry!!! Coupon Already Taken')
                    customer = Customer.objects.filter(user=request.user).first() 
                    if customer not in business.customers.all():
                        business.customers.add(customer)
                else:
                    customer = Customer.objects.filter(user=request.user).first()
                    if customer is None:
                        customer = Customer.objects.create(user=request.user) 
                    coupon.customer =  customer
                    coupon.save()

                    if customer not in business.customers.all():
                        business.customers.add(customer)
                    messages.success(request, 'Coupon Added!!!')
                    return redirect('profile')
            else:
                messages.success(request, 'Staff not allowed!')
                return redirect('profile')
        else:
            messages.success(request, 'Coupon Does Not Exists') 
            return redirect('profile') 
        return redirect('profile')
    else:
        return render(request, 'business/add-coupon.html')


@login_required(login_url="/login-user/")
def business(request):
    businesses = Business.objects.filter(owner=request.user)
    if not businesses:
        messages.success("You haven't created any business account. create one !!! by clicking create new business")
        return redirect('profile')
    businesses_count = businesses.count()
    business = businesses.first()
    if businesses_count == 1:
        return redirect('dashboard', business.slug)
    
    staff = Staff.objects.filter(user=request.user, business=business).first()

    
    context = {
        'businesses': businesses,
        'business': business,
        'staff': staff,
    }
    return render(request, 'business/business.html', context)

@login_required(login_url="/login-user/")
@team_member_required
def dashboard(request, slug):
    today = date.today()
    businesses = Business.objects.filter(owner=request.user)
    business = Business.objects.filter(slug=slug).first()
    staff = Staff.objects.filter(business=business, user=request.user)
    coupones = Coupone.objects.filter(business=business)
    total_coupone = coupones.count()
    total_expired_coupones = coupones.filter(date_created__lt = today -timedelta(days=Coupone.expiry_in.field.default)).count()
    total_challenges = StoreChallenge.objects.filter(business=business).count()
    total_customers = Customer.objects.filter(business=business).count()
    context={
        'businesses': businesses,
        'business': business,
        'staff': staff,
        'total_coupone': total_coupone,
        'total_expired_coupones' : total_expired_coupones,
        'total_challenges' :  total_challenges,
        'total_customers' : total_customers
    }
    return render(request, 'business/dashboard.html', context)

@login_required(login_url="/login-user/")
@team_member_required
def add_staff(request, slug):
    url=f'/register-user/?add_staff_to={slug}'
    return redirect(url)

def add_customer(request, slug):
    business = Business.objects.filter(slug=slug).first()
    context = {
        'slug': slug,
        'business': business,
    }
    return render(request, 'business/add-customer.html', context)

@login_required(login_url="/login-user/")
@team_member_required
def customers(request, slug):
    businesses = Business.objects.filter(owner=request.user)
    business = Business.objects.filter(slug=slug).first()
    customers = business.customers.all()
    staff = Staff.objects.filter(business=business, user=request.user)
    context={
        'businesses': businesses,
        'business': business,
        'customers':customers, 
        'staff' : staff
    }
    return render(request, 'business/customers.html', context)

def generate_unique_code():
    while True:
        code = uuid.uuid4().hex[:8]
        if not Coupone.objects.filter(code=code).exists():
            return code
        

@login_required(login_url="/login-user/")
@team_member_required
def create_coupones(request, slug):
    business = Business.objects.filter(slug=slug).first()
    staff = Staff.objects.filter(user=request.user, business=business).first()
    if staff is None:
        messages.success(request, 'have No permission to create coupones ')
        return redirect('profile')
    if request.method == "POST":
        coupone_type = request.POST.get('coupone_type')
        discount = request.POST.get('discount')
        expiry_in = request.POST.get('expiry_in')
        total_coupones = request.POST.get('total_coupones')
        coupones_total = int(total_coupones)
        if not total_coupones:
            coupones_total = 1 
        if coupones_total > 1:
            for i in range(coupones_total):
                Coupone.objects.create(
                business = business,
                coupone_type = coupone_type,
                code = generate_unique_code(),
                discount=discount,
                expiry_in= expiry_in,
                created_by=staff
            )

        else:
            messages.success(request, 'coupone created successfuly') 
            Coupone.objects.create(
                business = business,
                coupone_type = coupone_type,
                discount=discount,
                code = generate_unique_code(),
                expiry_in= expiry_in,
                created_by=staff
            )
        messages.success(request, 'coupones created successfuly')  
        return redirect('coupones', slug)
    context = {
        'business': business,
        'staff': staff
    }
    return render(request, 'business/create_coupones.html', context)

@login_required(login_url="/login-user/")
@team_member_required
def coupones(request, slug):
    update = request.GET.get('update') or ''
    businesses = Business.objects.filter(owner=request.user)
    business = Business.objects.filter(slug=slug).first()
    coupones = Coupone.objects.filter(business=business).order_by('-id')
    staff = Staff.objects.filter(business=business, user=request.user)

    if update != '':
        coupon = Coupone.objects.filter(id=update).first()
        if coupon.used == False:
            coupon.used = True
            coupon.save()
        else:
            coupon.used = False
            coupon.save()
        return redirect('coupones', slug)
    context={
        'businesses': businesses,
        'business': business,
        'coupones':coupones, 
        'staff': staff
    }
    return render(request, 'business/coupones.html', context)





@login_required(login_url="/login-user/")
@team_member_required
def create_store_challenge(request, slug):
    business = Business.objects.filter(slug=slug).first()
    staff = Staff.objects.filter(user=request.user, business=business).first()
    if staff is None:
        messages.success(request, 'have No permission to create coupones ')
        return redirect('profile')
    if request.method == "POST":
        challenge_type = request.POST.get('challenge_type')
        challenge_name = request.POST.get('challenge_name')
        challenge_reward = request.POST.get('challenge_reward')
        target_winners = request.POST.get('target_winners')
        day_of_the_challenge = request.POST.get('day_of_the_challenge')
            
        StoreChallenge.objects.create(
            business=business,
            challenge_type = challenge_type,
            challenge_name = challenge_name,
            challenge_reward = challenge_reward,
            target_winners = target_winners,
            day_of_the_challenge = day_of_the_challenge,
            created_by=staff
        )
        messages.success(request, 'challenge created successfuly')  
        return redirect('store_challenges', slug)
    context = {
        'business': business,
        'staff': staff
    }
    return render(request, 'business/create-challenge.html', context)

@login_required(login_url="/login-user/")
@team_member_required
def store_challenges(request, slug):
    update = request.GET.get('update') or ''
    businesses = Business.objects.filter(owner=request.user)
    business = Business.objects.filter(slug=slug).first()
    challenges = StoreChallenge.objects.filter(business=business).order_by('-id')
    staff = Staff.objects.filter(business=business, user=request.user)
    if update != '':
        challenge = StoreChallenge.objects.filter(id=update).first()
        if challenge.closed == False:
            challenge.closed = True
            challenge.save()
        else:
            challenge.closed = False
            challenge.save()
        return redirect('store_challenges', slug)
    context={
        'businesses': businesses,
        'business': business,
        'challenges':challenges,
        'staff': staff
    }
    return render(request, 'business/store-challenges.html', context)

@login_required(login_url="/login-user/")
def view_store_challenge(request, slug):
    challenge_id = request.GET.get('challenge_id')
    businesses = Business.objects.filter(owner=request.user)
    business = Business.objects.filter(slug=slug).first()
    challenge = StoreChallenge.objects.filter(id=challenge_id).first()
    staff = Staff.objects.filter(business=business, user=request.user)
    context={
        'businesses': businesses,
        'staff': staff,
        'business': business,
        'challenge':challenge
    }
    return render(request, 'business/view-store-challenges.html', context)