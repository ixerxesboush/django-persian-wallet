from django.contrib import messages
import json

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

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
    """Display one installment, its payments, and chart data."""
    installment = get_object_or_404(
        Installment.objects.prefetch_related('payments'), pk=pk, user=request.user,
    )
    payments = list(installment.payments.all())
    overdues = list(installment.overdues.all())
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
        amount = min(installment.monthly_amount, installment.remaining_amount)
        if not installment.is_active:
            messages.error(request, 'این قسط قبلاً تسویه شده است')
        elif amount <= 0:
            messages.error(request, 'این قسط قبلاً پرداخت شده است')
        elif user.balance < amount:
            messages.error(request, 'موجودی کیف پول کافی نیست')
        else:
            user.balance -= amount
            user.save(update_fields=['balance'])
            installment.paid_amount += amount
            installment.save()
            InstallmentPayment.objects.create(installment=installment, amount=amount)
            messages.success(request, 'قسط با موفقیت پرداخت شد')
    return redirect('installment_detail', pk=pk)


@login_required
@require_POST
def mark_overdue_view(request, pk):
    """Mark the current month as overdue once."""
    installment = get_object_or_404(Installment, pk=pk, user=request.user)
    due_date = timezone.localdate().replace(day=1)
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
        overdue = get_object_or_404(
            InstallmentOverdue.objects.select_for_update(),
            pk=overdue_id,
            installment=installment,
            is_resolved=False,
        )
        user = User.objects.select_for_update().get(pk=request.user.pk)
        amount = min(installment.monthly_amount, installment.remaining_amount)
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
