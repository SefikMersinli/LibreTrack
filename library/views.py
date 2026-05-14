from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Book, UserBook, Profile, Comment, NewsletterUser, ChatMessage
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from .forms import UserUpdateForm, ProfileUpdateForm, CommentForm, UserRegisterForm
from django.core.paginator import Paginator
import os
import random
import requests
from requests.exceptions import SSLError, RequestException


def google_books_get(url, *, params=None, timeout=10):
    """Google Books isteğini daha sağlam yapar.
    Bazı okul/KYK ağlarında SSL sertifika hatası olursa ikinci denemede verify=False kullanır.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
        "Accept": "application/json",
    }
    try:
        return requests.get(url, params=params, timeout=timeout, headers=headers)
    except SSLError:
        # Okul ağlarında veya bazı bilgisayarlarda sertifika hatası olabiliyor.
        return requests.get(url, params=params, timeout=timeout, headers=headers, verify=False)


# ==============================================================================
# 1. YARDIMCI FONKSİYONLAR (API VE ANALİZ)
# ==============================================================================

def book_to_dict(book):
    """Veritabanındaki kitapları arama kartı formatına çevirir."""
    return {
        'id': f'local_{book.id}',
        'title': book.title,
        'author': book.author or 'Bilinmeyen Yazar',
        'image_url': book.image_url or '',
        'isbn': book.isbn or '',
        'categories': book.categories or 'Genel',
        'published_date': book.published_date or 'Bilinmiyor',
        'source': 'local',
    }


def get_local_books(query=None, limit=80):
    """Elle/admin panelinden eklenen kitapları veritabanından getirir."""
    qs = Book.objects.all().order_by('-id')
    if query:
        qs = qs.filter(Q(title__icontains=query) | Q(author__icontains=query) | Q(categories__icontains=query))
    return [book_to_dict(book) for book in qs[:limit]]


def merge_books(local_books, api_books):
    """Aynı başlık tekrar ederse yerel veritabanındaki kaydı önde tutar."""
    merged = []
    seen = set()
    for book in local_books + api_books:
        title = (book.get('title') or '').strip()
        if not title:
            continue
        key = title.lower()
        if key in seen:
            continue
        seen.add(key)
        merged.append(book)
    return merged


def _google_book_item_to_dict(item):
    """Google Books sonucunu arama kartı formatına çevirir."""
    vol = item.get('volumeInfo', {}) or {}
    image_url = vol.get('imageLinks', {}).get('thumbnail') or vol.get('imageLinks', {}).get('smallThumbnail') or ''
    identifiers = vol.get('industryIdentifiers') or []
    isbn = identifiers[0].get('identifier', '') if identifiers else ''

    return {
        'id': item.get('id'),
        'title': vol.get('title', 'Başlık Alınamadı'),
        'author': ", ".join(vol.get('authors', ['Bilinmeyen Yazar'])),
        'image_url': image_url.replace("http:", "https:"),
        'isbn': isbn,
        'categories': ", ".join(vol.get('categories', ['Genel'])),
        'published_date': vol.get('publishedDate', 'Bilinmiyor'),
        'source': 'api',
    }


def get_books_from_open_library(query, max_books=12):
    """Google Books quota dolarsa Open Library üzerinden yedek arama yapar."""
    query = (query or "").strip()
    if not query:
        return []

    try:
        r = requests.get(
            "https://openlibrary.org/search.json",
            params={"q": query, "limit": max_books},
            timeout=10,
            headers={"User-Agent": "LibreTrack/1.0"},
        )
        if r.status_code != 200:
            print(f"OPEN LIBRARY HATASI: HTTP {r.status_code} - {r.text[:200]}")
            return []

        data = r.json()
        books = []
        for doc in data.get("docs", [])[:max_books]:
            title = doc.get("title") or "Başlık Alınamadı"
            authors = doc.get("author_name") or ["Bilinmeyen Yazar"]
            isbn_list = doc.get("isbn") or []
            isbn = isbn_list[0] if isbn_list else ""
            cover_id = doc.get("cover_i")
            image_url = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else ""
            open_key = (doc.get("key") or title).replace("/", "_")

            books.append({
                'id': f"ol_{open_key}",
                'title': title,
                'author': ", ".join(authors[:3]),
                'image_url': image_url,
                'isbn': isbn,
                'categories': ", ".join((doc.get("subject") or ["Genel"])[:3]),
                'published_date': str(doc.get("first_publish_year") or "Bilinmiyor"),
                'source': 'openlibrary',
            })
        return books
    except RequestException as e:
        print(f"OPEN LIBRARY BAĞLANTI HATASI: {e}")
        return []
    except Exception as e:
        print(f"OPEN LIBRARY VERİ OKUMA HATASI: {e}")
        return []


def get_books_from_api(query, max_books=12):
    """Google Books API'den kitap çeker. Quota dolarsa Open Library yedeğine düşer."""
    query = (query or "").strip()
    if not query:
        return []

    books_list = []
    url = "https://www.googleapis.com/books/v1/volumes"

    try:
        params = {
            "q": query,
            "maxResults": min(max_books, 40),
            "printType": "books",
            "orderBy": "relevance",
        }

        # Eski sabit API key kaldırıldı. Kendi key'in varsa ortam değişkeni olarak kullanabilirsin.
        api_key = os.environ.get("GOOGLE_BOOKS_API_KEY", "").strip()
        if api_key:
            params["key"] = api_key

        r = google_books_get(url, params=params, timeout=10)

        if r.status_code == 429:
            print("GOOGLE BOOKS HATASI: Günlük kota doldu. Open Library yedeği kullanılıyor.")
            return get_books_from_open_library(query, max_books=max_books)

        if r.status_code != 200:
            print(f"GOOGLE BOOKS HATASI: HTTP {r.status_code} - {r.text[:200]}")
            return get_books_from_open_library(query, max_books=max_books)

        data = r.json()
        for item in data.get('items', [])[:max_books]:
            books_list.append(_google_book_item_to_dict(item))

        if books_list:
            return books_list[:max_books]

        return get_books_from_open_library(query, max_books=max_books)

    except RequestException as e:
        print(f"DIŞ BAĞLANTI HATASI: {e}")
        return get_books_from_open_library(query, max_books=max_books)
    except Exception as e:
        print(f"GOOGLE BOOKS VERİ OKUMA HATASI: {e}")
        return get_books_from_open_library(query, max_books=max_books)

# ==============================================================================
# 2. KEŞFET VE ARAMA SİSTEMİ
# ==============================================================================

def search_view(request):
    query = (request.GET.get('q') or '').strip()
    konular = ['dünya klasikleri', 'psikoloji', 'yazılım', 'bilim kurgu', 'felsefe', 'tarih', 'roman']
    
    # Boş Keşfet sayfasında her yenilemede internete çıkmasın; kota tüketmesin.
    # Kullanıcı gerçekten arama yazarsa internetten kitap çekilir.
    local_books = get_local_books(query if query else None)
    api_books = get_books_from_api(query, max_books=12) if query else []
    all_books = merge_books(local_books, api_books)
    
    # Sayfalama (Pagination) - Her sayfada 8 kitap
    paginator = Paginator(all_books, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # İstatistikler ve Sidebar Verileri
    real_comments = Comment.objects.all().order_by('-created_at')[:15]
    total_books_count = Book.objects.count()
    total_users_count = User.objects.count()
    reading_count = UserBook.objects.filter(status='reading').count()
    comment_count = Comment.objects.count()

    stats = {
        'toplam': total_books_count,
        'okuyan': reading_count,
        'yorum_sayisi': comment_count
    }

    context = {
        'books': page_obj,
        'query': query,
        'real_comments': real_comments,
        'stats': stats,
        'total_saved_books': total_books_count,
        'total_users': total_users_count
    }
    return render(request, 'library/search.html', context)

def book_detail_view(request):
    book_id = request.GET.get('id')
    if not book_id:
        return redirect('search_books')

    # Detay sayfasında yorum yapma
    if request.method == 'POST' and request.user.is_authenticated:
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.book_id = book_id
            comment.save()
            messages.success(request, "Yorumunuz başarıyla eklendi! 💬")
            return redirect(f'/book-detail/?id={book_id}')

    book_details = {}

    # Yerel/admin panelinden eklenen kitapların detay sayfası
    if book_id.startswith('local_'):
        local_pk = book_id.replace('local_', '', 1)
        book = get_object_or_404(Book, pk=local_pk)
        book_details = {
            'id': book_id,
            'title': book.title,
            'author': book.author or 'Bilinmeyen Yazar',
            'image_url': book.image_url or '',
            'description': 'Bu kitap veritabanına elle eklendiği için detay açıklaması bulunmuyor.',
            'categories': book.categories or 'Genel',
            'page_count': '---',
            'published_date': book.published_date or 'Bilinmiyor',
            'pdf_url': None,
            'isbn': book.isbn or '',
        }
    elif book_id.startswith('ol_'):
        book_details = {
            'id': book_id,
            'title': 'Open Library Kitabı',
            'author': 'Detay bilgisi arama sonucundan eklenebilir',
            'description': 'Bu kitap Google Books kotası dolduğu için Open Library yedeğinden listelendi. Detay sayfasında sınırlı bilgi gösterilir.',
            'image_url': 'https://via.placeholder.com/150x200.png?text=Kapak+Yok',
            'categories': 'Genel',
            'page_count': '---',
            'published_date': 'Bilinmiyor',
            'pdf_url': None,
            'isbn': '',
        }
    else:
        # Kitap Detaylarını API'den Çekme
        url = f"https://www.googleapis.com/books/v1/volumes/{book_id}"
        try:
            r = google_books_get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                vol = data.get('volumeInfo', {})
                access = data.get('accessInfo', {})
                book_details = {
                    'id': book_id,
                    'title': vol.get('title'),
                    'author': ", ".join(vol.get('authors', ['Bilinmeyen Yazar'])),
                    'image_url': vol.get('imageLinks', {}).get('thumbnail', '').replace("http:", "https:"),
                    'description': vol.get('description', 'Bu kitap için açıklama bulunmuyor.'),
                    'categories': ", ".join(vol.get('categories', ['Genel'])),
                    'page_count': vol.get('pageCount', '---'),
                    'published_date': vol.get('publishedDate', 'Bilinmiyor'),
                    'pdf_url': access.get('pdf', {}).get('downloadLink') or access.get('webReaderLink'),
                    'isbn': (vol.get('industryIdentifiers') or [{}])[0].get('identifier', ''),
                }
            else:
                raise Exception("API Detay Hatası")
        except Exception:
            book_details = {
                'id': book_id,
                'title': 'Kitap Bilgisi Çevrimdışı',
                'author': 'Sistem Çevrimdışı Modda',
                'description': 'Şu an internet üzerinden detaylı verilere ulaşılamıyor. Lütfen daha sonra tekrar deneyin.',
                'image_url': 'https://via.placeholder.com/150x200.png?text=Kapak+Yok',
                'categories': 'Genel',
                'page_count': '---',
                'published_date': 'Bilinmiyor',
                'pdf_url': None,
            }

    comments = Comment.objects.filter(book_id=book_id).order_by('-created_at')
    context = {
        'book': book_details, 
        'comments': comments, 
        'comment_form': CommentForm()
    }
    return render(request, 'library/book_detail.html', context)

# ==============================================================================
# 3. KÜTÜPHANE VE KULLANICI LİSTESİ
# ==============================================================================

@login_required
def my_library_view(request):
    user_books = UserBook.objects.filter(user=request.user).select_related('book').order_by('-updated_at')
    
    stats = {
        'toplam': user_books.count(),
        'okunuyor': user_books.filter(status='reading').count(),
        'bitti': user_books.filter(status='finished').count(),
        'plan': user_books.filter(status='plan').count()
    }
    
    return render(request, 'library/my_library.html', {
        'user_books': user_books,
        'stats': stats
    })

@login_required
def add_to_list(request):
    if request.method == "POST":
        title = request.POST.get('title', '').strip()
        author = request.POST.get('author', 'Bilinmeyen Yazar').strip()
        image_url = request.POST.get('image_url', '')
        status = request.POST.get('status', 'plan')
        isbn = request.POST.get('isbn', '')
        categories = request.POST.get('categories', '')
        published_date = request.POST.get('published_date', '')

        if not title:
            messages.error(request, "Kitap başlığı boş olamaz.")
            return redirect('search_books')
        
        # Kitabı başlığa göre bulur; yoksa oluşturur. Varsa eksik alanları tamamlar.
        book, book_created = Book.objects.get_or_create(
            title=title, 
            defaults={
                'author': author,
                'image_url': image_url,
                'isbn': isbn,
                'categories': categories,
                'published_date': published_date,
            }
        )
        changed = False
        for field, value in {
            'author': author,
            'image_url': image_url,
            'isbn': isbn,
            'categories': categories,
            'published_date': published_date,
        }.items():
            if value and not getattr(book, field):
                setattr(book, field, value)
                changed = True
        if changed:
            book.save()
        
        user_book, ub_created = UserBook.objects.get_or_create(
            user=request.user, 
            book=book, 
            defaults={'status': status}
        )
        if not ub_created and user_book.status != status:
            user_book.status = status
            user_book.save()
        
        # Ajax (Arka plan) isteği ise:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            if ub_created:
                return JsonResponse({'status': 'success', 'message': f'"{title}" listenize eklendi!'})
            return JsonResponse({'status': 'success', 'message': f'"{title}" durumu güncellendi!'})
        
        # Normal sayfa yenilemeli istek ise:
        if ub_created:
            messages.success(request, f'"{title}" kütüphanenize eklendi.')
        else:
            messages.success(request, f'"{title}" durumu güncellendi veya zaten kütüphanenizde mevcut.')
            
        return redirect('my_library')
    return redirect('search_books')

@login_required
def delete_book(request, pk):
    user_book = get_object_or_404(UserBook, pk=pk, user=request.user)
    book_title = user_book.book.title
    user_book.delete()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    messages.info(request, f'"{book_title}" listenizden silindi.')
    return redirect('my_library')

@login_required
def update_rating(request):
    if request.method == "POST":
        ub_id = request.POST.get('ubid')
        rating = request.POST.get('rating')
        user_book = get_object_or_404(UserBook, id=ub_id, user=request.user)
        user_book.rating = int(rating)
        user_book.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

# ==============================================================================
# 4. PROFİL VE HESAP İŞLEMLERİ
# ==============================================================================

def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Hoş geldin {user.first_name}! Kaydın başarıyla tamamlandı.")
            return redirect('search_books')
    else:
        form = UserRegisterForm()
    return render(request, 'library/register.html', {'form': form})

@login_required
def profile_view(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, "Profil bilgileriniz güncellendi!")
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    return render(request, 'library/profile.html', {
        'u_form': u_form,
        'p_form': p_form
    })

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Şifreniz başarıyla değiştirildi!")
            return redirect('profile')
        else:
            messages.error(request, "Lütfen hataları düzeltin.")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'library/password_change.html', {'form': form})

# ==============================================================================
# 5. DİĞER SOSYAL ÖZELLİKLER (CHAT, BÜLTEN)
# ==============================================================================

@login_required
def chat_view(request):
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            ChatMessage.objects.create(user=request.user, content=content)
            # AJAX isteği ise sayfayı yenileme, sadece 'başarılı' yanıtı dön
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success'})
            return redirect('chat')
            
    # Artık HTML şablonuna mesajları buradan yollamıyoruz, JS kendi çekecek
    return render(request, 'library/chat.html')

@login_required
def get_chat_messages(request):
    """Arka planda JS'in her 2 saniyede bir veri çektiği gizli köprü"""
    messages = ChatMessage.objects.all().order_by('created_at')
    msg_list = []
    
    for msg in messages:
        msg_list.append({
            'user': msg.user.username,
            'content': msg.content,
            'time': msg.created_at.strftime("%H:%M"),
            'is_me': msg.user == request.user
        })
        
    return JsonResponse({'messages': msg_list})

def newsletter_signup(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            if not NewsletterUser.objects.filter(email=email).exists():
                NewsletterUser.objects.create(email=email)
                messages.success(request, 'LibreTrack bültenine kayıt oldunuz! 📧')
            else:
                messages.info(request, 'Bu e-posta zaten listemizde kayıtlı.')
    return redirect('search_books')