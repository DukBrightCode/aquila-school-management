from django.urls import path
from . import views

app_name = "staff"

urlpatterns = [
    path("", views.StaffListView.as_view(), name="list"),
    path("teacher/<int:pk>/", views.TeacherDetailView.as_view(), name="teacher_detail"),
    path("teacher/create/", views.TeacherCreateView.as_view(), name="teacher_create"),
    path("teacher/<int:pk>/update/", views.TeacherUpdateView.as_view(), name="teacher_update"),
    path("non-teaching/create/", views.NonTeachingStaffCreateView.as_view(), name="non_teaching_create"),
    path("non-teaching/<int:pk>/update/", views.NonTeachingStaffUpdateView.as_view(), name="non_teaching_update"),
    path("non-teaching/", views.non_teaching_staff_list, name="non_teaching_list"),
]