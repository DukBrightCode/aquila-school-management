from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        TEACHER = "TEACHER", "Teacher"
        STUDENT = "STUDENT", "Student"
        LIBRARIAN = "LIBRARIAN", "Librarian"  # <-- Added Librarian role

    role = models.CharField(
        max_length=20,  # Increased from 10 to fit 'LIBRARIAN' safely
        choices=Role.choices,
        default=Role.ADMIN,
    )

    def is_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    def is_teacher(self):
        return self.role == self.Role.TEACHER

    def is_student(self):
        return self.role == self.Role.STUDENT

    def is_librarian(self):
        return self.role == self.Role.LIBRARIAN or self.is_admin()  # Admins can also access library functions

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"