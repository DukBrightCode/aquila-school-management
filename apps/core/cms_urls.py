# Save as: apps/core/cms_urls.py
from django.urls import path
from . import cms_views as v

app_name = 'website'

urlpatterns = [
    path('', v.home, name='home'),
    path('settings/', v.site_settings, name='settings'),
    path('<slug:key>/', v.item_list, name='list'),
    path('<slug:key>/add/', v.item_form, name='add'),
    path('<slug:key>/<int:pk>/edit/', v.item_form, name='edit'),
    path('<slug:key>/<int:pk>/delete/', v.item_delete, name='delete'),
]