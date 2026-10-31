from django.contrib import admin
from .models import AttendanceRecord, DailyAttendance


class AttendanceRecordInline(admin.TabularInline):
    model = AttendanceRecord
    extra = 0


@admin.register(DailyAttendance)
class DailyAttendanceAdmin(admin.ModelAdmin):
    list_display = ("class_arm", "date", "marked_by", "created_at")
    list_filter = ("class_arm", "date")
    inlines = [AttendanceRecordInline]


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ("student", "daily_attendance", "status")
    list_filter = ("status", "daily_attendance__date", "daily_attendance__class_arm")
    search_fields = ("student__user__first_name", "student__user__last_name", "student__admission_number")