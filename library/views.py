from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from .models import Book, UserBook, Profile, Comment
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from .forms import UserUpdateForm, ProfileUpdateForm, CommentForm
from django.core.paginator import Paginator
import random
import requests
import time

# --- YARDIMCI FONKSİYON: GOOGLE BOOKS API ---
def search_books(query):
    if not query:
        return []
    
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=40&langRestrict=tr"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            books_data = []
            for item in data.get('items', []):
                volume_info = item.get('volumeInfo', {})
                book = {
                    'id': item.get('id'),
                    'title': volume_info.get('title', 'Başlıksız Kitap'),
                    'author': ", ".join(volume_info.get('authors', ['Bilinmeyen Yazar'])),
                    'image_url': volume_info.get('imageLinks', {}).get('thumbnail', '').replace("http:", "https:"),
                    'description': volume_info.get('description', 'Açıklama yok.'),
                }
                books_data.append(book)
            return books_data
    except:
        pass
    return []

# --- ANA ARAMA VE GİRİŞ SAYFASI ---
def search_view(request):
    query = request.GET.get('q')
    konular = ['dünya klasikleri', 'bilim kurgu', 'psikoloji', 'tarih', 'yazılım']
    
    if query:
        all_books = search_books(query)
    else:
        rastgele_konu = random.choice(konular)
        all_books = search_books(rastgele_konu)
    
    # SAYFALAMA (PAGINATION) - Her sayfada 8 kitap
    paginator = Paginator(all_books, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'books': page_obj,  # Template'de {% for book in books %} bunu kullanacak
        'query': query if query else '',
        'total_saved_books': Book.objects.count(),
        'total_users': User.objects.count(),
        'search_time': 0.15
    }
    return render(request, 'library/search.html', context)

# --- KİTAP EKLEME ---
@login_required
def add_to_list(request):
    if request.method == "POST":
        title = request.POST.get('title', '').strip()
        author = request.POST.get('author', 'Bilinmeyen Yazar').strip()
        image_url = request.POST.get('image_url', '')
        status = request.POST.get('status')

        book, _ = Book.objects.get_or_create(
            title=title,
            author=author,
            defaults={'image_url': image_url}
        )

        UserBook.objects.update_or_create(
            user=request.user, 
            book=book, 
            defaults={'status': status}
        )

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'message': 'Kitap eklendi!'})
        
        return redirect('my_library')
    return redirect('search_books')

# --- KİTAPLIK ---
@login_required
def my_library_view(request):
    user_books = UserBook.objects.filter(user=request.user).select_related('book').order_by('-id')
    stats = {
        'toplam': user_books.count(),
        'okunuyor': user_books.filter(status='reading').count(),
        'bitti': user_books.filter(status='finished').count(),
        'plan': user_books.filter(status='plan').count(),
    }
    return render(request, 'library/my_library.html', {'user_books': user_books, 'stats': stats})

# --- SİLME ---
@login_required
def delete_book(request, pk):
    ub = get_object_or_404(UserBook, pk=pk, user=request.user)
    ub.delete()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    messages.info(request, "Kitap kaldırıldı.")
    return redirect('my_library')

# --- PUANLAMA ---
@login_required
def update_rating(request):
    if request.method == "POST":
        ub_id = request.POST.get('ubid')
        rating = request.POST.get('rating')
        ub = get_object_or_404(UserBook, id=ub_id, user=request.user)
        ub.rating = int(rating)
        ub.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

# --- KAYIT ---
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('search_books')
    else: form = UserCreationForm()
    return render(request, 'library/register.html', {'form': form})

# --- PROFİL ---
@login_required
def profile_view(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save(); p_form.save()
            messages.success(request, "Profilin güncellendi!")
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)
    return render(request, 'library/profile.html', {'u_form': u_form, 'p_form': p_form})

# --- ŞİFRE DEĞİŞTİRME ---
@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Şifren başarıyla güncellendi!")
            return redirect('profile')
    else: form = PasswordChangeForm(request.user)
    return render(request, 'library/change_password.html', {'form': form})

# --- KİTAP DETAY ---
def book_detail_view(request):
    book_id = request.GET.get('id')
    comments = Comment.objects.filter(book_id=book_id).order_by('-created_at')
    book_details = {}
    if book_id:
        url = f"https://www.googleapis.com/books/v1/volumes/{book_id}"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                vol = r.json().get('volumeInfo', {})
                book_details = {
                    'title': vol.get('title'),
                    'author': ", ".join(vol.get('authors', [])),
                    'image_url': vol.get('imageLinks', {}).get('thumbnail', '').replace("http:", "https:"),
                    'description': vol.get('description', 'Açıklama yok.'),
                    'id': book_id
                }
        except: pass
    form = CommentForm()
    return render(request, 'library/book_detail.html', {'book': book_details, 'comments': comments, 'comment_form': form})