from django.contrib import admin
from .models import Period, TimetableSlot


@admin.register(Period)
class PeriodAdmin(admin.ModelAdmin):
    list_display = ("name", "start_time", "end_time")
    ordering = ("start_time",)


@admin.register(TimetableSlot)
class TimetableSlotAdmin(admin.ModelAdmin):
    list_display = ("class_arm", "day_of_week", "period", "subject", "teacher")
    list_filter = ("class_arm", "day_of_week", "subject")
    search_fields = (
        "class_arm__name",
        "subject__name",
        "teacher__user__first_name",
        "teacher__user__last_name",
    )