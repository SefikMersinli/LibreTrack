from django.contrib import admin
from .models import Book, UserBook, ChatMessage

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

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    # 'timestamp' yerine 'created_at' yazdık
    list_display = ('user', 'content', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('content', 'user__username')
    ordering = ('-created_at',)