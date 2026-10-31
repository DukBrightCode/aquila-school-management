from django.conf import settings
from django.db import models
from apps.school_structure.models import ClassArm
from apps.staff.models import Teacher
from apps.students.models import Student


class DailyAttendance(models.Model):
    class_arm = models.ForeignKey(
        ClassArm, on_delete=models.CASCADE, related_name="daily_attendances"
    )
    date = models.DateField()
    marked_by = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="marked_attendances",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("class_arm", "date")
        verbose_name = "Daily Attendance"
        verbose_name_plural = "Daily Attendances"

    def __str__(self):
        return f"{self.class_arm} - {self.date}"


class AttendanceRecord(models.Model):
    STATUS_CHOICES = (
        ("PRESENT", "Present"),
        ("ABSENT", "Absent"),
        ("LATE", "Late"),
    )

    daily_attendance = models.ForeignKey(
        DailyAttendance, on_delete=models.CASCADE, related_name="records"
    )
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="attendance_records"
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PRESENT")

    class Meta:
        unique_together = ("daily_attendance", "student")
        verbose_name = "Attendance Record"
        verbose_name_plural = "Attendance Records"

    def __str__(self):
        return f"{self.student} - {self.daily_attendance.date}: {self.status}"