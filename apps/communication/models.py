from django.conf import settings
from django.db import models
from django.utils import timezone

class Announcement(models.Model):
    ROLE_CHOICES = [
        ('ALL', 'Everyone (All Users)'),
        ('STAFF', 'All Staff (Teachers & Librarians)'),
        ('TEACHERS', 'Teachers Only'),
        ('LIBRARIANS', 'Librarians Only'),
        ('STUDENTS', 'Students Only'),
    ]
    
    title = models.CharField(max_length=200)
    body = models.TextField()
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    target_role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='ALL')
    is_pinned = models.BooleanField(default=False, help_text="Pin to the top of the announcement list.")
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Optional: Automatically hide after this date.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_expired(self):
        if self.expires_at and timezone.now() > self.expires_at:
            return True
        return False

    def __str__(self):
        return self.title