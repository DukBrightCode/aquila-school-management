from django.urls import path
from .views import home_view, about_view, academics_view, admissions_view, news_events_view, gallery_view, contact_view, settings_view

app_name = 'core'

urlpatterns = [
    path('', home_view, name='home'),
    path('about/', about_view, name='about'),
    path('academics/', academics_view, name='academics'),
    path('admissions/', admissions_view, name='admissions'),
    path('news-events/', news_events_view, name='news_events'),
    path('gallery/', gallery_view, name='gallery'),
    path('contact/', contact_view, name='contact'),
    path('settings/', settings_view, name='settings'),
]