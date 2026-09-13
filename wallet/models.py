from django.conf import settings
from django.db import models


class Transaction(models.Model):
    DEPOSIT = 'deposit'
    WITHDRAW = 'withdraw'
    TYPE_CHOICES = [
        (DEPOSIT, 'واریز'),
        (WITHDRAW, 'برداشت'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name='کاربر',
    )
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name='نوع')
    amount = models.PositiveIntegerField(verbose_name='مبلغ (تومان)')
    comment = models.TextField(blank=True, verbose_name='توضیحات')
    balance_after = models.IntegerField(verbose_name='موجودی پس از تراکنش')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='زمان')

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'تراکنش'
        verbose_name_plural = 'تراکنش‌ها'
