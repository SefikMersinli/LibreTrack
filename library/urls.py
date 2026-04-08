from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    # Ana Fonksiyonlar
    path('search/', views.search_view, name='search_books'),
    path('add/', views.add_to_list, name='add_to_list'),
    path('library/', views.my_library_view, name='my_library'),
    path('delete/<int:pk>/', views.delete_book, name='delete_book'),
    path('book-detail/', views.book_detail_view, name='book_detail'),
    path('update-rating/', views.update_rating, name='update_rating'),
    
    # Kullanıcı Kayıt ve Giriş/Çıkış
    path('register/', views.register_view, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='library/login.html'), name='login'),
    # Logout sonrası ana sayfaya veya girişe yönlendirme için
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
    # Profil ve Güvenlik
    path('profile/', views.profile_view, name='profile'),
    path('password-change/', views.change_password, name='password_change'), 

    # Şifre Sıfırlama (E-posta ile)
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(template_name='library/password_reset_form.html'),
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='library/password_reset_done.html'),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name='library/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='library/password_reset_complete.html'),
         name='password_reset_complete'),

     path('newsletter-kayit/', views.newsletter_signup, name='newsletter_signup'),


     path('toggle-exchange/<int:pk>/', views.toggle_exchange, name='toggle_exchange'),
]