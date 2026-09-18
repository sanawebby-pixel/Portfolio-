from django import forms
from django.contrib.auth.models import User
from welfare_app.models import UserProfile, Department, Employee
from .employee_forms import TailwindMixin


ROLE_CHOICES = [
    ('Admin', 'Administrator (Full Access)'),
    ('Welfare Officer', 'Welfare Officer (Claims, Visits, Reports)'),
    ('HR Staff', 'HR Staff (Employees & Personnel Records)'),
    ('Finance Officer', 'Finance Officer (Payments, Budgets, Treasury)'),
    ('Approver', 'Approver / Manager (Claim Authorizations)'),
    ('Medical Officer', 'Medical Officer (Diagnostics & Records)'),
    ('Inventory Officer', 'Inventory & Pharmacy Officer'),
    ('Viewer', 'Viewer (Read-only Access)'),
]


class UserCreateForm(TailwindMixin, forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter strong temporary password'}),
        label="Account Password"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm temporary password'}),
        label="Confirm Password"
    )
    role = forms.ChoiceField(choices=ROLE_CHOICES, initial='Welfare Officer', label="Assigned System Role")
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True),
        required=False,
        label="Assigned Department"
    )
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.all(),
        required=False,
        label="Linked Employee Profile"
    )
    phone = forms.CharField(
        max_length=50,
        required=False,
        label="Contact Phone #",
        widget=forms.TextInput(attrs={'placeholder': 'e.g. +92-300-1234567'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password']
        labels = {
            'username': 'Username / Login ID',
            'email': 'Official Email Address',
            'first_name': 'First Name',
            'last_name': 'Last Name',
        }
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'e.g. javed.ahmed'}),
            'email': forms.EmailInput(attrs={'placeholder': 'e.g. javed@welfare.org'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'e.g. Javed'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'e.g. Ahmed'}),
        }

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
            raise forms.ValidationError('Passwords do not match. Please re-enter both identical passwords.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class UserUpdateForm(TailwindMixin, forms.ModelForm):
    role = forms.ChoiceField(choices=ROLE_CHOICES, label="Assigned System Role")
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True),
        required=False,
        label="Assigned Department"
    )
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.all(),
        required=False,
        label="Linked Employee Profile"
    )
    phone = forms.CharField(
        max_length=50,
        required=False,
        label="Contact Phone #",
        widget=forms.TextInput(attrs={'placeholder': 'e.g. +92-300-1234567'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active']
        labels = {
            'username': 'Username / Login ID',
            'email': 'Official Email Address',
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'is_active': 'Account Active Status',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True


class AdminPasswordChangeForm(TailwindMixin, forms.Form):
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter new password'}),
        label="New Password"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm new password'}),
        label="Confirm New Password"
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password')
        p2 = cleaned_data.get('confirm_password')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned_data


class UserProfileForm(TailwindMixin, forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['role', 'department', 'employee', 'phone', 'avatar']
        labels = {
            'role': 'Assigned Role',
            'department': 'Department',
            'employee': 'Linked Employee Profile',
            'phone': 'Contact Phone',
            'avatar': 'Profile Picture / Avatar',
        }


