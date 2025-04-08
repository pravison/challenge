from django.shortcuts import render, redirect
from django.db.models import Sum, Q
import os
from django.conf import settings
from django.http import HttpResponse
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import datetime, date, timedelta
from django.contrib.auth.models import User
import uuid
from django.utils.text import slugify
from .models import Business, Staff, Coupone, Product, ScanCount, StoreChallenge, RefferralCode, LoyaltyPointsCategory, LoyaltyPoint, BusinessCustomer
from customers.models import Customer
from .decorators import team_member_required

import random
from django.http import JsonResponse
from django.core.mail import send_mail

import qrcode
from PIL import Image, ImageDraw, ImageFont


from io import BytesIO
import base64
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

        LoyaltyPointsCategory.objects.create(
            business = business,
            category= 'points on purchases made',
            total_value_for_a_point = 100,
        )
        LoyaltyPointsCategory.objects.create(
            business = business,
            category= 'points on visiting the store',
            total_value_for_a_point = 2,
        )
        LoyaltyPointsCategory.objects.create(
            business = business,
            category= 'points on refferal sales',
            total_value_for_a_point = 200,
        )
        LoyaltyPointsCategory.objects.create(
            business = business,
            category= 'points on bringing friends to the store',
            total_value_for_a_point = 5,
        )
        
        messages.success(request, 'Business Account Created Successfuly')  
        return redirect('dashboard', slug)
    
    return render(request, 'business/add-business.html', context)

# assign coupon to customer
@login_required(login_url="/login-user/")
def add_coupon(request): # assign coupon to customer
    customer_email = request.GET.get('customer_email') or ''
    coupone_code= request.GET.get('coupone_code') or ''
    next_url= request.GET.get('next_url') or ''
    context = {
        'customer_email': customer_email,
        'coupone_code': coupone_code,
        'next_url': next_url
    }

    if request.method == "POST":
        coupon_code = request.POST.get('coupon_code')
        customer_email = request.POST.get('customer_email')
        if Coupone.objects.filter(code=coupon_code).exists():
            coupon = Coupone.objects.filter(code=coupon_code).first()
            business = coupon.business
            
            if coupon.customer:
                    messages.success(request, 'Sorry!!! Coupon Already Taken')
                    customer = Customer.objects.filter(user=request.user).first() 
                    if customer is None:
                        customer = Customer.objects.create(user=user)
                    if customer not in business.customers.all():
                        business.customers.add(customer)
            else:
                # we query user from database
                user=User.objects.filter(email=customer_email).first()
                # if user does not exist we redirect them to register
                if not user:
                    url=f'/business/{business.slug}/add-customer/?coupone_code={coupon.code}'
                    return redirect(url)
                staff = Staff.objects.filter(business=business, user=user).first()
                if staff:
                    messages.success(request, 'Staffs not allowed to participate!')
                    if next_url !='':
                        return redirect(next_url)
                    return redirect('profile')
                customer = Customer.objects.filter(user=user).first()
                if customer is None:
                    customer = Customer.objects.create(user=user) 
                coupon.customer =  customer
                coupon.save()

                if customer not in business.customers.all():
                    business.customers.add(customer)
                messages.success(request, 'Coupon Added!!!')
                if next_url !='':
                    messages.success(request, f'we have assigned coupon to customer {customer} \n Now repeat to update coupone to used!!!')
                    return redirect(next_url)
                return redirect('profile')
        else:
            messages.success(request, 'Coupon Does Not Exists') 
            return redirect('profile') 
        if next_url !='':
            return redirect(next_url)
        return redirect('profile')
    else:
        return render(request, 'business/add-coupon.html', context)


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
    coupone_code= request.GET.get('coupone_code') or ''
    business = Business.objects.filter(slug=slug).first()
    context = {
        'slug': slug,
        'business': business,
        'coupone_code': coupone_code
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
        code = uuid.uuid4().hex[:6]
        if not RefferralCode.objects.filter(code=code).exists():
            return code
        
# create new coupon 
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
        coupone_apply_to = request.POST.get('coupone_apply_to')
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
                coupone_apply_to=coupone_apply_to,
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
    next_url = request.GET.get('next_url') or ''
    businesses = Business.objects.filter(owner=request.user)
    business = Business.objects.filter(slug=slug).first()
    coupones = Coupone.objects.filter(business=business).order_by('-id')
    staff = Staff.objects.filter(business=business, user=request.user)

    if update != '':
        # we are working o assumption that business has only one active challenge running 
        # this assumption will be update to query specific challenge if business has many 
        challenge = StoreChallenge.objects.filter(
                        business=business,
                        closed=False
                    ).last()
        # coupon = Coupone.objects.filter(id=update).first()
        coupon_id = update
        try:
            # Fetch the current coupon being used
            coupon = Coupone.objects.get(id=coupon_id, business=business)
            if coupon.used == False:
                if not coupon.customer:
                    messages.success(request, f"Coupone not assigned to any customer!!!")
                    messages.success(request, f"fill above form to assign !!!")
                    url = f'/business/add-coupon/?coupone_code={coupon.code}&next_url={next_url}'
                    return redirect(url)
                coupon.used = True
                coupon.save()  # Mark this coupon as used

                # Check if the updated coupon is a direct ticket to a challenge
                if coupon.coupone_type == 'direct ticket to a challenge':
                    if challenge:
                        challenge.participants.add(coupon)
                        challenge.save()
                        
                        # Notify customer
                        # if coupon.customer.email:
                        #     send_mail(
                        #         'You Have a Direct Ticket to the Challenge!',
                        #         f'Congratulations! Your coupon code {coupon.code} is a direct ticket to participate in the challenge: {challenge.challenge_name}.',
                        #         'noreply@yourbusiness.com',
                        #         [coupon.customer.email],
                        #         fail_silently=True,
                        #     )
                        messages.success(request, f"Congradulations Your Coupon {coupon.code} has landed you a direct ticket to a challenge to win {challenge.challenge_reward}")
                    else:
                        messages.success(request, f" Business has no active challenge!!!")
                    return redirect('coupones', slug)

                # Find all 'used' coupons for the same business that have not expired
                valid_coupons = Coupone.objects.filter(
                    business=coupon.business,
                    used=True,
                )

                # Filter out expired coupons
                valid_coupons = [c for c in valid_coupons if c.expiry_date >= datetime.now().date()]

                if not valid_coupons:
                    messages.success(request, f" No valid coupons available!!!")
                    return redirect('coupones', slug)

                # Randomly select a coupon
                selected_coupon = random.choice(valid_coupons)

                # Check if the selected coupon belongs to the same customer
                if selected_coupon.customer == coupon.customer:
                    # Fetch the active challenge for the business
                    
                    if not challenge:
                        messages.success(request, f" Business has no active challenge!!!")
                        return redirect('coupones', slug)

                    # Add the selected coupon to the challenge participants
                    challenge.participants.add(selected_coupon)
                    challenge.save()
                    messages.success(request, f"Congradulations your Coupon {selected_coupon.code} has landed you a spot to a challenge to win {challenge.challenge_reward}.")
                    
                else:
                    messages.success(request, f"Your coupon did not win this time. Keep trying with more coupons!")


                # Notify customer
                
                if selected_coupon == coupon:
                    # Case 1: Selected coupon is the same as the updated one
                    messages.success(request, 'Your Coupon Code Earned You a Challenge Spot!')
                    messages.success(request, f"""Congratulations! Your coupon code {coupon.code} has landed you a chance to participate \n
                               in the challenge: {challenge.challenge_name}.\n
                               Keep collecting coupons to increase your chances of winning!""")            
                elif selected_coupon.customer == coupon.customer:
                    # Case 2: Selected coupon is different from the updated one
                    messages.success(request, 'You Got Selected for a Challenge!')
                    messages.success(request, f"""Congratulations! Although your coupon {coupon.code}, didnt got selceted its your other coupone \n
                               {selected_coupon.code} that landed you a spot in the challenge to win : {challenge.challenge_reward}.\n
                                   "Keep acquiring coupons because you never know which one will help you win the offer!""") 

            else:
                messages.success(request, 'you need permision to change the update to not used')
            return redirect('coupones', slug)

        except Coupone.DoesNotExist:
            messages.success(request, 'Your Coupon Code does not exists!')
            return redirect('coupones', slug)
    context={
        'businesses': businesses,
        'business': business,
        'coupones':coupones, 
        'staff': staff
    }
    return render(request, 'business/coupones.html', context)

@login_required(login_url="/login-user/")
def view_coupon(request, slug):
    coupon_id = request.GET.get('coupon_id')
    businesses = Business.objects.filter(owner=request.user)
    business = Business.objects.filter(slug=slug).first()
    coupon = Coupone.objects.filter(id=coupon_id).first()
    staff = Staff.objects.filter(business=business, user=request.user)
    today = date.today()

    # we are quering the latest featured challenge
     # will work on it later 
    challenge = StoreChallenge.objects.filter(
                    business=business,

                    closed=False
                ).last()

    qr_url = f"{request.scheme}://{request.get_host()}/business/add-coupon/?coupone_code={coupon.code}"  # URL to lock the code

    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=2.5, border=1)
    qr.add_data(qr_url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')

    # Save QR code to memory
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    qr_code_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
    buffer.close()

    context = {
        # 'company_name': company_name,
        # 'coupon_code': coupon_code,
        # 'coupon_image_name': f"coupons/{coupon_image_name}",
        'qr_code_image': qr_code_image,
        'businesses': businesses,
        'staff': staff,
        'business': business,
        'coupon':coupon,
        'today':today,
        'challenge': challenge
    }
    return render(request, 'business/view_coupon.html', context)


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
            messages.success(request, "NOT allowed to update challenge status")
            # challenge.closed = True
            # challenge.save()
        else:
            messages.success(request, "NOT allowed to update challenge status")
            # challenge.closed = False
            # challenge.save()
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
    select_winners = request.GET.get('select_winners') or ''
    next_url = request.GET.get('next_url') or ''
    businesses = Business.objects.filter(owner=request.user)
    business = Business.objects.filter(slug=slug).first()
    challenge = StoreChallenge.objects.filter(id=challenge_id).first()
    staff = Staff.objects.filter(business=business, user=request.user)

    qr_url = f"{request.scheme}://{request.get_host()}/business/{slug}/stand-a-chance-to-win/?challenge_id={challenge_id}"  # URL to lock the code

    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=5, border=2)
    qr.add_data(qr_url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')

    # Save QR code to memory
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    qr_code_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
    buffer.close()

    if select_winners !='':
        #check if winners already selceted 
        # check if today is greator than challenge date 
        #  randomly select winners from participants
        try:
            # Fetch the challenge
            challenge = StoreChallenge.objects.get(id=challenge_id)
            
            if challenge.closed:
                messages.success(request, "Challenge already closed !!!")
                if next_url !='':
                    return redirect(next_url)
                else:
                    return redirect('store_challenges', slug)

            # Get all participants related to this challenge
            participants = list(challenge.participants.all())
            
            if not participants:
                messages.success(request, "No participants found for this challenge!!!")
                if next_url !='':
                    return redirect(next_url)
                else:
                    return redirect('store_challenges', slug)
            # check if number of participants is less than target winners and return telling owner to add more participants
            if challenge.target_winners > len(participants):
                messages.success(request, "participants are less than target winners !!!")
                messages.success(request, "Add more participants !!!")
                if next_url !='':
                    return redirect(next_url)
                else:
                    return redirect('store_challenges', slug)
            # Determine the number of winners to select
            num_winners = min(challenge.target_winners, len(participants))
            # later on i will come to prevent selecting winners if participants are less than target winners
            # Randomly select winners
            selected_winners = random.sample(participants, num_winners)

            # Add winners to the winners field
            challenge.winners.set(selected_winners)

            # Return the winners' IDs or any other relevant info
            messages.success(request, "Winners Have been Succefully selected !!!")
            # Mark challenge as closed
            challenge.closed = True
            challenge.save()

        except StoreChallenge.DoesNotExist:
            messages.success(request, "Challenge Does not Exists !!!")
        if next_url !='':
            return redirect(next_url)
        else:
            return redirect('store_challenges', slug)

    context={
        'qr_code_image': qr_code_image,
        'businesses': businesses,
        'staff': staff,
        'business': business,
        'challenge':challenge
    }
    return render(request, 'business/view-store-challenges.html', context)

def add_challenge_participant(request, slug):
    challenge_id = request.GET.get('challenge_id')
    # businesses = Business.objects.filter(owner=request.user) or None
    business = Business.objects.filter(slug=slug).first()
    challenge = StoreChallenge.objects.filter(id=challenge_id).first()
    # staff = Staff.objects.filter(business=business, user=request.user) or None
    today = date.today()
    coupon = ''

    if challenge.closed:
        messages.success(request, f"visit {business.business_name} @ {business.address} for More Information!!!")
    else:
        coupones = Coupone.objects.filter(business=business, used=False).order_by('-id')
        valid_coupons = [c for c in coupones if c.expiry_date >= datetime.now().date()]

        existing_participants = set(challenge.participants.all())  # Convert to set for fast lookup
        available_coupons = [c for c in valid_coupons if c not in existing_participants]

        if not available_coupons:
            messages.success(request, f"Visit {business.business_name} @ {business.address} for more information!")
        else:
            # Randomly select a coupon that is not already a participant
            coupon = random.choice(available_coupons)
            challenge.participants.add(coupon)  # Add the selected coupon to participants

    context={
        # 'businesses': businesses,
        # 'staff': staff,
        'today': today,
        'business': business,
        'challenge':challenge,
        'coupon': coupon
    }
    return render(request, 'business/add-challenge-participant.html', context)

def generate_unique_refferal_code():
    while True:
        code = uuid.uuid4().hex[:4]
        if not RefferralCode.objects.filter(code=code).exists():
            return code
        

@login_required(login_url="/login-user/")
def create_refferal_code(request, slug):
    business = Business.objects.filter(slug=slug).first()
    customer = Customer.objects.filter(user=request.user).first()
    next_url = request.GET.get('next_url') or ''
    if business is None:
        messages.success(request, 'There was an error generating your refferal please try again!!! ')
        if next_url !='':
            return redirect(next_url)
        return redirect('profile')

    if customer is None:
        customer = Customer.objects.create(user=request.user)
        if customer not in business.customers.all():
            business.customers.add(customer)
        refferal_code = RefferralCode.objects.create(
            customer=customer,
            business = business,
            code = generate_unique_refferal_code()
        )
        messages.success(request, 'Refferal Code Generated Succesfully!!! ')
        messages.success(request, f'your refferal code is {refferal_code.code}!!! ') 
    else:
        if customer not in business.customers.all():
            business.customers.add(customer)
        if not RefferralCode.objects.filter(customer=customer, business=business).exists():
            refferal_code = RefferralCode.objects.create(
            customer=customer,
            business = business,
            code = generate_unique_refferal_code()
            )
            messages.success(request, 'Refferal Code Generated Succesfully!!! ')
            messages.success(request, f'your refferal code is {refferal_code.code}!!! ') 
        else:
            messages.success(request, 'already have a refferal code!!! ')
    if next_url !='':
        return redirect(next_url)
    return redirect('profile')

@login_required(login_url="/login-user/")
@team_member_required
def loyalty_points_category(request, slug):
    businesses = Business.objects.filter(owner=request.user)
    business = Business.objects.filter(slug=slug).first()
    staff = Staff.objects.filter(business=business, user=request.user)
    loyalty_categories = LoyaltyPointsCategory.objects.filter(business=business)
    context={
        'businesses': businesses,
        'business': business,
        'staff': staff,
        'loyalty_categories': loyalty_categories
    }
    return render(request, 'business/loyalty-points-category.html', context)

from . forms import EditLoyaltyPointsCategoryForm

@login_required(login_url="/login-user/")
@team_member_required
def edit_loyalty_category(request, slug):
    id = request.GET.get('id') or ''
    if id == '':
        messages.success(request, "There was error editing loyalty category please reselect and try again")
        return ('loyalty_points_category', business.slug)
    businesses = Business.objects.filter(owner=request.user)
    business = Business.objects.filter(slug=slug).first()
    staff = Staff.objects.filter(business=business, user=request.user).first()
    loyalty_category = LoyaltyPointsCategory.objects.filter(id=id).first()
    if request.method == 'POST':
        form = EditLoyaltyPointsCategoryForm(request.POST, instance=loyalty_category)
        if form.is_valid():
            instance=form.save(commit=False)
            instance.edited_by= staff
            instance.save()
            messages.success(request, "Editted succesfully")
            return redirect('loyalty_points_category', slug)
            
    else:
        form = EditLoyaltyPointsCategoryForm(instance=loyalty_category)
        context = {
            'businesses': businesses,
            'business': business,
            'staff': staff,
            'form': form,
            'loyalty_category':loyalty_category
        }
        return render(request, 'business/edit-loyalty-category.html', context)
    
@login_required(login_url="/login-user/")
@team_member_required
def add_loyalty_points_to_customer(request, slug):
    businesses = Business.objects.filter(owner=request.user)
    business = Business.objects.filter(slug=slug).first()
    staff = Staff.objects.filter(business=business, user=request.user).first()
    loyalty_categories = LoyaltyPointsCategory.objects.filter(business=business)
    if request.method == 'POST':
        category_name = request.POST.get('category')
        purchase_value = request.POST.get('purchase_value')
        customer_email = request.POST.get('customer_email')

        loyalty_category = LoyaltyPointsCategory.objects.filter(business=business, category=category_name).first()
        earned_points = int(int(purchase_value)/int(loyalty_category.total_value_for_a_point))

        user = User.objects.filter(email=customer_email).first()
        if user :
            customer = Customer.objects.filter(user=user).first()
            if customer:
                business_customer = BusinessCustomer.objects.filter(business=business, customer=customer).first()
                if business_customer is None:
                    business_customer = BusinessCustomer.objects.create(business=business, customer = customer)
                
                if customer not in business.customers.all():
                    business.customers.add(customer)
                business.customers.add(customer)
                LoyaltyPoint.objects.create(
                    business=business,
                    customer = customer,
                    category=loyalty_category,
                    purchase_value=purchase_value,
                    points_earned=earned_points,
                    added_by = f'{request.user.first_name} {request.user.last_name}' 
                )

                if business_customer.reffered_by is not None:
                    customer_reffery = Customer.objects.filter(user=business_customer.reffered_by).first()
                    if customer_reffery:
                        points_category = LoyaltyPointsCategory.objects.filter(business=business, category='points from refferal sales').first()
                        if not points_category:
                            points_category = LoyaltyPointsCategory.objects.create(
                                business = business,
                                category = 'points from refferal sales',
                                total_value_for_a_point = int(1),
                                )
                        LoyaltyPoint.objects.create(
                            business=business,
                            customer = customer_reffery,
                            category=points_category,
                            purchase_value=int(0),
                            points_earned=int(50), # will rewrite the code to make these part dynamic
                            added_by = f'{customer.user.first_name} {customer.user.last_name}' 
                        )
                messages.success(request, "points added succesfully")
            else:
                customer = Customer.objects.create(user=user)
                business.customers.add(customer)
                business_customer = BusinessCustomer.objects.create(business=business, customer=customer)

                LoyaltyPoint.objects.create(
                    business=business,
                    customer = customer,
                    category=loyalty_category,
                    purchase_value=purchase_value,
                    points_earned=earned_points,
                    added_by = f'{request.user.first_name} {request.user.last_name}' 
                )

                if business_customer.reffered_by is not None:
                    customer_reffery = Customer.objects.filter(user=business_customer.reffered_by).first()
                    if customer_reffery:
                        points_category = LoyaltyPointsCategory.objects.filter(business=business, category='points from refferal sales').first()
                        if not points_category:
                            points_category = LoyaltyPointsCategory.objects.create(
                                business = business,
                                category = 'points from refferal sales',
                                total_value_for_a_point = int(1),
                                )
                        LoyaltyPoint.objects.create(
                            business=business,
                            customer = customer_reffery,
                            category=points_category,
                            purchase_value=int(0),
                            points_earned=int(50), # will rewrite the code to make these part dynamic
                            added_by = f'automatically added' 
                        )
                        
                
                messages.success(request, "points added succesfully")
        else:
            messages.success(request, "Customer does not exist send them a link to register first")
        
        return redirect('loyalty_points', slug)

    context = {
        'businesses': businesses,
        'business': business,
        'staff': staff,
        'loyalty_categories':loyalty_categories
    }
    return render(request, 'business/add-loyalty-points.html', context)

@login_required(login_url="/login-user/")
def customer_adding_loyalty_points(request, slug):
    businesses = Business.objects.filter(owner=request.user)
    business = Business.objects.filter(slug=slug).first()
    staff = Staff.objects.filter(business=business, user=request.user).first()
    loyalty_categories = LoyaltyPointsCategory.objects.filter(business=business)
    if request.method == 'POST':
        category_name = request.POST.get('category')
        purchase_value = request.POST.get('purchase_value')
        customer_email = request.POST.get('customer_email')

        loyalty_category = LoyaltyPointsCategory.objects.filter(business=business, category=category_name).first()
        earned_points = int(int(purchase_value)/int(loyalty_category.total_value_for_a_point))

        user = User.objects.filter(email=customer_email).first()
        if user :
            customer = Customer.objects.filter(user=user).first()
            if customer is not None:
                business_customer = BusinessCustomer.objects.filter(business=business, customer=customer).first()
                if business_customer is None:
                    business_customer = BusinessCustomer.objects.create(business=business, customer = customer)
                if business.customers.filter(user=user).exists():
                    LoyaltyPoint.objects.create(
                        business=business,
                        customer = customer,
                        category=loyalty_category,
                        purchase_value=purchase_value,
                        points_earned=earned_points,
                        added_by = f'{request.user.first_name} {request.user.last_name}' 
                    )
                    business_customer.total_loyal_points += earned_points
                    business_customer.save()
                    messages.success(request, "points added succesfully")
                else:
                    business.customers.add(customer)
                    LoyaltyPoint.objects.create(
                        business=business,
                        customer = customer,
                        category=loyalty_category,
                        purchase_value=purchase_value,
                        points_earned=earned_points,
                        added_by = f'{request.user.first_name} {request.user.last_name}' 
                    )
                    business_customer.total_loyal_points += earned_points
                    business_customer.save()
                    messages.success(request, "points added succesfully")
            else:
                customer = Customer.objects.create(user=user)
                business.customers.add(customer)
                business_customer = BusinessCustomer.objects.create(business=business, customer=customer)
                LoyaltyPoint.objects.create(
                    business=business,
                    customer = customer,
                    category=loyalty_category,
                    purchase_value=purchase_value,
                    points_earned=earned_points,
                    added_by = f'automatically added' 
                )
                business_customer.total_loyal_points += earned_points
                business_customer.save()
                messages.success(request, "points added succesfully")
        else:
            messages.success(request, "Customer does not exist send them a link to register first")
        
        return redirect('loyalty_points', slug)

    context = {
        'businesses': businesses,
        'business': business,
        'staff': staff,
        'loyalty_categories':loyalty_categories
    }
    return render(request, 'business/customer-adding-loyalty-points.html', context)

@login_required(login_url="/login-user/")
@team_member_required
def loyalty_points(request, slug):
    approve_point_id = request.GET.get('approve_point_id') or ''
    businesses = Business.objects.filter(owner=request.user)
    business = Business.objects.filter(slug=slug).first()


    # a quering the first product
    # will update code to query products dynamically
    products = Product.objects.filter(business=business).first()
    staff = Staff.objects.filter(business=business, user=request.user)
    loyalty_points = LoyaltyPoint.objects.filter(business=business)

    if approve_point_id !='':
        loyalty_point = loyalty_points.filter(id=approve_point_id).first()
        loyalty_point.status = 'approved'
        loyalty_point.save()
    

    qr_url = f"{request.scheme}://{request.get_host()}/business/{slug}/loyalty-membership/"  # URL to lock the code

    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=5, border=2)
    qr.add_data(qr_url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')

    # Save QR code to memory
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    qr_code_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
    buffer.close()
    context={
        'businesses': businesses,
        'business': business,
        'staff': staff,
        'loyalty_points': loyalty_points,
        'qr_code_image': qr_code_image,
        'products': products
    }
    return render(request, 'business/loyalty-points.html', context)

def loyalty_qr_code(request, slug):
    code_reffered = request.GET.get('referral_code') or '' #code that reffered request.user
  
    if code_reffered !='':
        request.session['stored_refferal_code'] = {
            'slug': slug,
            'code': code_reffered
            }
    business = Business.objects.filter(slug=slug).first()
    if not business:
        messages.success(request, "Bussiness doesnt exists!!!")
        return redirect('profile')
    # a quering the first product
    # will update code to query products dynamically
    products = Product.objects.filter(business=business).first()
    qr_url = f"{request.scheme}://{request.get_host()}/business/{slug}/loyalty-membership/"  # URL to lock the code

    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=5, border=2)
    qr.add_data(qr_url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')

    # Save QR code to memory
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    qr_code_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
    buffer.close()
    context={
        'business': business,
        'qr_code_image': qr_code_image,
        'products': products
    }
    return render(request, 'business/loyalty-qr-code.html', context)


def get_next_number(slug):
    business = Business.objects.filter(slug=slug).first()
    if not business:
        return redirect('profile')
    """
    atomically generate next number in sequence, skipping multiples of 20 """
    with transaction.atomic():
        # business = Business.objects.filter(id=id).first()
        sequence = ScanCount.objects.filter(business=business).last()
        if sequence is None:
            sequence= ScanCount.objects.create(
            business=business,
            number=14
            )
        next_number=sequence.number +1 
        if next_number % 20 == 0:
            next_number += 1
        return next_number
    
def loyalty_membership(request, slug): 
    
    business = Business.objects.filter(slug=slug).first()
    if not business:
        messages.success(request, "Bussiness doesnt exists!!!")
        return redirect('profile')

    customer_scan_count= request.session.get('customer_scan_count')
    
    # a quering the first product
    # will update code to query products dynamically
    products = Product.objects.filter(business=business).first()

    total_points = 0,
    remaining_points = 0,
    percentage_points = 0,
    refferal_code = ''#request.user refferal code
    customer = None
    if request.user.is_authenticated:
        customer = Customer.objects.filter(user=request.user).first()
    if customer:
        refferal_code = RefferralCode.objects.filter(business=business, customer=customer).first()
        points= LoyaltyPoint.objects.filter(business=business, customer=customer)
        total_points = points.filter(status='approved').aggregate(Sum('points_earned'))['points_earned__sum'] or 0
        remaining_points = 1000 - total_points
        percentage_points = (total_points/1000)*100
        if total_points > 1000:
            remaining_points = total_points - 1000
    
    
    if not customer_scan_count:
        scan_count = ScanCount.objects.create(
            business = business,
            customer = customer or None,
            number = get_next_number(slug)
        )
        request.session['customer_scan_count'] = {
            'slug': slug,
            'number': scan_count.number
            }
        customer_scan_count = scan_count.number
    else:
        store_slug = customer_scan_count.get('slug')
        if store_slug == slug:
            customer_scan_count = customer_scan_count.get('number')
        else:
            scan_count = ScanCount.objects.create(
                business = business,
                customer = customer or None,
                number = get_next_number(slug)
            )
            customer_scan_count['slug']= slug
            request.session['customer_scan_count'] = {
                'slug': slug,
                'number': scan_count.number
                }
            customer_scan_count = scan_count.number

    
    context={
        'business': business,
        'products': products,
        'customer': customer,
        'customer_scan_count': customer_scan_count,
        'total_points': total_points,
        'remaining_points': remaining_points,
        'percentage_points': percentage_points,
        'refferal_code': refferal_code,
        # 'code_reffered': code_reffered
    }
    return render(request, 'business/loyalty-membership.html', context)


@login_required(login_url="/login-user/")
@team_member_required
def redeemed_loyalty_points(request, slug):
    businesses = Business.objects.filter(owner=request.user)
    business = Business.objects.filter(slug=slug).first()
    staff = Staff.objects.filter(business=business, user=request.user)
    business_customer = None
    customer_email = request.GET.get('customer_email') or ''

    if customer_email != '':
        user = User.objects.filter(email=customer_email).first()
        if user is None:
            messages.success(request, "user with that email does not exists")
        else:
            customer = Customer.objects.filter(user=user).first()
            if customer is None:
                messages.success(request, "customer does not exists")
                customer = None
            else:
                business_customer = BusinessCustomer.objects.filter(customer=customer, business=business).first()
                if business_customer is None:
                    messages.success(request, "customer has not yet registered for loyalty points")
                    customer = None

    context={
        'businesses': businesses,
        'business': business,
        'staff': staff,
        'business_customer': business_customer,
    }
    return render(request, 'business/redeeme-points.html', context)