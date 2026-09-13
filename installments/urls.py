from django.urls import path

from .views import (
    create_installment_view,
    installment_detail_view,
    installment_list_view,
    installment_payment_view,
    mark_overdue_view,
    resolve_overdue_view,
)

urlpatterns = [
    path('', installment_list_view, name='installment_list'),
    path('create/', create_installment_view, name='create_installment'),
    path('<int:pk>/', installment_detail_view, name='installment_detail'),
    path('<int:pk>/pay/', installment_payment_view, name='installment_pay'),
    path('<int:pk>/overdue/', mark_overdue_view, name='mark_overdue'),
    path('<int:pk>/overdue/<int:overdue_id>/pay/', resolve_overdue_view, name='resolve_overdue'),
    path('<int:pk>/resolve-overdue/', resolve_overdue_view, {'overdue_id': None}, name='resolve_overdue_by_date'),
    path('pay/<int:pk>/', installment_payment_view, name='pay_installment'),
]
