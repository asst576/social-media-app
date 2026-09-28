from django import forms
from django.contrib.auth.forms import UserCreationForm

from accounts.models import Profile, User


class SignUpForm(UserCreationForm):
    email = forms.EmailField()

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.role = User.Role.MEMBER
        if commit:
            user.save()
            self.save_m2m()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("display_name", "biography")
        widgets = {"biography": forms.Textarea(attrs={"rows": 3})}
