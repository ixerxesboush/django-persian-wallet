from django import forms


class TransactionForm(forms.Form):
    """Base form for wallet deposits and withdrawals."""

    amount = forms.IntegerField(
        min_value=1,
        label='مبلغ (تومان)',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'مبلغ به تومان', 'step': '1'}),
    )
    comment = forms.CharField(
        required=False,
        label='توضیحات (اختیاری)',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
    )
