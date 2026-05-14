# Eski sürümlerde Google Books API key burada sabit duruyordu.
# Güvenlik ve kota sorunu yaşamamak için kaldırıldı.
# Kitap arama işlemleri artık library/views.py içindeki get_books_from_api fonksiyonuyla yapılıyor.

from .views import get_books_from_api


def search_books(query):
    return get_books_from_api(query, max_books=12)
