from django.shortcuts import render, redirect
from datetime import datetime
from django.http import HttpResponse
from .forms import UserForm
from .models import User, UserProfile
from django.contrib import messages, auth
from vendor.forms import VendorForm
from .utils import detectUser, send_verification_email
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required, user_passes_test
from django.template.defaultfilters import slugify
from vendor.models import Vendor
from orders.models import Order
# Create your views here.
# Restrict the vendor from accessing the customer page
def check_role_vendor(user):
    if user.role == 1:
        return True
    else:
        raise PermissionDenied


# Restrict the customer from accessing the vendor page
def check_role_customer(user):
    if user.role == 2:
        return True
    else:
        raise PermissionDenied

def registerUser(request):
   if request.user.is_authenticated:
        messages.warning(request, 'You are already logged in!')
        return redirect('myAccount')
   if request.method == 'POST':
      form = UserForm(request.POST)
      if form.is_valid():
         # password = form.cleaned_data['password']
         # user = form.save(commit=False)
         # user.set_password(password)
         # user.role = User.CUSTOMER
         # user.save()

        # Create the user using create_user method
         first_name = form.cleaned_data['first_name']
         last_name = form.cleaned_data['last_name']
         username = form.cleaned_data['username']
         email = form.cleaned_data['email']
         password = form.cleaned_data['password']
         user = User.objects.create_user(first_name=first_name, last_name=last_name, username=username, email=email, password=password)
         user.role = User.CUSTOMER
         user.save()
         
        #  mail_subject = 'Please activate your account'
        #  email_template = 'accounts/emails/account_verification_email.html'
         send_verification_email(request, user)
         messages.success(request, 'Your account has been registered sucessfully!')
         return redirect('registerUser')
      
      else:
            print('invalid form')
            print(form.errors)
      
   else:
      form = UserForm()
   context = {
      'form':form,
   }
   return render(request, 'accounts/registerUser.html',context)


def registerVendor(request):
   if request.user.is_authenticated:
        messages.warning(request, 'You are already logged in!')
        return redirect('myAccount')

   elif request.method == 'POST':
        # store the data and create the user
        form = UserForm(request.POST)
        v_form = VendorForm(request.POST, request.FILES)
        if form.is_valid() and v_form.is_valid:
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = User.objects.create_user(first_name=first_name, last_name=last_name, username=username, email=email, password=password)
            user.role = User.VENDOR
            user.save()
            vendor = v_form.save(commit=False)
            vendor.user = user
            vendor_name = v_form.cleaned_data['vendor_name']
            vendor.vendor_slug = slugify(vendor_name)+'-'+str(user.id)
            user_profile = UserProfile.objects.get(user=user)
            vendor.user_profile = user_profile
            vendor.save()

            # Send verification email
            # mail_subject = 'Please activate your account'
            # email_template = 'accounts/emails/account_verification_email.html'
            send_verification_email(request, user)

            messages.success(request, 'Your account has been registered sucessfully! Please wait for the approval.')
            return redirect('registerVendor')
        else:
            print('invalid form')
            print(form.errors)
   else:
        form = UserForm()
        v_form = VendorForm()

   context = {
        'form': form,
        'v_form': v_form,
    }

   return render(request, 'accounts/registerVendor.html',context)

def login(request):
    if request.user.is_authenticated:
        messages.warning(request, 'You are already logged in!')
        return redirect('myAccount')
    elif request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = auth.authenticate(email=email, password=password)

        if user is not None:
            auth.login(request, user)
            messages.success(request, 'You are now logged in.')
            return redirect('myAccount')
        else:
            messages.error(request, 'Invalid login credentials')
            return redirect('login')
    return render(request, 'accounts/login.html')

def logout(request):
   auth.logout(request)
   messages.info(request, 'You are logged out.')
   return redirect('login')

@login_required(login_url = 'login')
def myAccount(request):
    user = request.user
    redirectUrl = detectUser(user)
    return redirect(redirectUrl)


@login_required(login_url = 'login')
@user_passes_test(check_role_customer)
def custDashboard(request):
    orders = Order.objects.filter(user=request.user,is_ordered=True)
    context = {
        'orders':orders,
        'orders_count':orders.count(),
    }
    return render(request, 'accounts/custDashboard.html',context)


@login_required(login_url = 'login')
@user_passes_test(check_role_vendor)
def vendorDashboard(request):
    vendor = Vendor.objects.get(user=request.user)
    orders = Order.objects.filter(vendors__in=[vendor.id], is_ordered=True).order_by('created_at')
    # recent_orders = orders[:10]

    # # current month's revenue
    # current_month = datetime.datetime.now().month
    # current_month_orders = orders.filter(vendors__in=[vendor.id], created_at__month=current_month)
    # current_month_revenue = 0
    # for i in current_month_orders:
    #     current_month_revenue += i.get_total_by_vendor()['grand_total']
    

    # total revenue
    total_revenue = 0
    # for i in orders:
    #     total_revenue += i.get_total_by_vendor()['grand_total']
    context = {
        'orders': orders,
        'orders_count': orders.count(),
        # 'recent_orders': recent_orders,
        'total_revenue': total_revenue,
        # 'current_month_revenue': current_month_revenue,
    }
    return render(request, 'accounts/vendorDashboard.html', context)


def activate(request, uidb64, token):
    # Activate the user by setting the is_active status to True
    return
    # try:
    #     uid = urlsafe_base64_decode(uidb64).decode()
    #     user = User._default_manager.get(pk=uid)
    # except(TypeError, ValueError, OverflowError, User.DoesNotExist):
    #     user = None

    # if user is not None and default_token_generator.check_token(user, token):
    #     user.is_active = True
    #     user.save()
    #     messages.success(request, 'Congratulation! Your account is activated.')
    #     return redirect('myAccount')
    # else:
    #     messages.error(request, 'Invalid activation link')
    #     return redirect('myAccount')