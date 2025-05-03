from django import forms
from django.contrib.auth import get_user_model
from .models import Post, Comment
from django.utils import timezone

User = get_user_model()


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = (
            'title', 'image', 'text', 'pub_date',
            'location', 'category', 'is_published'
        )

        widgets = {
            'pub_date': forms.DateTimeInput(attrs={'type': 'datetime'})
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)

        widgets = {
            'text': forms.Textarea(attrs={'rows': 3}),
        }


class EditProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')
