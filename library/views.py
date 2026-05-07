from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from .models import Book, UserBook, Profile, Comment, NewsletterUser, ChatMessage
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from .forms import UserUpdateForm, ProfileUpdateForm, CommentForm, UserRegisterForm
from django.core.paginator import Paginator
import random
import requests

# ==============================================================================
# 1. YARDIMCI FONKSİYONLAR (API VE ANALİZ)
# ==============================================================================

def get_books_from_api(query, max_books=240): 
    """Google Books API'den döngü ile çok sayıda kitap çeker."""
    books_list = []
    
    try:
        # Google tek seferde maks 40 kitap verir. Biz de 40'ar 40'ar çekmek için döngü kuruyoruz.
        for start_index in range(0, max_books, 40):
            # API'ye 'startIndex' parametresini ekleyerek nereden başlayacağını söylüyoruz
            url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=40&startIndex={start_index}"
            
            # Okul internetini çok kitlememek için timeout süresini 3 saniyeye çektim
            r = requests.get(url, timeout=3)
            
            if r.status_code == 200:
                data = r.json()
                items = data.get('items', [])
                
                # Eğer o kelimeyle ilgili kitap bittiyse (örneğin 150. kitapta bittiyse) döngüyü kır
                if not items:
                    break
                    
                for item in items:
                    vol = item.get('volumeInfo', {})
                    books_list.append({
                        'id': item.get('id'),
                        'title': vol.get('title'),
                        'author': ", ".join(vol.get('authors', ['Bilinmeyen Yazar'])),
                        'image_url': vol.get('imageLinks', {}).get('thumbnail', '').replace("http:", "https:"),
                    })
            else:
                break # API'den anlık red yersek döngüyü durdur
                
        # Listede kaç kitap biriktiyse onu döndür (Maksimum bizim belirlediğimiz sayı kadar)
        return books_list[:max_books]
        
    except:
        # OKUL İNTERNETİ ERİŞİMİ ENGELLEDİĞİNDE VEYA ÇOK YAVAŞLADIĞINDA BURASI ÇALIŞIR
        print("DIŞ BAĞLANTI HATASI! Gümüşhane Üniversitesi Çevrimdışı Mod Aktif.")
        return [
            {'id': 'y1', 'title': '1984', 'author': 'George Orwell', 'image_url': '/static/images/1984.jpg'},
            {'id': 'y2', 'title': 'Nutuk', 'author': 'M. Kemal Atatürk', 'image_url': '/static/images/atam.jpg'},
            {'id': 'y3', 'title': 'Sefiller', 'author': 'Victor Hugo', 'image_url': '/static/images/sefiller.jpg'},
            {'id': 'y4', 'title': 'Suç ve Ceza', 'author': 'Dostoyevski', 'image_url': '/static/images/suc_ve_ceza.jpg'},
            {'id': 'y5', 'title': 'Simyacı', 'author': 'Paulo Coelho', 'image_url': '/static/images/simyaci.jpg'},
            {'id': 'y6', 'title': 'Kürk Mantolu Madonna', 'author': 'Sabahattin Ali', 'image_url': '/static/images/kurk_mantolu_madonna.jpg'},
            {'id': 'y7', 'title': 'Yabancı', 'author': 'Albert Camus', 'image_url': '/static/images/yabanci.jpg'},
            {'id': 'y8', 'title': 'Karamazov Kardeşler', 'author': 'Dostoyevski', 'image_url': '/static/images/karamazov.jpg'},
            {'id': 'y9', 'title': 'Savaş ve Barış', 'author': 'Lev Tolstoy', 'image_url': '/static/images/sefiller.jpg'},
            {'id': 'y10', 'title': 'Fahrenheit 451', 'author': 'Ray Bradbury', 'image_url': '/static/images/1984.jpg'},
        ]

# ==============================================================================
# 2. KEŞFET VE ARAMA SİSTEMİ
# ==============================================================================

def search_view(request):
    query = request.GET.get('q')
    konular = ['dünya klasikleri', 'psikoloji', 'yazılım', 'bilim kurgu', 'felsefe', 'tarih', 'roman']
    
    search_query = query if query else random.choice(konular)
    all_books = get_books_from_api(search_query)
    
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
        'query': query if query else '',
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

    # Kitap Detaylarını API'den Çekme
    url = f"https://www.googleapis.com/books/v1/volumes/{book_id}"
    book_details = {}
    try:
        r = requests.get(url, timeout=5)
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
            }
        else:
            raise Exception("API Detay Hatası")
    except:
        # OKUL İNTERNETİ BAĞLANTIYI KESTİĞİNDE ÇALIŞACAK KISIM
        book_details = {
            'id': book_id,
            'title': 'Kitap Bilgisi Çevrimdışı',
            'author': 'Sistem Çevrimdışı Modda',
            'description': 'Şu an okul interneti üzerinden detaylı verilere ulaşılamıyor. Lütfen daha sonra tekrar deneyin.',
            # SENİN FOTOĞRAFIN YERİNE BOŞ KAPAK GÖRSELİ:
            'image_url': 'https://via.placeholder.com/150x200.png?text=Kapak+Yok'
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
        
        # 1. KORUMA KALKANI: Kitabı sadece 'title' (başlık) ile arıyoruz. 
        # Yazar adı API'den farklı gelse bile yeni kitap üretmeyecek.
        book, book_created = Book.objects.get_or_create(
            title=title, 
            defaults={'author': author, 'image_url': image_url}
        )
        
        # 2. KORUMA KALKANI: Kullanıcıda bu kitap zaten var mı kontrolü (update_or_create yerine get_or_create)
        user_book, ub_created = UserBook.objects.get_or_create(
            user=request.user, 
            book=book, 
            defaults={'status': status}
        )
        
        # Ajax (Arka plan) isteği ise:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            if ub_created:
                return JsonResponse({'status': 'success', 'message': f'"{title}" listenize eklendi!'})
            else:
                return JsonResponse({'status': 'info', 'message': f'"{title}" zaten kütüphanenizde mevcut!'})
        
        # Normal sayfa yenilemeli istek ise:
        if ub_created:
            messages.success(request, f'"{title}" kütüphanenize eklendi.')
        else:
            messages.info(request, f'"{title}" zaten kütüphanenizde bulunuyor.')
            
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