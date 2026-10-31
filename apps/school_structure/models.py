from django.db import models


class AcademicSession(models.Model):
    name = models.CharField(max_length=20, unique=True, help_text="e.g. 2025/2026")
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_current:
            AcademicSession.objects.filter(is_current=True).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)


class Term(models.Model):
    class TermName(models.TextChoices):
        FIRST = "FIRST", "First Term"
        SECOND = "SECOND", "Second Term"
        THIRD = "THIRD", "Third Term"

    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE, related_name="terms")
    name = models.CharField(max_length=10, choices=TermName.choices)
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["session", "name"]
        unique_together = ("session", "name")

    def __str__(self):
        return f"{self.get_name_display()} ({self.session.name})"

    def save(self, *args, **kwargs):
        if self.is_current:
            Term.objects.filter(is_current=True).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)


class ClassLevel(models.Model):
    class Category(models.TextChoices):
        PRIMARY = "PRIMARY", "Primary"
        JSS = "JSS", "Junior Secondary School"
        SSS = "SSS", "Senior Secondary School"

    name = models.CharField(max_length=50, unique=True, help_text="e.g. Primary 1, JSS1, SS3")
    category = models.CharField(max_length=10, choices=Category.choices)
    order = models.PositiveIntegerField(unique=True, help_text="Sorting order (e.g. 1 for Primary 1)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name


class ClassArm(models.Model):
    class_level = models.ForeignKey(ClassLevel, on_delete=models.CASCADE, related_name="arms")
    name = models.CharField(max_length=10, help_text="e.g. A, B, C")
    class_teacher = models.ForeignKey(
        "staff.Teacher",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="class_arms_led"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["class_level__order", "name"]
        unique_together = ("class_level", "name")

    def __str__(self):
        return f"{self.class_level.name} {self.name}"


class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="e.g. Mathematics, English Language")
    code = models.CharField(max_length=20, unique=True, help_text="e.g. MATH, ENG")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Standard Many-to-Many relationship (Django automatically manages the join table)
    class_arms = models.ManyToManyField(
        ClassArm,
        related_name="subjects",
        blank=True
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"
class ClassSubject(models.Model):
    class_level = models.ForeignKey(ClassLevel, on_delete=models.CASCADE, related_name="class_subjects")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="subject_classes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["class_level__order", "subject__name"]
        unique_together = ("class_level", "subject")

    def __str__(self):
        return f"{self.subject.name} - {self.class_level.name}"