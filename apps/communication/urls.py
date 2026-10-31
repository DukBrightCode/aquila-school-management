from django.urls import path
from . import views

app_name = 'communication'

urlpatterns = [
    path('', views.announcement_list, name='list'),
    path('create/', views.create_announcement, name='create'),
    path('<int:pk>/edit/', views.edit_announcement, name='edit'),
    path('<int:pk>/delete/', views.delete_announcement, name='delete'),
]