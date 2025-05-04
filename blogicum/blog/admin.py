from django.contrib import admin

from .models import Location, Category, Post, Comment
# Register your models here.

admin.site.register(Location)
admin.site.register(Category)
admin.site.register(Post)
admin.site.register(Comment)
