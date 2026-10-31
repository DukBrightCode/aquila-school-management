from django.shortcuts import render
from django.utils import timezone

from apps.core.models import (
    Event, News, Gallery, SchoolStat, Feature, Achievement, Testimonial,
)


def home_view(request):
    """
    Renders the public home page. This route is accessible to all users
    without requiring authentication.
    """
    context = {
        'stats': SchoolStat.objects.filter(is_active=True),
        'features': Feature.objects.filter(is_active=True),
        'events': Event.objects.filter(is_published=True, date__gte=timezone.now())
                       .order_by('-is_featured', 'date')[:3],
        'achievements': Achievement.objects.filter(is_published=True)[:3],
        'testimonials': Testimonial.objects.filter(is_published=True)[:3],
        'news': News.objects.filter(is_published=True)[:3],
        'gallery': Gallery.objects.filter(is_published=True)[:8],
    }
    return render(request, 'home.html', context)


def page_not_found(request, exception):
    """Custom 404 handler rendering a responsive Tailwind error template."""
    return render(request, 'errors/404.html', status=404)


def server_error(request):
    """Custom 500 handler rendering a responsive Tailwind server error template."""
    return render(request, 'errors/500.html', status=500)