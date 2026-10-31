from django.urls import path
from . import views

app_name = "attendance"

urlpatterns = [
    path("mark/", views.MarkAttendanceView.as_view(), name="mark_attendance"),
    path("summary/", views.AttendanceSummaryView.as_view(), name="summary"),
    path("records/", views.attendance_records_list, name="records_list"),
]