from django.contrib import admin
from .models import Video, VideoView, Comment,Profile, Contact


admin.site.register(Profile)
@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ["title",]}
    list_display = ('title', 'view_count', 'created_at', 'updated_at')  # Add relevant fields to the list view

@admin.register(VideoView)
class VideoViewAdmin(admin.ModelAdmin):
    list_display = ('video', 'user_ip', 'viewed_at')  # Customize as needed

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('username', 'video', 'time', 'comment_text')
    list_filter = ('video', 'time')
    search_fields = ('username', 'comment_text')

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email','subject', 'message')
    search_fields = ('name', 'email')