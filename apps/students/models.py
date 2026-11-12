from django.conf import settings
from django.db import models
from django.db import transaction
from django.utils import timezone
import re
import secrets
import string
from apps.school_structure.models import ClassArm, ClassLevel


class AdmissionCounter(models.Model):
    class_level = models.ForeignKey(
        ClassLevel, on_delete=models.CASCADE, related_name="admission_counters"
    )
    year = models.IntegerField()
    last_number = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("class_level", "year")
        verbose_name = "Admission Counter"
        verbose_name_plural = "Admission Counters"

    def __str__(self):
        return f"{self.class_level.name} - {self.year}: {self.last_number}"


class Student(models.Model):
    GENDER_CHOICES = (
        ("M", "Male"),
        ("F", "Female"),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_profile",
    )
    admission_number = models.CharField(max_length=50, unique=True, blank=True)
    first_name = models.CharField(max_length=100, default="")
    last_name = models.CharField(max_length=100, default="")
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    current_class_level = models.ForeignKey(
        ClassLevel, on_delete=models.PROTECT, related_name="students"
    )
    current_class_arm = models.ForeignKey(
        ClassArm,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
    )
    
    # Inside class Student, next to current_class_arm:
    stream = models.ForeignKey(
        "school_structure.Stream",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="students",
    )
    guardian_name = models.CharField(max_length=255, blank=True)
    guardian_phone = models.CharField(max_length=20, blank=True)
    guardian_email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    photo = models.ImageField(upload_to="student_photos/", blank=True, null=True)
    date_enrolled = models.DateField(default=timezone.localdate)

    class Meta:
        ordering = ["last_name", "first_name"]

    @property
    def full_name(self):
        name = f"{self.first_name} {self.last_name}".strip()
        return name if name else self.admission_number

    @property
    def is_profile_complete(self):
        return bool(
            self.date_of_birth
            and self.guardian_name
            and self.guardian_phone
        )

    def __str__(self):
        return f"{self.full_name} ({self.admission_number})"

    def save(self, *args, **kwargs):
        if not self.admission_number:
            self.admission_number = self.generate_admission_number()
        super().save(*args, **kwargs)

    def generate_admission_number(self):
        year = timezone.now().year
        level_code = re.sub(r'[^a-zA-Z0-9]', '', self.current_class_level.name).upper()

        with transaction.atomic():
            counter, created = AdmissionCounter.objects.select_for_update().get_or_create(
                class_level=self.current_class_level,
                year=year,
                defaults={"last_number": 0}
            )

            candidate_number = f"{level_code}-{year}-{counter.last_number + 1:03d}"

            # Skip if this number already exists (shouldn't happen, but safety check)
            while Student.objects.filter(admission_number=candidate_number).exists():
                counter.last_number += 1
                candidate_number = f"{level_code}-{year}-{counter.last_number + 1:03d}"

            counter.last_number += 1
            counter.save()

            return candidate_number

    def create_login_account(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()

        if self.user:
            raise ValueError("Student already has a login account")

        username = self.admission_number
        if User.objects.filter(username=username).exists():
            raise ValueError(f"Username '{username}' is already taken")

        # Generate random 10-character password
        alphabet = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(secrets.choice(alphabet) for _ in range(10))

        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=self.first_name,
            last_name=self.last_name,
            role=User.Role.STUDENT,
        )

        self.user = user
        self.save(update_fields=['user'])

        return username, password