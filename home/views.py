from django.shortcuts import render, redirect
from django.db.models import Sum, Q, Prefetch

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import date, timedelta
from django.utils.text import slugify
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from datetime import date
from businesses.models import Business, Staff, Coupone, StoreChallenge, RefferralCode, BusinessCustomer, LoyaltyPointsCategory, LoyaltyPoint
from customers.models import Customer
# Create your views here.
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from .models import PasswordResetCode
from .forms import RequestResetCodeForm, PasswordResetCodeForm
import uuid

# Create your views here.
def index(request):
    return render(request, 'home/index.html')

def pricing(request):
    return render(request, 'home/pricing.html')


from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import SetPasswordForm

def request_reset_code(request):
    if request.method == 'POST':
        email = request.POST['email']
        try:
            user = User.objects.get(email=email)      
            # Generate or update the reset code
            reset_code, created = PasswordResetCode.objects.get_or_create(user=user)
            reset_code.code = str(uuid.uuid4().hex[:6])
            reset_code.is_valid = True
            reset_code.save()
            
            # Send email
            send_mail(
                'Your Password Reset Code',
                f'Your reset code is: {reset_code.code}',
                'noreply@example.com',
                [email],
            )
            messages.success(request, 'A reset code has been sent to your email and expires in ten minutes.')
            return redirect('verify_reset_code')
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email.')
    else:
        form = RequestResetCodeForm()
    return render(request, 'home/request_reset_code.html')


# def verify_reset_code(request):
#     if request.method == 'POST':
#         form = PasswordResetCodeForm(request.POST)
#         if form.is_valid():
#             code = form.cleaned_data['code']
#         try:
#             reset_code = PasswordResetCode.objects.filter(code=code, is_valid=True).order_by('-created_at').first()
#             if reset_code.is_expired():
#                 reset_code.is_valid = False
#                 reset_code.save()
#                 messages.error(request, 'This code has expired.')
#                 return redirect('request_reset_code')
#             else:
#                 # Invalidate the code
#                 reset_code.is_valid = False
#                 reset_code.save()
#                 # Redirect to password reset form
#                 request.session['password_reset_user_id'] = reset_code.user.id
#                 return redirect('reset_password')
#                 return redirect('request_reset_code')
#         except PasswordResetCode.DoesNotExist:
#             messages.error(request, 'Invalid or expired code.')
#     form = PasswordResetCodeForm()
#     return render(request, 'home/verify_reset_code.html', {'form': form} )

# def reset_password(request):
#     user_id = request.session.get('password_reset_user_id')
#     if not user_id:
#         return redirect('request_reset_code')
    
#     user = User.objects.get(id=user_id)
#     try:
#         reset_code = PasswordResetCode.objects.filter(user=user).order_by('-created_at').first()
#         if reset_code.is_expired():
#             # If the code is expired or invalid, redirect to request a new one
#             reset_code.is_valid = False
#             reset_code.save()
#             messages.error(request, 'Your reset code has expired. Please request a new code.')
#             return redirect('request_reset_code')
#     except (User.DoesNotExist, PasswordResetCode.DoesNotExist):
#         # If the user or reset code is not found, redirect to the request page
#         messages.error(request, 'Invalid reset request. Please try again.')
#         return redirect('request_reset_code')
#     if request.method == 'POST':
#         form = SetPasswordForm(user, request.POST)
#         if form.is_valid():
#             form.save()
#             # Keep the user logged in after password change
#             update_session_auth_hash(request, user)
#             messages.success(request, 'Your password has been successfully reset.')
#             return redirect('login_user')
#     else:
#         form = SetPasswordForm(user)
#     return render(request, 'home/reset_password.html', {'form': form})

def verify_reset_code(request):
    if request.method == 'POST':
        form = PasswordResetCodeForm(request.POST)
        if not form.is_valid():
            messages.error(request, 'Error assessing your data counter check and try again')
            return redirect('verify_reset_code')
        code = form.cleaned_data['code']
        try:
            reset_code = PasswordResetCode.objects.filter(code=code, is_valid=True).order_by('created_at').last()
            if reset_code is None:
                messages.error(request, 'Counter check your code seems its incorrect')
                return redirect('verify_reset_code')
            if reset_code.is_expired():
                reset_code.is_valid = False
                reset_code.save()
                messages.error(request, 'This code has expired.')
                return redirect('request_reset_code')
            else:
                # Invalidate the code
                reset_code.is_valid = False
                reset_code.save()
                # Redirect to password reset form
                request.session['password_reset_user_id'] = reset_code.user.id
                return redirect('reset_password')
        except PasswordResetCode.DoesNotExist:
            messages.error(request, 'Counter check your code seems its incorrect')
            return redirect('verify_reset_code')
    form = PasswordResetCodeForm()
    return render(request, 'home/verify_reset_code.html', {'form': form} )

def reset_password(request):
    user_id = request.session.get('password_reset_user_id')
    if not user_id:
        messages.error(request, 'There was an error proccessing your application, try again')
        return redirect('request_reset_code')
    
    user = User.objects.get(id=user_id)
    try:
        reset_code = PasswordResetCode.objects.filter(user=user).order_by('-created_at').first()
        if reset_code is None:
            messages.error(request, 'There was an error proccessing your application, try again')
            return redirect('request_reset_code')
        if reset_code.is_expired():
            # If the code is expired or invalid, redirect to request a new one
            reset_code.is_valid = False
            reset_code.save()
            messages.error(request, 'Your reset code has expired. Please request a new code.')
            return redirect('request_reset_code')
    except (User.DoesNotExist, PasswordResetCode.DoesNotExist):
        # If the user or reset code is not found, redirect to the request page
        messages.error(request, 'Invalid reset request. Please try again.')
        return redirect('request_reset_code')
    if request.method == 'POST':
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            # Keep the user logged in after password change
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been successfully reset.')
            return redirect('login_user')
    else:
        form = SetPasswordForm(user)
    return render(request, 'home/reset_password.html', {'form': form})



@login_required(login_url="/login-user/")
def profile(request):
    customer = Customer.objects.filter(user=request.user).first()
    if not Customer.objects.filter(user=request.user).exists():
        customer = Customer.objects.create(user=request.user)
        #customer is addeded to business model as many to many relationship and also added to businessCustomer model
    # business_customer = BusinessCustomer.objects.filter(customer=customer) or [] 
    customer_businesses = Business.objects.filter(customers=customer).prefetch_related("challenges") #business user has participated in their challange

    today = date.today()
    #checking if request.user is a staff in any business account
    staff_businesses = Staff.objects.filter(user=request.user)
    #checking if request.user has business account and quering tem
    businesses = Business.objects.filter(owner=request.user)

    # getting coupones customer has
    coupones = list(Coupone.objects.filter(customer=customer).order_by('-id'))
    # getting all cahllenges customer paarticipated in 
    challenges = StoreChallenge.objects.filter(participants__customer=customer).order_by('-id')
    # getting active challenges customer is participating in
    active_challenges = challenges.filter(closed=False)
    challenges_count = active_challenges.count()

    active_coupones_count = sum(
        1 for c in coupones if not c.used and c.date_created > today - timedelta(days=Coupone._meta.get_field('expiry_in').default)
    )
    # business_points= business_points = Business.objects.filter(
    #     customers=customer
    # ).annotate(
    #     total_customer_points=Sum(
    #         'points__points_earned', 
    #         filter=Q(points__customer=customer)  # Only include points for this customer
    #     )
    # )
    # Prefetch only the customer's points for each business
    customer_points_prefetch = Prefetch(
        'points',
        queryset=LoyaltyPoint.objects.filter(customer=customer),
        to_attr='customer_points'  # Rename for clarity
    )

    
    # Get businesses associated with the customer
    business_points = Business.objects.filter(
        customers=customer 
    ).annotate(
        total_customer_points=Sum(
            'points__points_earned',
            filter=Q(points__customer=customer) and Q(points__status='approved')
        )
    ).prefetch_related(customer_points_prefetch)

    refferal_codes = RefferralCode.objects.filter(customer=customer)
    points= LoyaltyPoint.objects.filter(customer=customer)
    total_points = points.exclude(status='declined').aggregate(Sum('points_earned'))['points_earned__sum'] or 0
    total_approved_points = points.filter(status='approved').aggregate(Sum('points_earned'))['points_earned__sum'] or 0
    total_points_awaiting_approval = points.filter(status='awaiting approval').aggregate(Sum('points_earned'))['points_earned__sum'] or 0
    
   
    context = {
        'businesses': businesses,
        'coupones': coupones,
        'challenges': challenges,
        'customer': customer,
        'challenges_count': challenges_count,
        'active_coupones_count': active_coupones_count,
        'customer_businesses': customer_businesses,
        'staff_businesses': staff_businesses,
        'refferal_codes' : refferal_codes,
        'points': points,
        'total_points': total_points,
        'total_approved_points': total_approved_points,
        'total_points_awaiting_approval':total_points_awaiting_approval,
        'business_points': business_points,
        # 'business_customer': business_customer
    }
    return render(request, 'home/profile.html', context)

# Create your views here.
def register_user(request):
    next_url = request.GET.get('next', '')
    pricing_plan = request.GET.get('pricing_plan') or ''
    add_staff_to = request.GET.get('add_staff_to') or ''
    add_customer_to = request.GET.get('add_customer_to') or ''  # Corrected this line   
    code = request.session.get('coupon_code') or request.GET.get('code') or ''
    refferal_code = request.GET.get('refferal_code') or ''
    
    stored_refferal_code = request.session.get('stored_refferal_code') or '' #  we get both refferal code plus business slug         
    
    if refferal_code !='' and add_customer_to !='':
        request.session['stored_refferal_code'] = {
            'slug': add_customer_to,
            'code': refferal_code
            }

    if stored_refferal_code !='':
        stored_slug = stored_refferal_code.get('slug')
        if stored_slug == add_customer_to:
            refferal_code = stored_refferal_code.get('code')
            
    

    context = {
        'add_staff_to': add_staff_to,
        'add_customer_to': add_customer_to,
        'pricing_plan': pricing_plan,
        'code': code,
        'next_url': next_url,
    }

    if request.method == "POST":
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            messages.success(request, 'Email already exists.')
            messages.success(request, 'If you have never registered using this email, please reach out to our tech team.')
            return render(request, 'home/register.html', context)
        
        # Create user
        username = str(email)
        user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name, email=email, password=password)
        
        
        if pricing_plan != '':
            user = authenticate(username=username, password=password)
            login(request, user)
            url = f'/business/add-business/?pricing_plan={pricing_plan}'
            return redirect(url)

        # Add staff logic
        if add_staff_to != '':
            business = Business.objects.filter(slug=add_staff_to).first()
            if business:
                if not Staff.objects.filter(user=user, business=business).exists():
                    Staff.objects.create(user=user, business=business)
                    messages.success(request, 'Staff added successfully')
                    messages.success(request, 'Share email and password for them to log in')

                # Add customer if it does not exist
                if Customer.objects.filter(user=user).first() is None:
                    customer = Customer.objects.create(user=user)
                    if customer not in business.customers.all():
                        business.customers.add(customer)
            
            return redirect('dashboard', add_staff_to)
        # print(add_staff_to)

        # Add customer logic
        if add_customer_to != '':
            business = Business.objects.filter(slug=add_customer_to).first()
            if business:
                if Customer.objects.filter(user=user).first() is None:
                    customer = Customer.objects.create(user=user)
                    if customer not in business.customers.all():
                        business.customers.add(customer)
                        points_category = LoyaltyPointsCategory.objects.filter(business=business, category='signup points').first()
                        if not points_category:
                            points_category = LoyaltyPointsCategory.objects.create(
                                business = business,
                                category = 'signup points',
                                total_value_for_a_point = int(1),
                                )

                        LoyaltyPoint.objects.create(
                            business = business,
                            customer = customer,
                            category = points_category or None,
                            purchase_value = int(0),
                            points_earned = int(200),#have assummed every business will give 200 signupp bonus will correct to add what each business want to offer
                            added_by = 'automaticaly during signup',
                            status = 'approved'
                            )
                        messages.success(request, 'Congrats You have Claimed 200 points')


                    # Handle coupon code
                    if code != '':
                        coupon = Coupone.objects.filter(code=code).first()
                        if coupon:
                            if coupon.customer:
                                messages.success(request, 'Sorry! Coupon already taken')
                            else:
                                coupon.customer = customer
                                coupon.save()

                            if customer not in business.customers.all():
                                business.customers.add(customer)
                        else:
                            messages.success(request, 'Coupon does not exist') 

                    if refferal_code != '':
                        code = RefferralCode.objects.filter(business=business, code=refferal_code).first()
                        if code:
                            BusinessCustomer.objects.create(
                                business = business,
                                customer = code.customer,
                                reffered_by = code.customer.user
                                )
            

        # Handle redirect for "next_url" parameter
        if next_url != '':
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect(next_url)

        # Default redirect after registration
        user = authenticate(username=username, password=password)
        login(request, user)
        return redirect('profile')

    return render(request, 'home/register.html', context)

def login_user(request):
    next_url = request.GET.get('next', '')
    coupon_code = request.GET.get('coupone_code', '')

    stored_refferal_code = request.session.get('stored_refferal_code') or '' #  we get both refferal code plus business slug         
    

    if coupon_code:
        request.session['coupon_code'] = coupon_code  # Store actual coupon code

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)

            coupon_code = request.session.get('coupon_code')
            print(f"Coupon Code from session: {coupon_code}")

            if coupon_code:
                coupon = Coupone.objects.filter(code=coupon_code).first()
                print(f"Fetched Coupon: {coupon}")

                if not coupon:  # ✅ Prevent NoneType error
                    messages.error(request, "Invalid or expired coupon code.")
                    return redirect('profile')

                business = coupon.business  # Now it's safe

                if coupon.customer:
                    messages.error(request, "Unfortunately, this coupon is already taken.")
                else:
                    user = request.user
                    staff = Staff.objects.filter(business=business, user=user).first()

                    if staff:
                        messages.error(request, "Staff members are not allowed to participate!")
                        return redirect(next_url or 'profile')

                    customer, created = Customer.objects.get_or_create(user=user)
                    coupon.customer = customer
                    coupon.save()

                    if customer not in business.customers.all():
                        coupon.business.customers.add(customer)


                    messages.success(request, "You have successfully locked the coupon code to yourself!")
                    messages.success(request, "Now you stand a chance to win the offer!")

            if stored_refferal_code !='':
                stored_slug = stored_refferal_code.get('slug')
                business = Business.objects.filter(slug=stored_slug).first()
                if business:
                    customer = Customer.objects.filter(user=user).first()
                    if customer is None:
                        customer = Customer.objects.create(user=user)
                    if customer not in business.customers.all():
                        business.customers.add(customer)
                        
                        points_category = LoyaltyPointsCategory.objects.filter(business=business, category='signup points').first()
                        
                        if points_category is None:
                            points_category = LoyaltyPointsCategory.objects.create(
                                business=business,
                                category='signup points',
                                total_value_for_a_point = int(1)
                                )

                        LoyaltyPoint.objects.create(
                            business = business,
                            customer = customer,
                            category = points_category,
                            purchase_value = int(0),
                            points_earned = int(200),#have assummed every business will give 200 signupp bonus will correct to add what each business want to offer
                            added_by = 'automaticaly during signup',
                            status = 'approved'
                            )
                        messages.success(request, 'Congrats You have Claimed 200 points')

                        refferal_code = stored_refferal_code.get('code') 
                        code = RefferralCode.objects.filter(business=business, code=refferal_code).first()
                        if code:
                            BusinessCustomer.objects.create(
                                business = business,
                                customer = code.customer,
                                reffered_by = code.customer.user
                                )
            messages.success(request, 'Welcome, you have ben logged in!')
            return redirect(next_url or 'profile')
        messages.error(request, "There was an error logging in. Please try again.")
        return redirect('login_user')

    return render(request, 'home/login.html', {'next': next_url})

def logout_user(request):
    logout(request)
    messages.success(request, "You Have Been Logged Out...")
    return redirect('login_user')
