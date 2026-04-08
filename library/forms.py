from django import forms
from django.contrib.auth.models import User
from .models import Profile, Comment

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()
    
    class Meta:
        model = User
        fields = ['username', 'email']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Form alanlarına otomatik olarak modern tasarım sınıflarımızı ekleyelim
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control shadow-none'})

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image']

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        labels = {
            'content': '' # Etiketi gizleyelim ki placeholder daha şık dursun
        }
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control rounded-4 shadow-sm bg-background text-white border-secondary',
                'placeholder': 'Kitap hakkında ne düşünüyorsun? Görüşlerini paylaş...',
                'rows': '3'
            }),
        }