from django.contrib import admin
from .models import Book, UserBook

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    # Panelde hangi sütunlar görünsün?
    list_display = ('title', 'author', 'published_date', 'categories')
    # Sağ tarafta hangi kriterlere göre filtreleme yapılsın?
    list_filter = ('categories', 'published_date')
    # Arama çubuğu neleri arasın?
    search_fields = ('title', 'author')
    # Sayfa başına kaç kayıt gelsin?
    list_per_page = 20

@admin.register(UserBook)
class UserBookAdmin(admin.ModelAdmin):
    # Kullanıcının hangi kitabı hangi durumda okuduğunu görelim
    list_display = ('user', 'book', 'status', 'rating', 'updated_at')
    # Okuma durumuna ve puana göre filtreleyelim
    list_filter = ('status', 'rating')
    # Kullanıcı adına veya kitap adına göre arayalım
    search_fields = ('user__username', 'book__title')
    # Admin panelinden direkt durum değiştirilebilsin
    list_editable = ('status',)

# Not: admin.site.register(Book) satırlarını silebilirsin, 
# yukarıdaki @admin.register dekoratörü zaten bu işi yapıyor.