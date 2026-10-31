from django.urls import path
from . import views

app_name = "timetable"

urlpatterns = [
    path("", views.class_timetable, name="class_timetable"),
    path("edit/<int:class_arm_id>/", views.edit_timetable, name="edit_timetable"),
    path("periods/", views.period_list, name="period_list"),
]