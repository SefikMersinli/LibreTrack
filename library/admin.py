from django.contrib import admin
from .models import Book, UserBook


admin.site.register(Book)
admin.site.register(UserBook)

# Register your models here.
