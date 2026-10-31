from django.conf import settings
from django.db import models
from apps.school_structure.models import ClassArm, Subject


class Teacher(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="teacher_profile",
    )
    staff_id = models.CharField(max_length=50, unique=True)
    subjects_taught = models.ManyToManyField(
        Subject, related_name="teachers", blank=True
    )
    class_arms_assigned = models.ManyToManyField(
        ClassArm, related_name="assigned_teachers", blank=True
    )
    date_employed = models.DateField()

    def __str__(self):
        return f"Teacher: {self.user.get_full_name() or self.user.username} ({self.staff_id})"


class NonTeachingStaff(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="non_teaching_profile",
    )
    staff_id = models.CharField(max_length=50, unique=True)
    designation = models.CharField(max_length=100)

    def __str__(self):
        return f"Staff: {self.user.get_full_name() or self.user.username} ({self.designation})"