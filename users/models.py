from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """User model for the application."""

    first_name = models.CharField(max_length=150, blank=True, verbose_name='نام')
    last_name = models.CharField(max_length=150, blank=True, verbose_name='نام خانوادگی')
    international_id = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='شناسه بین‌المللی',
    )
    balance = models.IntegerField(default=0, verbose_name='موجودی (تومان)')

    class Meta:
        verbose_name = 'کاربر'
        verbose_name_plural = 'کاربران'

    def __str__(self):
        return self.get_full_name() or self.username


class LoginHistory(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='login_history',
        verbose_name='کاربر',
    )
    login_time = models.DateTimeField(auto_now_add=True, verbose_name='زمان ورود')
    ip_address = models.CharField(max_length=50, blank=True, verbose_name='نشانی IP')

    class Meta:
        ordering = ['-login_time']
        verbose_name = 'سابقه ورود'
        verbose_name_plural = 'سوابق ورود'
