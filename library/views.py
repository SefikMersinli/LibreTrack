from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from .models import Book, UserBook, Profile, Comment, NewsletterUser
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from .forms import UserUpdateForm, ProfileUpdateForm, CommentForm
from django.core.paginator import Paginator
import random
import requests

# 1. YARDIMCI FONKSİYON: Google Books API'den kitapları çeker
def get_books_from_api(query):
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=20"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            items = r.json().get('items', [])
            books_list = []
            for item in items:
                vol = item.get('volumeInfo', {})
                books_list.append({
                    'id': item.get('id'),
                    'title': vol.get('title'),
                    'author': ", ".join(vol.get('authors', ['Bilinmeyen Yazar'])),
                    'image_url': vol.get('imageLinks', {}).get('thumbnail', '').replace("http:", "https:"),
                })
            return books_list
    except:
        return []
    return []

# 2. ANA KEŞFET SAYFASI (Arama, Takas Sistemi, Newsletter ve Yorumlar)
def search_view(request):
    query = request.GET.get('q')
    konular = ['dünya klasikleri', 'psikoloji', 'yazılım', 'bilim kurgu', 'felsefe']
    
    # Kitapları getir
    search_query = query if query else random.choice(konular)
    all_books = get_books_from_api(search_query)
    
    # Sayfalama
    paginator = Paginator(all_books, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # İstatistikler ve Yorumlar
    real_comments = Comment.objects.all().order_by('-created_at')[:3]
    stats = {
        'toplam': Book.objects.count(),
        'okuyan': UserBook.objects.filter(status='reading').count(),
        'yorum_sayisi': Comment.objects.count()
    }

    # TAKAS SİSTEMİ: Giriş yapmayan kullanıcılar için hata koruması
    if request.user.is_authenticated:
        exchange_books = UserBook.objects.filter(is_exchangeable=True).exclude(user=request.user).select_related('book', 'user')[:8]
    else:
        exchange_books = UserBook.objects.filter(is_exchangeable=True).select_related('book', 'user')[:8]

    context = {
        'books': page_obj,
        'query': query if query else '',
        'real_comments': real_comments,
        'stats': stats,
        'exchange_books': exchange_books,
        'total_saved_books': stats['toplam'],
        'total_users': User.objects.count()
    }
    return render(request, 'library/search.html', context)

# 3. NEWSLETTER KAYDI
def newsletter_signup(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            if not NewsletterUser.objects.filter(email=email).exists():
                NewsletterUser.objects.create(email=email)
                messages.success(request, 'Bültene başarıyla kayıt oldunuz! 📧')
            else:
                messages.info(request, 'Bu e-posta zaten kayıtlı.')
    return redirect('search_books')

# 4. KİTAP DETAY VE YORUM SİSTEMİ
def book_detail_view(request):
    book_id = request.GET.get('id')
    if not book_id:
        return redirect('search_books')

    if request.method == 'POST' and request.user.is_authenticated:
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.book_id = book_id
            comment.save()
            messages.success(request, "Yorumun paylaşıldı! 💬")
          # 4. KİTAP DETAY VE YORUM SİSTEMİ
def book_detail_view(request):
    book_id = request.GET.get('id')
    if not book_id:
        return redirect('search_books')

    if request.method == 'POST' and request.user.is_authenticated:
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.book_id = book_id
            comment.save()
            messages.success(request, "Yorumun paylaşıldı! 💬")
            return redirect(f'/book-detail/?id={book_id}')

    url = f"https://www.googleapis.com/books/v1/volumes/{book_id}"
    book_details = {}
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            vol = data.get('volumeInfo', {})
            access = data.get('accessInfo', {}) # PDF ve indirme bilgileri burada
            
            book_details = {
                'id': book_id,
                'title': vol.get('title'),
                'author': ", ".join(vol.get('authors', ['Bilinmeyen Yazar'])),
                'image_url': vol.get('imageLinks', {}).get('thumbnail', '').replace("http:", "https:"),
                'description': vol.get('description', 'Açıklama mevcut değil.'),
                'categories': ", ".join(vol.get('categories', ['Edebiyat'])),
                'page_count': vol.get('pageCount', '---'),
                'published_date': vol.get('publishedDate', 'Belirtilmemiş'),
                # PDF linkini sözlüğün içine, virgülle ayırarak yerleştirdik:
                'pdf_url': access.get('pdf', {}).get('downloadLink') or access.get('webReaderLink'),
            }
    except:
        pass

    comments = Comment.objects.filter(book_id=book_id).order_by('-created_at')
    context = {'book': book_details, 'comments': comments, 'comment_form': CommentForm()}
    return render(request, 'library/book_detail.html', context)
# 5. TAKAS DURUMUNU DEĞİŞTİR (AJAX)
@login_required
def toggle_exchange(request, pk):
    user_book = get_object_or_404(UserBook, pk=pk, user=request.user)
    user_book.is_exchangeable = not user_book.is_exchangeable
    user_book.save()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success', 'is_exchangeable': user_book.is_exchangeable})
    return redirect('my_library')


# --- DİĞER STANDART GÖRÜNÜMLER ---
@login_required
def add_to_list(request):
    if request.method == "POST":
        title = request.POST.get('title', '').strip()
        author = request.POST.get('author', 'Bilinmeyen Yazar').strip()
        image_url = request.POST.get('image_url', '')
        status = request.POST.get('status', 'plan')
        book, _ = Book.objects.get_or_create(title=title, author=author, defaults={'image_url': image_url})
        UserBook.objects.update_or_create(user=request.user, book=book, defaults={'status': status})
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'message': f'"{title}" listenize eklendi!'})
        return redirect('my_library')
    return redirect('search_books')

@login_required
def my_library_view(request):
    user_books = UserBook.objects.filter(user=request.user).select_related('book').order_by('-updated_at')
    stats = {
        'toplam': user_books.count(),
        'okunuyor': user_books.filter(status='reading').count(),
        'bitti': user_books.filter(status='finished').count(),
        'plan': user_books.filter(status='plan').count()
    }
    return render(request, 'library/my_library.html', {'user_books': user_books, 'stats': stats})

@login_required
def delete_book(request, pk):
    ub = get_object_or_404(UserBook, pk=pk, user=request.user)
    ub.delete()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest': return JsonResponse({'status': 'success'})
    return redirect('my_library')

@login_required
def update_rating(request):
    if request.method == "POST":
        ub_id = request.POST.get('ubid')
        rating = request.POST.get('rating')
        ub = get_object_or_404(UserBook, id=ub_id, user=request.user)
        ub.rating = int(rating); ub.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(); login(request, user)
            messages.success(request, f"Hoş geldin {user.username}!"); return redirect('search_books')
    else: form = UserCreationForm()
    return render(request, 'library/register.html', {'form': form})

@login_required
def profile_view(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save(); p_form.save(); messages.success(request, "Profil güncellendi!"); return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)
    return render(request, 'library/profile.html', {'u_form': u_form, 'p_form': p_form})

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save(); update_session_auth_hash(request, user)
            messages.success(request, "Şifre güncellendi!"); return redirect('profile')
    else: form = PasswordChangeForm(request.user)
    return render(request, 'library/password_change.html', {'form': form})