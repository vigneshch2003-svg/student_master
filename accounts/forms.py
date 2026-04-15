from django import forms
from django.contrib.auth.models import User


class StaffForm(forms.ModelForm):
    """Single form for both creating and editing staff."""
    ROLE_CHOICES = [('Staff', 'Staff'), ('Admin', 'Admin')]

    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'sf-input'}))
    password1 = forms.CharField(
        label='Password', required=False,
        widget=forms.PasswordInput(attrs={'class': 'sf-input', 'placeholder': 'Leave blank to keep current'})
    )
    password2 = forms.CharField(
        label='Confirm Password', required=False,
        widget=forms.PasswordInput(attrs={'class': 'sf-input', 'placeholder': 'Repeat password'})
    )
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.Select(attrs={'class': 'sf-input'}))
    subject = forms.CharField(
        required=False, label='Assigned Subject',
        widget=forms.TextInput(attrs={'class': 'sf-input', 'placeholder': 'e.g. Mathematics'})
    )

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {'username': forms.TextInput(attrs={'class': 'sf-input'})}

    def clean_email(self):
        email = self.cleaned_data.get('email')
        qs = User.objects.filter(email=email)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1', '').strip()
        p2 = cleaned_data.get('password2', '').strip()
        # Password required only on create
        if not self.instance.pk and not p1:
            raise forms.ValidationError('Password is required.')
        if p1 and p1 != p2:
            raise forms.ValidationError('Passwords do not match.')
        if cleaned_data.get('role') == 'Staff' and not cleaned_data.get('subject', '').strip():
            raise forms.ValidationError('Subject is required for Staff role.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        p1 = self.cleaned_data.get('password1', '').strip()
        if p1:
            user.set_password(p1)
        if commit:
            user.save()
        return user
