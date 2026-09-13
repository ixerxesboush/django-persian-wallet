from django.conf import settings
from django.db import models

from core.utils import gregorian_to_jalali


class Installment(models.Model):
    """Represents a user's installment schedule."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='installments',
        verbose_name='کاربر',
    )
    name = models.CharField(max_length=200, verbose_name='نام قسط')
    total_amount = models.PositiveIntegerField(verbose_name='مبلغ کل قسط (تومان)')
    monthly_amount = models.PositiveIntegerField(verbose_name='مبلغ هر قسط ماهانه (تومان)')
    paid_amount = models.PositiveIntegerField(default=0, verbose_name='مبلغ پرداخت شده (تومان)')
    remaining_amount = models.PositiveIntegerField(default=0, verbose_name='مانده بدهی (تومان)')
    start_date = models.DateField(verbose_name='تاریخ شروع')
    is_active = models.BooleanField(default=True, verbose_name='وضعیت فعال')
    overdue_count = models.PositiveIntegerField(default=0, verbose_name='تعداد ماه‌های معوقه')
    last_overdue_date = models.DateTimeField(null=True, blank=True, verbose_name='آخرین تاریخ معوقه')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')

    class Meta:
        verbose_name = 'قسط'
        verbose_name_plural = 'اقساط'

    def save(self, *args, **kwargs):
        self.remaining_amount = self.total_amount - self.paid_amount
        self.is_active = self.remaining_amount > 0
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_start_date_jalali(self):
        return gregorian_to_jalali(self.start_date)


class InstallmentPayment(models.Model):
    installment = models.ForeignKey(
        Installment,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='قسط',
    )
    amount = models.PositiveIntegerField(verbose_name='مبلغ (تومان)')
    due_date = models.DateField(null=True, blank=True, verbose_name='تاریخ سررسید')
    payment_date = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ پرداخت')
    comment = models.TextField(blank=True, verbose_name='توضیحات')

    class Meta:
        ordering = ['payment_date']
        verbose_name = 'پرداخت قسط'
        verbose_name_plural = 'پرداخت‌های اقساط'


class InstallmentOverdue(models.Model):
    installment = models.ForeignKey(
        Installment,
        on_delete=models.CASCADE,
        related_name='overdues',
        verbose_name='قسط',
    )
    due_date = models.DateField(verbose_name='ماه سررسید')
    marked_date = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ثبت')
    reason = models.TextField(blank=True, verbose_name='علت')
    is_resolved = models.BooleanField(default=False, verbose_name='حل شده')
    resolved_date = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ تسویه')

    class Meta:
        ordering = ['-due_date']
        constraints = [
            models.UniqueConstraint(
                fields=['installment', 'due_date'],
                name='unique_installment_overdue_month',
            ),
        ]
        verbose_name = 'قسط معوقه'
        verbose_name_plural = 'اقساط معوقه'
