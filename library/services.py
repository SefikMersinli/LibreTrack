import requests

# API Anahtarını buraya sabitledik
GOOGLE_API_KEY = "AIzaSyBV5ibi93-FpqoC-wsgHO7co3l26vjmZI8"

def search_books(query):
    # Anahtar, URL'nin sonuna otomatik olarak ekleniyor
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=12&key={GOOGLE_API_KEY}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(url, timeout=10, verify=False, headers=headers)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Bağlantı Hatası: {e}")
        return []

    books_data = []
    items = data.get('items', [])
    
    for item in items:
        vol = item.get('volumeInfo') or item.get('volume_info') or {}
        
        if not vol:
            continue

        image_links = vol.get('imageLinks', {})
        thumb = image_links.get('thumbnail') or image_links.get('smallThumbnail')
        
        if thumb:
            thumb = thumb.replace("http://", "https://")
        else:
            thumb = "https://images.unsplash.com/photo-1543002588-bfa74002ed7e?q=80&w=500"

        books_data.append({
            'id': item.get('id'),
            'title': vol.get('title', 'Başlık Alınamadı'),
            'author': ", ".join(vol.get('authors', ['Bilinmeyen Yazar'])),
            'image_url': thumb,
            'isbn': vol.get('industryIdentifiers', [{}])[0].get('identifier', '0000000000000')
        })
    
    print(f"ARAMA SONUCU ({query}): {len(books_data)} kitap bulundu.")
    return books_data