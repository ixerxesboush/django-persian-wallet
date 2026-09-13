from django.urls import path

from .views import dashboard_view, deposit_view, transaction_history_view, withdraw_max_view, withdraw_view

urlpatterns = [
    path('dashboard/', dashboard_view, name='dashboard'),
    path('deposit/', deposit_view, name='deposit'),
    path('withdraw/', withdraw_view, name='withdraw'),
    path('withdraw-max/', withdraw_max_view, name='withdraw_max'),
    path('transactions/', transaction_history_view, name='transaction_history'),
]
