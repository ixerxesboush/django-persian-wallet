from django.urls import path

from .views import delete_profile_view, login_history_view, signin_view, signout_view, signup_view

urlpatterns = [
    path('signup/', signup_view, name='signup'),
    path('signin/', signin_view, name='signin'),
    path('signout/', signout_view, name='signout'),
    path('delete/', delete_profile_view, name='delete_profile'),
    path('login-history/', login_history_view, name='login_history'),
]
