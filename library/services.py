import requests

# API Anahtarını buraya sabitledik
GOOGLE_API_KEY = "AIzaSyBV5ibi93-FpqoC-wsgHO7co3l26vjmZI8"

def search_books(query):
    # maxResults=12 tasarımımızdaki 4'lü ızgara (grid) yapısına tam oturuyor
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=12&key={GOOGLE_API_KEY}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        # verify=False bazen okul ağlarında (KYK/Üniversite) SSL hatalarını aşmanı sağlar
        response = requests.get(url, timeout=10, verify=False, headers=headers)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Bağlantı Hatası: {e}")
        return []

    books_data = []
    items = data.get('items', [])
    
    for item in items:
        vol = item.get('volumeInfo', {})
        if not vol: continue

        # Görsel Kontrolü ve HTTPS zorunluluğu
        image_links = vol.get('imageLinks', {})
        thumb = image_links.get('thumbnail') or image_links.get('smallThumbnail')
        
        if thumb:
            thumb = thumb.replace("http://", "https://")
        else:
            # Senin seçtiğin Unsplash görseli harika, aynen kalsın
            thumb = "https://images.unsplash.com/photo-1543002588-bfa74002ed7e?q=80&w=500"

        # ISBN Alımı (Daha güvenli hale getirildi)
        identifiers = vol.get('industryIdentifiers', [])
        isbn = identifiers[0].get('identifier', '0000000000000') if identifiers else '0000000000000'

        books_data.append({
            'id': item.get('id'), # Google'ın kendi ID'si (Detay sayfası için şart)
            'title': vol.get('title', 'Başlık Alınamadı'),
            'author': ", ".join(vol.get('authors', ['Bilinmeyen Yazar'])),
            'image_url': thumb,
            'isbn': isbn,
            'categories': ", ".join(vol.get('categories', ['Genel'])), # Kategori bilgisini de ekledim
            'page_count': vol.get('pageCount', 0), # Sayfa sayısını detay için ekledim
            'published_date': vol.get('publishedDate', 'Tarih Bilgisi Yok')
        })
    
    return books_data