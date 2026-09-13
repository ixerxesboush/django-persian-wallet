from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import TransactionForm
from .models import Transaction

User = get_user_model()


@login_required
def dashboard_view(request):
    """Show the wallet dashboard and recent activity."""
    transactions = request.user.transactions.all()
    return render(request, 'wallet/dashboard.html', {
        'user': request.user,
        'recent_transactions': transactions[:10],
        'recent_logins': request.user.login_history.all()[:5],
        'deposit_total': transactions.filter(type=Transaction.DEPOSIT).aggregate(total=Sum('amount'))['total'] or 0,
        'withdraw_total': transactions.filter(type=Transaction.WITHDRAW).aggregate(total=Sum('amount'))['total'] or 0,
    })


@login_required
def deposit_view(request):
    """Deposit whole Tomans and record the transaction."""
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = User.objects.select_for_update().get(pk=request.user.pk)
                amount = form.cleaned_data['amount']
                user.balance += amount
                user.save(update_fields=['balance'])
                Transaction.objects.create(
                    user=user, type=Transaction.DEPOSIT, amount=amount,
                    comment=form.cleaned_data['comment'], balance_after=user.balance,
                )
            messages.success(request, 'مبلغ با موفقیت واریز شد')
            return redirect('dashboard')
    else:
        form = TransactionForm()
    return render(request, 'wallet/deposit.html', {'form': form})


@login_required
def withdraw_view(request):
    """Withdraw whole Tomans when the wallet has sufficient funds."""
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            if _withdraw(request.user, form.cleaned_data['amount'], form.cleaned_data['comment']):
                messages.success(request, 'مبلغ با موفقیت برداشت شد')
                return redirect('dashboard')
            messages.error(request, 'موجودی کافی نیست')
    else:
        form = TransactionForm()
    return render(request, 'wallet/withdraw.html', {'form': form})


@login_required
@require_POST
def withdraw_max_view(request):
    """Withdraw the complete current wallet balance."""
    if _withdraw(request.user, request.user.balance, request.POST.get('comment', 'برداشت حداکثر موجودی')):
        messages.success(request, 'کل موجودی با موفقیت برداشت شد')
    else:
        messages.error(request, 'موجودی کیف پول صفر است')
    return redirect('dashboard')


def _withdraw(user, amount, comment=''):
    with transaction.atomic():
        locked_user = User.objects.select_for_update().get(pk=user.pk)
        if amount <= 0 or locked_user.balance < amount:
            return False
        locked_user.balance -= amount
        locked_user.save(update_fields=['balance'])
        Transaction.objects.create(
            user=locked_user, type=Transaction.WITHDRAW, amount=amount,
            comment=comment, balance_after=locked_user.balance,
        )
    return True


@login_required
def transaction_history_view(request):
    """Display all wallet transactions as an ATM-style receipt."""
    return render(request, 'wallet/transaction_history.html', {
        'transactions': request.user.transactions.all()[:100],
    })
