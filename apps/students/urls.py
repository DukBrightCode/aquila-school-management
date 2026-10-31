from django.urls import path
from . import views

app_name = "students"

urlpatterns = [
    path("", views.StudentListView.as_view(), name="list"),
    path("<int:pk>/", views.StudentDetailView.as_view(), name="detail"),
    path("create/", views.StudentCreateView.as_view(), name="create"),
    path("<int:pk>/update/", views.StudentUpdateView.as_view(), name="update"),
    path("<int:pk>/promote/", views.promote_student, name="promote"),
]