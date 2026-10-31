from django.db import models


class Period(models.Model):
    name = models.CharField(max_length=50)  # e.g., "Period 1", "Morning Registration"
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ["start_time"]
        verbose_name = "Period"
        verbose_name_plural = "Periods"

    def __str__(self):
        return f"{self.name} ({self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')})"


class TimetableSlot(models.Model):
    DAY_CHOICES = [
        ("MONDAY", "Monday"),
        ("TUESDAY", "Tuesday"),
        ("WEDNESDAY", "Wednesday"),
        ("THURSDAY", "Thursday"),
        ("FRIDAY", "Friday"),
    ]

    class_arm = models.ForeignKey(
        "school_structure.ClassArm",
        on_delete=models.CASCADE,
        related_name="timetable_slots",
    )
    subject = models.ForeignKey(
        "school_structure.Subject",
        on_delete=models.CASCADE,
        related_name="timetable_slots",
    )
    teacher = models.ForeignKey(
        "staff.Teacher",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="timetable_slots",
    )
    day_of_week = models.CharField(max_length=10, choices=DAY_CHOICES)
    period = models.ForeignKey(
        Period,
        on_delete=models.CASCADE,
        related_name="timetable_slots",
    )

    class Meta:
        unique_together = ("class_arm", "day_of_week", "period")
        verbose_name = "Timetable Slot"
        verbose_name_plural = "Timetable Slots"

    def __str__(self):
        return f"{self.class_arm} | {self.day_of_week} | {self.period.name}: {self.subject.name}"