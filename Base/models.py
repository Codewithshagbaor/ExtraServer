from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.contrib.auth import get_user_model
User = get_user_model()
import uuid
# models.py
import random

class Video(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    video_file = models.FileField(upload_to='videos', blank=True)
    view_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    slug = models.SlugField(unique=True, max_length=255, blank=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('video_detail', args=[str(self.slug)])



class VideoView(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    user_ip = models.GenericIPAddressField()
    viewed_at = models.DateTimeField(auto_now_add=True)
    device_os = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)

class Comment(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    username = models.CharField(max_length=100)
    time = models.DateTimeField(auto_now_add=True)
    comment_text = models.TextField()

    def __str__(self):
        return f"Comment by {self.username} on {self.video.title} at {self.time}"

def random_default_picture():
    default_pictures = ['/static/images/1.jpg', '/static/images/2.jpg', '/static/images/3.jpg', '/static/images/4.jpg', '/static/images/5.jpg', '/static/images/6.jpg', '/static/images/7.jpg', '/static/images/8.jpg', '/static/images/9.jpg', '/static/images/10.jpg', '/static/images/11.jpg', '/static/images/12.jpg']
    return random.choice(default_pictures)
class Profile(models.Model):
    user = models.OneToOneField(User, related_name="user_profile", on_delete=models.CASCADE)
    last_login = models.DateTimeField(blank=True, null=True)
    unique_id = models.CharField(max_length=8, default=str(uuid.uuid4())[:8])
    active = models.BooleanField(default=False)
    profile_pic = profile_pic = models.ImageField(upload_to='user_profile_pics', default=random.choice(['/static/images/1.jpg', '/static/images/2.jpg', '/static/images/3.jpg', '/static/images/4.jpg', '/static/images/5.jpg', '/static/images/6.jpg', '/static/images/7.jpg', '/static/images/8.jpg', '/static/images/9.jpg', '/static/images/10.jpg', '/static/images/11.jpg', '/static/images/12.jpg']))
    def __str__(self):
        return self.user.first_name if self.user.first_name else self.user.username

class Contact(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    subject = models.CharField(max_length=150)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name