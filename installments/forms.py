from django import forms

from core.utils import jalali_to_gregorian

from .models import Installment


class InstallmentCreateForm(forms.ModelForm):
    """Form to create a new installment."""

    start_date = forms.CharField(
        label='تاریخ شروع (شمسی)',
        widget=forms.TextInput(attrs={
            'class': 'form-control jalali-datepicker',
            'placeholder': '1402/01/01',
            'data-jalali': 'true',
            'data-format': 'YYYY/MM/DD',
        }),
    )

    class Meta:
        model = Installment
        fields = ['name', 'total_amount', 'monthly_amount', 'start_date']
        labels = {
            'name': 'نام قسط',
            'total_amount': 'مبلغ کل قسط',
            'monthly_amount': 'مبلغ هر قسط ماهانه',
            'start_date': 'تاریخ شروع',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام قسط'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'مبلغ کل به تومان', 'step': '1'}),
            'monthly_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'مبلغ ماهانه به تومان', 'step': '1'}),
        }

    def clean_start_date(self):
        value = self.cleaned_data['start_date']
        try:
            year, month, day = [int(part) for part in value.replace('-', '/').split('/')]
            return jalali_to_gregorian(year, month, day)
        except (AttributeError, TypeError, ValueError):
            raise forms.ValidationError('تاریخ وارد شده معتبر نیست')
