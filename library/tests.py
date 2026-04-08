from django.test import TestCase
from django.contrib.auth.models import User
from .models import Book, UserBook

class LibraryModelTest(TestCase):
    def setUp(self):
        # Test için geçici veriler oluşturalım
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.book = Book.objects.create(
            title='Test Kitabı', 
            author='Şefik Mersinli', 
            isbn='123456789'
        )

    def test_book_creation(self):
        # Kitap modelinin doğru kaydedildiğini kontrol edelim
        self.assertEqual(self.book.title, 'Test Kitabı')
        self.assertEqual(str(self.book), 'Test Kitabı')

    def test_user_book_status(self):
        # Kullanıcının listesine kitap ekleme durumunu kontrol edelim
        user_book = UserBook.objects.create(
            user=self.user, 
            book=self.book, 
            status='reading'
        )
        self.assertEqual(user_book.status, 'reading')
        self.assertTrue(UserBook.objects.filter(user=self.user).exists())