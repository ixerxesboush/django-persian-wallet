from django.contrib import admin

from .models import Installment, InstallmentOverdue, InstallmentPayment


admin.site.register(Installment)
admin.site.register(InstallmentPayment)
admin.site.register(InstallmentOverdue)
