import os
from pathlib import Path

# Ana dizin ayarı
BASE_DIR = Path(__file__).resolve().parent.parent

# GÜVENLİK AYARLARI
DEBUG = True
SECRET_KEY = 'django-insecure-%vxs8%gya5m_)2gpyhqa$p@k6%y&dn0@ny^x5yyri@zh#434to'
ALLOWED_HOSTS = ['*']

# UYGULAMALAR
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Senin Uygulaman
    'library',
    
    # Tasarım Paketleri
    'crispy_forms',
    'crispy_bootstrap5',
]

# ARA KATMANLAR
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

# ŞABLONLAR (HTML Dosyaları)
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
            ],
        },
    },
]

# VERİTABANI
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# DİL VE ZAMAN (Türkiye Ayarları)
LANGUAGE_CODE = 'tr-tr'
TIME_ZONE = 'Europe/Istanbul'
USE_I18N = True
USE_TZ = True

# --- ÖNEMLİ: STATİK VE MEDYA DOSYALARI ---
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# --- ÖNEMLİ: GİRİŞ / ÇIKIŞ YÖNLENDİRMELERİ ---
# Giriş başarılı olunca Keşfet (search_books) sayfasına git
LOGIN_REDIRECT_URL = 'search_books' 
LOGOUT_REDIRECT_URL = 'login'
LOGIN_URL = 'login'

# CRISPY FORMS AYARLARI
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# E-POSTA AYARLARI (Şifre Sıfırlama İçin)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'sefik.mersinli@gmail.com'
EMAIL_HOST_PASSWORD = 'cgyj huzr bdlt jxtu'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'