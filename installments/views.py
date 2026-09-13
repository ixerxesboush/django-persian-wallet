from django.contrib import messages
import json
import math
import datetime

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from dateutil.relativedelta import relativedelta

from core.utils import gregorian_to_jalali, toman_format
from .forms import InstallmentCreateForm
from .models import Installment, InstallmentOverdue, InstallmentPayment

User = get_user_model()


@login_required
def installment_list_view(request):
    """Display installments and aggregate statistics for the current user."""
    installments = request.user.installments.all().prefetch_related('payments')
    completed = installments.filter(is_active=False)
    return render(request, 'installments/list.html', {
        'installments': installments,
        'active_installments': installments.filter(is_active=True),
        'completed_installments': completed,
        'total_count': installments.count(),
        'completed_count': completed.count(),
        'total_paid': installments.aggregate(total=Sum('paid_amount'))['total'] or 0,
        'total_remaining': installments.aggregate(total=Sum('remaining_amount'))['total'] or 0,
        'stats': [
            ('تعداد کل اقساط', installments.count()),
            ('اقساط تسویه شده', completed.count()),
            ('کل پرداخت شده', toman_format(installments.aggregate(total=Sum('paid_amount'))['total'] or 0)),
            ('کل مانده بدهی', toman_format(installments.aggregate(total=Sum('remaining_amount'))['total'] or 0)),
        ],
    })


@login_required
def create_installment_view(request):
    """Create a new installment for the logged-in user."""
    if request.method == 'POST':
        form = InstallmentCreateForm(request.POST)
        if form.is_valid():
            installment = form.save(commit=False)
            installment.user = request.user
            installment.save()
            messages.success(request, 'قسط جدید با موفقیت ایجاد شد')
            return redirect('installment_list')
    else:
        form = InstallmentCreateForm()
    return render(request, 'installments/create.html', {'form': form})


@login_required
def installment_detail_view(request, pk):
    """Display the dynamic installment book and financial summary."""
    installment = get_object_or_404(
        Installment.objects.prefetch_related('payments'), pk=pk, user=request.user,
    )
    payments = list(installment.payments.all())
    overdues = list(installment.overdues.all())
    total_months = math.ceil(installment.total_amount / installment.monthly_amount)
    end_date = installment.start_date + relativedelta(months=total_months - 1)
    paid_due_dates = {
        payment.due_date or payment.payment_date.date()
        for payment in payments
    }
    overdue_dates = {
        overdue.due_date
        for overdue in overdues
        if not overdue.is_resolved
    }
    schedule_list = []
    remaining_total = installment.total_amount
    current_date = installment.start_date
    paid_count = overdue_count = 0
    total_paid_amount = total_overdue_amount = 0
    for index in range(1, total_months + 1):
        month_amount = remaining_total if index == total_months else installment.monthly_amount
        remaining_total -= month_amount
        if current_date in paid_due_dates:
            status = 'paid'
            paid_count += 1
            total_paid_amount += month_amount
        elif current_date in overdue_dates:
            status = 'overdue'
            overdue_count += 1
            total_overdue_amount += month_amount
        else:
            status = 'pending'
        schedule_list.append({
            'index': index,
            'jalali_date': gregorian_to_jalali(current_date),
            'amount': month_amount,
            'status': status,
            'due_date': current_date,
        })
        current_date += relativedelta(months=1)
    next_due_date = next(
        (item['due_date'] for item in schedule_list if item['status'] == 'pending'),
        None,
    )
    cumulative = 0
    chart_labels, chart_values = [], []
    for payment in payments:
        cumulative += payment.amount
        chart_labels.append(gregorian_to_jalali(payment.payment_date))
        chart_values.append(cumulative)
    return render(request, 'installments/detail.html', {
        'installment': installment,
        'payments': payments,
        'payment_rows': [
            {
                'date': gregorian_to_jalali(payment.payment_date),
                'amount': payment.amount,
                'comment': payment.comment,
            }
            for payment in payments
        ],
        'overdue_rows': [
            {
                'item': overdue,
                'date': gregorian_to_jalali(overdue.due_date),
            }
            for overdue in overdues
        ],
        'payment_count': len(payments),
        'paid_count': paid_count,
        'overdue_count': overdue_count,
        'total_months': total_months,
        'schedule_list': schedule_list,
        'start_date_jalali': gregorian_to_jalali(installment.start_date),
        'end_date_jalali': gregorian_to_jalali(end_date),
        'remaining_balance': installment.total_amount - total_paid_amount,
        'total_paid_amount': total_paid_amount,
        'total_overdue_amount': total_overdue_amount,
        'next_due_date': next_due_date,
        'overdues': overdues,
        'overdue_total': len([item for item in overdues if not item.is_resolved]) * installment.monthly_amount,
        'chart_labels': json.dumps(chart_labels),
        'chart_values': json.dumps(chart_values),
    })


@login_required
@require_POST
def installment_payment_view(request, pk):
    """Pay one installment and create a payment history record atomically."""
    with transaction.atomic():
        installment = get_object_or_404(
            Installment.objects.select_for_update(), pk=pk, user=request.user,
        )
        user = User.objects.select_for_update().get(pk=request.user.pk)
        due_date = _parse_due_date(request.POST.get('due_date')) or installment.start_date
        already_paid = InstallmentPayment.objects.filter(
            installment=installment, due_date=due_date,
        ).exists()
        amount = _scheduled_amount(installment, due_date)
        if not installment.is_active:
            messages.error(request, 'این قسط قبلاً تسویه شده است')
        elif already_paid:
            messages.error(request, 'این قسط قبلاً پرداخت شده است')
        elif user.balance < amount:
            messages.error(request, 'موجودی کیف پول کافی نیست')
        else:
            user.balance -= amount
            user.save(update_fields=['balance'])
            installment.paid_amount += amount
            installment.save()
            InstallmentPayment.objects.create(
                installment=installment, amount=amount, due_date=due_date,
            )
            messages.success(request, 'قسط با موفقیت پرداخت شد')
    return redirect('installment_detail', pk=pk)


@login_required
@require_POST
def mark_overdue_view(request, pk):
    """Mark the current month as overdue once."""
    installment = get_object_or_404(Installment, pk=pk, user=request.user)
    due_date = _parse_due_date(request.POST.get('due_date')) or timezone.localdate().replace(day=1)
    if InstallmentPayment.objects.filter(
        installment=installment,
        payment_date__year=due_date.year,
        payment_date__month=due_date.month,
    ).exists():
        messages.error(request, 'این قسط قبلاً پرداخت شده است')
        return redirect('installment_detail', pk=pk)
    if InstallmentOverdue.objects.filter(installment=installment, due_date=due_date).exists():
        messages.error(request, 'این ماه قبلاً به عنوان معوقه ثبت شده است')
        return redirect('installment_detail', pk=pk)
    InstallmentOverdue.objects.create(
        installment=installment,
        due_date=due_date,
        reason=request.POST.get('reason', '').strip(),
    )
    installment.overdue_count = InstallmentOverdue.objects.filter(
        installment=installment, is_resolved=False,
    ).count()
    installment.last_overdue_date = timezone.now()
    installment.save(update_fields=['overdue_count', 'last_overdue_date'])
    messages.warning(request, 'این قسط به عنوان معوقه ثبت شد. در صورت امکان، ماه آینده می‌توانید آن را پرداخت کنید.')
    return redirect('installment_detail', pk=pk)


@login_required
@require_POST
def resolve_overdue_view(request, pk, overdue_id):
    """Pay and resolve one overdue month atomically."""
    with transaction.atomic():
        installment = get_object_or_404(
            Installment.objects.select_for_update(),
            pk=pk,
            user=request.user,
        )
        overdue_query = InstallmentOverdue.objects.select_for_update().filter(
            installment=installment, is_resolved=False,
        )
        if overdue_id is not None:
            overdue_query = overdue_query.filter(pk=overdue_id)
        else:
            due_date = _parse_due_date(request.POST.get('overdue_date'))
            overdue_query = overdue_query.filter(due_date=due_date)
        overdue = get_object_or_404(overdue_query)
        user = User.objects.select_for_update().get(pk=request.user.pk)
        amount = _scheduled_amount(installment, overdue.due_date)
        if amount <= 0:
            messages.error(request, 'این قسط قبلاً پرداخت شده است')
        elif user.balance < amount:
            messages.error(request, 'موجودی کافی نیست')
        else:
            user.balance -= amount
            user.save(update_fields=['balance'])
            installment.paid_amount += amount
            installment.save()
            InstallmentPayment.objects.create(
                installment=installment,
                amount=amount,
                due_date=overdue.due_date,
                comment='پرداخت قسط معوقه',
            )
            overdue.is_resolved = True
            overdue.resolved_date = timezone.now()
            overdue.save(update_fields=['is_resolved', 'resolved_date'])
            installment.overdue_count = InstallmentOverdue.objects.filter(
                installment=installment, is_resolved=False,
            ).count()
            installment.save(update_fields=['overdue_count'])
            messages.success(request, 'معوقه با موفقیت پرداخت شد')
    return redirect('installment_detail', pk=pk)


pay_installment_view = installment_payment_view


def _parse_due_date(value):
    if not value:
        return None
    try:
        return datetime.date.fromisoformat(value)
    except ValueError:
        return None


def _scheduled_amount(installment, due_date):
    total_months = math.ceil(installment.total_amount / installment.monthly_amount)
    last_date = installment.start_date + relativedelta(months=total_months - 1)
    if due_date == last_date:
        return installment.total_amount - installment.monthly_amount * (total_months - 1)
    return installment.monthly_amount
