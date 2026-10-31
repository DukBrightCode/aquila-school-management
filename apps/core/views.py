from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone

from .models import (
    Event, Gallery, News, SiteSetting,
    SchoolStat, Feature, Achievement, Testimonial,
    HeroSlide, QuickLink, DownloadFile, FAQ, KeyDate,
)


def home_view(request):
    context = {
        'stats': SchoolStat.objects.filter(is_active=True),
        'slides': HeroSlide.objects.filter(is_active=True),
        'features': Feature.objects.filter(is_active=True),
        'events': Event.objects.filter(is_published=True, date__gte=timezone.now())
                       .order_by('-is_featured', 'date')[:3],
        'achievements': Achievement.objects.filter(is_published=True)[:3],
        'testimonials': Testimonial.objects.filter(is_published=True)[:3],
        'news': News.objects.filter(is_published=True)[:3],
        'gallery': Gallery.objects.filter(is_published=True)[:8],
        'quick_links': QuickLink.objects.filter(is_active=True),
        'key_dates': KeyDate.objects.filter(is_active=True, date__gte=timezone.localdate())[:6],
        'downloads': DownloadFile.objects.filter(is_published=True),
        'faqs': FAQ.objects.filter(is_published=True),
    }
    return render(request, 'home.html', context)


def about_view(request):
    return render(request, 'core/about.html')


def academics_view(request):
    return render(request, 'core/academics.html')


def admissions_view(request):
    return render(request, 'core/admissions.html')


def news_events_view(request):
    featured_event = Event.objects.filter(is_featured=True, is_published=True).first()
    upcoming_events = Event.objects.filter(
        is_published=True,
        date__gte=timezone.now()
    ).order_by('date')[:4]
    recent_news = News.objects.filter(is_published=True).order_by('-published_date')[:3]

    context = {
        'featured_event': featured_event,
        'upcoming_events': upcoming_events,
        'recent_news': recent_news,
    }
    return render(request, 'core/news_events.html', context)


def gallery_view(request):
    gallery_images = Gallery.objects.all()
    categories = Gallery.CATEGORY_CHOICES

    context = {
        'gallery_images': gallery_images,
        'categories': categories,
    }
    return render(request, 'core/gallery.html', context)


def contact_view(request):
    return render(request, 'core/contact.html')


@staff_member_required
def settings_view(request):
    if request.method == 'POST':
        school_name = request.POST.get('school_name', '').strip()
        school_motto = request.POST.get('school_motto', '').strip()

        if school_name:
            site = SiteSetting.load()
            site.school_name = school_name
            site.school_motto = school_motto
            site.save()
            messages.success(request, 'Settings updated successfully!')
            return redirect('core:settings')
        messages.error(request, 'School name cannot be empty.')

    return render(request, 'core/settings.html')