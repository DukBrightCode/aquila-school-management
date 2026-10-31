from django.contrib import admin
from .models import NonTeachingStaff, Teacher


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("staff_id", "user", "date_employed")
    search_fields = ("staff_id", "user__first_name", "user__last_name")
    filter_horizontal = ("subjects_taught", "class_arms_assigned")


@admin.register(NonTeachingStaff)
class NonTeachingStaffAdmin(admin.ModelAdmin):
    list_display = ("staff_id", "user", "designation")
    search_fields = ("staff_id", "user__first_name", "user__last_name", "designation")