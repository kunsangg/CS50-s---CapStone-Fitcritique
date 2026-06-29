from django import forms
from django.contrib.auth.models import User

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'w-full bg-zinc-900 border border-zinc-700 text-zinc-100 rounded-lg px-4 py-2 mt-1 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500'}))
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'w-full bg-zinc-900 border border-zinc-700 text-zinc-100 rounded-lg px-4 py-2 mt-1 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500'}), label='Confirm Password')

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'w-full bg-zinc-900 border border-zinc-700 text-zinc-100 rounded-lg px-4 py-2 mt-1 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500'}),
            'email': forms.EmailInput(attrs={'class': 'w-full bg-zinc-900 border border-zinc-700 text-zinc-100 rounded-lg px-4 py-2 mt-1 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500'})
        }

    def clean_password_confirm(self):
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Passwords do not match.")
        return password_confirm
