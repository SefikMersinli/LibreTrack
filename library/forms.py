from django import forms
from django.contrib.auth.models import User
from .models import Profile
from .models import Profile, Comment

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()
    class Meta:
        model = User
        fields = ['username', 'email']

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image']

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control rounded-4 shadow-sm',
                'placeholder': 'Kitap hakkında ne düşünüyorsun? Görüşlerini paylaş...',
                'rows': '3'
            }),
        }