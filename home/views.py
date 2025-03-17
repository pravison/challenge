from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import date, timedelta
from django.utils.text import slugify
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from datetime import date
from businesses.models import Business, Staff, Coupone, StoreChallenge, RefferralCode, BusinessCustomer
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


def verify_reset_code(request):
    if request.method == 'POST':
        form = PasswordResetCodeForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
        try:
            reset_code = PasswordResetCode.objects.filter(code=code, is_valid=True).order_by('-created_at').first()
            if reset_code.is_expired():
                reset_code.is_valid = False
                reset_code.save()
                messages.error(request, 'This code has expired.')
            else:
                # Invalidate the code
                reset_code.is_valid = False
                reset_code.save()
                # Redirect to password reset form
                request.session['password_reset_user_id'] = reset_code.user.id
                return redirect('reset_password')
        except PasswordResetCode.DoesNotExist:
            messages.error(request, 'Invalid or expired code.')
    form = PasswordResetCodeForm()
    return render(request, 'home/verify_reset_code.html', {'form': form} )

def reset_password(request):
    user_id = request.session.get('password_reset_user_id')
    if not user_id:
        return redirect('request_reset_code')
    
    user = User.objects.get(id=user_id)
    try:
        reset_code = PasswordResetCode.objects.filter(user=user).order_by('-created_at').first()
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
    #Business.objects.filter(challenges__participants=creator).distinct().prefetch_related("challenges") #business user has participated in their challange
    
    
    refferal_codes = RefferralCode.objects.filter(customer=customer)

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
        # 'business_customer': business_customer
    }
    return render(request, 'home/profile.html', context)

# Create your views here.
def register_user(request):
    pricing_plan = request.GET.get('pricing_plan') or ''
    add_staff_to = request.GET.get('add_staff_to') or ''
    add_customer_to = request.GET.get('add_customer_to') or ''  # Corrected this line
    code = request.GET.get('code') or ''
    next = request.GET.get('next') or ''
    print(add_customer_to)
    print(code)
    context = {
        'add_staff_to': add_staff_to,
        'add_customer_to': add_customer_to,
        'pricing_plan': pricing_plan,
        'code': code,
        'next': next,
    }

    if request.method == "POST":
        print(add_customer_to)
        print(code)
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
        

        # Handle redirect for "next" parameter
        if next != '':
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect(next)

        # Default redirect after registration
        user = authenticate(username=username, password=password)
        login(request, user)
        return redirect('profile')

    return render(request, 'home/register.html', context)

def login_user(request):
    next = request.GET.get('next') or ''
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        # Authenticate
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            messages.success(request, "You Have Been Logged In!")
            if next != '':
                return redirect(next)
            return redirect('profile')
        else:
            messages.success(request, "There Was An Error Logging In, Please Try Again...")
            return redirect('login_user')
    else:
        return render(request, 'home/login.html', {'next':next})

def logout_user(request):
    logout(request)
    messages.success(request, "You Have Been Logged Out...")
    return redirect('login_user')
