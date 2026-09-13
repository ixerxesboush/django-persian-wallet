from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    """Form for creating a new user account."""

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            'username',
            'first_name',
            'last_name',
            'international_id',
            'password1',
            'password2',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'نام کاربری'
        self.fields['first_name'].label = 'نام'
        self.fields['last_name'].label = 'نام خانوادگی'
        self.fields['international_id'].label = 'شناسه بین‌المللی'
        self.fields['password1'].label = 'رمز عبور'
        self.fields['password2'].label = 'تأیید رمز عبور'

        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

        self.fields['username'].widget.attrs['placeholder'] = 'نام کاربری'
        self.fields['first_name'].widget.attrs['placeholder'] = 'نام'
        self.fields['last_name'].widget.attrs['placeholder'] = 'نام خانوادگی'
        self.fields['international_id'].widget.attrs['placeholder'] = 'شناسه بین‌المللی'
        self.fields['password1'].widget.attrs['placeholder'] = 'رمز عبور'
        self.fields['password2'].widget.attrs['placeholder'] = 'تأیید رمز عبور'


class CustomUserDeleteForm(forms.Form):
    """Confirmation form to delete a profile."""

    password = forms.CharField(
        label='رمز عبور',
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'رمز عبور'}),
    )
