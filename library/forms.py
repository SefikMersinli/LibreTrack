from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm # En üste aldık
from .models import Profile, Comment

class UserRegisterForm(UserCreationForm):
    first_name = forms.CharField(label='Ad', max_length=30, widget=forms.TextInput(attrs={'placeholder': 'Adınızı giriniz'}))
    last_name = forms.CharField(label='Soyad', max_length=30, widget=forms.TextInput(attrs={'placeholder': 'Soyadınızı giriniz'}))
    email = forms.EmailField(label='E-posta', widget=forms.EmailInput(attrs={'placeholder': 'E-posta adresinizi giriniz'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control shadow-none'})

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()
    
    class Meta:
        model = User
        fields = ['username', 'email']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
            'content': ''
        }
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control rounded-4 shadow-sm bg-background text-white border-secondary',
                'placeholder': 'Kitap hakkında ne düşünüyorsun? Görüşlerini paylaş...',
                'rows': '3'
            }),
        }