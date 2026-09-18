from django import forms
from django.contrib.auth.models import User
from welfare_app.models import UserProfile, Employee
from .employee_forms import TailwindMixin


ROLE_CHOICES = [
    ('Admin', 'Admin'),
    ('HR Officer', 'HR Officer'),
    ('Welfare Officer', 'Welfare Officer'),
    ('Medical Officer', 'Medical Officer'),
    ('Finance Officer', 'Finance Officer'),
    ('Manager', 'Manager'),
    ('Inventory Officer', 'Inventory Officer'),
    ('Employee', 'Employee'),
]


class UserCreateForm(TailwindMixin, forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput())
    role = forms.ChoiceField(choices=ROLE_CHOICES, initial='Employee')

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm = cleaned_data.get('confirm_password')
        if password and confirm and password != confirm:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class UserUpdateForm(TailwindMixin, forms.ModelForm):
    role = forms.ChoiceField(choices=ROLE_CHOICES)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active']


class UserProfileForm(TailwindMixin, forms.ModelForm):
    class Meta:
        model = UserProfile
        exclude = ['user', 'created_at', 'updated_at']
