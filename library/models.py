from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Book(models.Model):
    isbn = models.CharField(max_length=20, null=True, blank=True) 
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    image_url = models.URLField(max_length=500, null=True, blank=True)
    
    # EKSİK OLAN VE HATA VEREN ALANLAR BURADA:
    published_date = models.CharField(max_length=50, null=True, blank=True)
    categories = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.title

# 2. KULLANICI KİTAP LİSTESİ (ARA TABLO)
class UserBook(models.Model):
    STATUS_CHOICES = [
        ('plan', 'Okuyacağım'),
        ('reading', 'Okuyorum'),
        ('finished', 'Bitirdim'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='plan')
    rating = models.IntegerField(default=0) # Yıldız puanı
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) # Analizler için son güncelleme tarihi

    class Meta:
        unique_together = ('user', 'book') # Bir kitap listeye sadece bir kez eklenir

    def __str__(self):
        return f"{self.user.username} - {self.book.title} ({self.status})"
    

    is_exchangeable = models.BooleanField(default=False, verbose_name="Takasa Açık mı?")
    # İsteğe bağlı: takas açıklaması
    exchange_note = models.CharField(max_length=255, blank=True, null=True)

# 3. YORUM MODELİ (Google Books ID Odaklı)
class Comment(models.Model):
    # Google Books ID kullanmak daha mantıklı çünkü bazen yerel DB'de kitap olmayabilir
    book_id = models.CharField(max_length=100) 
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(verbose_name="Yorumunuz")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.book_id}"

# 4. PROFİL MODELİ
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='default.jpg', upload_to='profile_pics')
    bio = models.TextField(max_length=500, blank=True)

    def __str__(self):
        return f'{self.user.username} Profili'

# 5. OTOMATİK PROFİL SİNYALLERİ
@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    instance.profile.save()


# library/models.py
class NewsletterUser(models.Model):
    email = models.EmailField(unique=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __clstr__(self):
        return f'{self.user.username}: {self.content[:20]}'