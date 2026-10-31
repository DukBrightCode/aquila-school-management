from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from apps.accounts.permissions import role_required
from .forms import AnnouncementForm
from .models import Announcement


@login_required
def announcement_list(request):
    user = request.user
    now = timezone.now()
    
    # Exclude expired announcements
    qs = Announcement.objects.exclude(expires_at__lt=now)

    if user.role == 'ADMIN':
        announcements = qs.order_by('-is_pinned', '-created_at')
    elif user.role == 'TEACHER':
        announcements = qs.filter(target_role__in=['ALL', 'STAFF', 'TEACHERS']).order_by('-is_pinned', '-created_at')
    elif user.role == 'STUDENT':
        announcements = qs.filter(target_role__in=['ALL', 'STUDENTS']).order_by('-is_pinned', '-created_at')
    elif user.is_librarian():
        announcements = qs.filter(target_role__in=['ALL', 'STAFF', 'LIBRARIANS']).order_by('-is_pinned', '-created_at')
    else:
        announcements = Announcement.objects.none()

    return render(request, 'communication/announcement_list.html', {'announcements': announcements})


@role_required("ADMIN")
def create_announcement(request):
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.posted_by = request.user
            announcement.save()
            messages.success(request, "Announcement published successfully!")
            return redirect('communication:list')
    else:
        form = AnnouncementForm()
    return render(request, 'communication/announcement_form.html', {'form': form, 'action': 'Create'})


@role_required("ADMIN")
def edit_announcement(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, instance=announcement)
        if form.is_valid():
            form.save()
            messages.success(request, "Announcement updated successfully!")
            return redirect('communication:list')
    else:
        form = AnnouncementForm(instance=announcement)
    return render(request, 'communication/announcement_form.html', {'form': form, 'action': 'Edit'})


@role_required("ADMIN")
def delete_announcement(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    if request.method == 'POST':
        announcement.delete()
        messages.success(request, "Announcement deleted successfully.")
        return redirect('communication:list')
    return render(request, 'communication/announcement_confirm_delete.html', {'announcement': announcement})