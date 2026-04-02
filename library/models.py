from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Book(models.Model):
    # unique=True kısmını siliyoruz veya null=True ekliyoruz
    isbn = models.CharField(max_length=20, null=True, blank=True) 
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    image_url = models.URLField(max_length=500, null=True, blank=True)

    def __str__(self):
        return self.title

class UserBook(models.Model):
    STATUS_CHOICES = [
        ('plan', 'Okuyacağım'),
        ('reading', 'Okuyorum'),
        ('finished', 'Bitirdim'),
    ]
    # YENİ EKLENEN SATIR BURASI:
    rating = models.IntegerField(default=0) 

    def __str__(self):
        return f"{self.user.username} - {self.book.title} ({self.status})"
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='plan')
    added_at = models.DateTimeField(auto_now_add=True) # Ne zaman eklendiğini takip etmek profesyoneldir.

    class Meta:
        # Bir kullanıcı aynı kitabı listesine sadece bir kez ekleyebilir.
        unique_together = ('user', 'book')


class Comment(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.book.title}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='default.jpg', upload_to='profile_pics')
    bio = models.TextField(max_length=500, blank=True)

    def __str__(self):
        return f'{self.user.username} Profili'

# Kullanıcı oluştuğunda otomatik profil oluşturma sinyalleri
@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    instance.profile.save()


class Comment(models.Model):
    book_id = models.CharField(max_length=100) # Google Books ID'si
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(verbose_name="Yorumunuz")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at'] # En yeni yorum en üstte görünsün

    def __str__(self):
        return f"{self.user.username} - {self.book_id}"