from django import forms

from social.models import Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ("body", "image")
        widgets = {"body": forms.Textarea(attrs={"rows": 3})}

    def clean_body(self):
        return self.cleaned_data["body"].strip()

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("body") and not cleaned_data.get("image"):
            raise forms.ValidationError("Add text, an image, or both to your post.")
        return cleaned_data
