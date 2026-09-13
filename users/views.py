from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .forms import CustomUserCreationForm, CustomUserDeleteForm
from .models import LoginHistory


def signup_view(request):
    """Register a new user."""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'ثبت نام با موفقیت انجام شد')
            return redirect('signin')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/signup.html', {'form': form})


def signin_view(request):
    """Authenticate the user and record a successful login."""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            LoginHistory.objects.create(
                user=user,
                ip_address=request.META.get('REMOTE_ADDR', ''),
            )
            messages.success(request, 'ورود موفقیت‌آمیز بود')
            return redirect('dashboard')
        messages.error(request, 'نام کاربری یا رمز عبور اشتباه است')
    return render(request, 'users/signin.html')


def signout_view(request):
    """Log out the currently authenticated user."""
    logout(request)
    messages.info(request, 'خروج از حساب انجام شد')
    return redirect('signin')


@login_required
@require_http_methods(['GET', 'POST'])
def delete_profile_view(request):
    """Delete the current user's account after password confirmation."""
    if request.method == 'POST':
        form = CustomUserDeleteForm(request.POST)
        if form.is_valid():
            if request.user.check_password(form.cleaned_data['password']):
                user = request.user
                logout(request)
                user.delete()
                messages.success(request, 'حساب کاربری شما با موفقیت حذف شد')
                return redirect('signup')
            messages.error(request, 'رمز عبور نامعتبر است')
    else:
        form = CustomUserDeleteForm()
    return render(request, 'users/delete_confirm.html', {'form': form})


@login_required
def login_history_view(request):
    """Display the authenticated user's login history."""
    return render(request, 'users/login_history.html', {
        'history': request.user.login_history.all()[:50],
    })
