from django.conf import settings
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone


class AssessmentType(models.Model):
    """
    Admin-configurable assessment component tied to a specific Term.
    Allows arbitrary structures (e.g., Test + Project + Exam) without hardcoded rules.
    """
    term = models.ForeignKey(
        "school_structure.Term",
        on_delete=models.CASCADE,
        related_name="assessment_types"
    )
    name = models.CharField(max_length=100)
    max_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Maximum raw score achievable in this assessment component."
    )
    weight_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.01")),
            MaxValueValidator(Decimal("100.00"))
        ],
        help_text="Percentage weight of this assessment towards the 100% term total."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Designates whether this component is currently active for grade calculation."
    )
    #class AssessmentType: ADD this field
    exam_type = models.CharField(
        max_length=20,
        choices=[("MID_TERM", "Mid Term"), ("FULL_TERM", "Full Term")],
        default="FULL_TERM",
        help_text="Which exam type this component belongs to.",
    )
    
    class Meta:
        ordering = ["id"]
        unique_together = ("term", "exam_type", "name")

    def __str__(self):
        return f"{self.term} - {self.name} ({self.weight_percentage}%)"


class GradingScale(models.Model):
    """
    Defines score ranges and matching letter grades and remarks.
    """
    min_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00")), MaxValueValidator(Decimal("100.00"))]
    )
    #class GradingScale: ADD this field
    exam_type = models.CharField(
        max_length=20,
        choices=[("MID_TERM", "Mid Term"), ("FULL_TERM", "Full Term")],
        default="FULL_TERM",
        help_text="Which exam type this grade range applies to.",
    )
    max_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00")), MaxValueValidator(Decimal("100.00"))]
    )
    grade_letter = models.CharField(max_length=5)  # e.g., A1, B2, C4, F9
    remark = models.CharField(max_length=50)       # e.g., Excellent, Credit, Fail
    
    class Meta:
        ordering = ["-min_score"]

    def clean(self):
        super().clean()
        if self.min_score is not None and self.max_score is not None:
            if self.min_score > self.max_score:
                raise ValidationError({"min_score": "min_score cannot be greater than max_score."})

    def __str__(self):
        return f"{self.grade_letter} ({self.min_score} - {self.max_score}): {self.remark}"


class Score(models.Model):
    """
    Stores raw assessment entries per student, subject, term, and assessment component.
    """
    class ExamType(models.TextChoices):
        MID_TERM = "MID_TERM", "Mid Term"
        FULL_TERM = "FULL_TERM", "Full Term"

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="scores"
    )
    subject = models.ForeignKey(
        "school_structure.Subject",
        on_delete=models.CASCADE,
        related_name="scores"
    )
    class_arm = models.ForeignKey(
        "school_structure.ClassArm",
        on_delete=models.CASCADE,
        related_name="scores"
    )
    term = models.ForeignKey(
        "school_structure.Term",
        on_delete=models.CASCADE,
        related_name="scores"
    )
    assessment_type = models.ForeignKey(
        AssessmentType,
        on_delete=models.CASCADE,
        related_name="scores"
    )
    exam_type = models.CharField(
        max_length=20,
        choices=ExamType.choices,
        default=ExamType.FULL_TERM,
        help_text="Type of exam: Mid Term or Full Term"
    )
    score_value = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Numeric raw score earned by the student."
    )
    entered_by = models.ForeignKey(
        "staff.Teacher",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="entered_scores"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("student", "subject", "term", "assessment_type", "exam_type")

    def clean(self):
        super().clean()
        if self.assessment_type_id and self.score_value is not None:
            if self.score_value > self.assessment_type.max_score:
                raise ValidationError({
                    "score_value": f"Score ({self.score_value}) exceeds maximum allowed score "
                                   f"({self.assessment_type.max_score}) for {self.assessment_type.name}."
                })
            #Mine Testing
            if self.assessment_type_id and self.assessment_type.exam_type != self.exam_type:
                raise ValidationError({
                    "assessment_type": "This component belongs to a different exam type."
                })        
    

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student} - {self.subject} ({self.assessment_type.name} - {self.get_exam_type_display()}): {self.score_value}"


class PredefinedRemark(models.Model):
    REMARK_TYPES = (
        ('TEACHER', 'Teacher Remark'),
        ('PRINCIPAL', 'Principal Remark'),
    )
    type = models.CharField(max_length=20, choices=REMARK_TYPES)
    text = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f"[{self.get_type_display()}] {self.text}"


class StudentReportRemark(models.Model):
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="report_remarks"
    )
    term = models.ForeignKey(
        "school_structure.Term",
        on_delete=models.CASCADE,
        related_name="report_remarks"
    )
    teacher_remark = models.TextField(blank=True, null=True)
    principal_remark = models.TextField(blank=True, null=True)
    teacher_signature = models.ImageField(upload_to="signatures/teachers/", blank=True, null=True)
    principal_signature = models.ImageField(upload_to="signatures/principals/", blank=True, null=True)
    date_printed = models.DateField(default=timezone.now)

    class Meta:
        unique_together = ("student", "term")

    def __str__(self):
        return f"Remarks for {self.student} - {self.term}"
    
class Skill(models.Model):
    """Master list. Teachers can add to it; nothing is hard-coded."""
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)        # hide instead of delete
    display_order = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name
    

class StudentSkillRating(models.Model):
    student = models.ForeignKey("students.Student", on_delete=models.CASCADE,
                                related_name="skill_ratings")
    term = models.ForeignKey("school_structure.Term", on_delete=models.CASCADE,
                             related_name="skill_ratings")
    skill = models.ForeignKey(Skill, on_delete=models.PROTECT)   # old report cards stay intact
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)])
    rated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+")

    class Meta:
        unique_together = ("student", "term", "skill")
        ordering = ["skill__display_order", "skill__name"]

    def __str__(self):
        return f"{self.student} - {self.skill}: {self.rating}"

# ---- 1) apps/academics/models.py : ADD this model at the bottom ----

class ClassSubjectTeacher(models.Model):
    """Who teaches a subject in a class arm (shown on the report card)."""

    class_arm = models.ForeignKey(
        "school_structure.ClassArm",
        on_delete=models.CASCADE,
        related_name="subject_teachers",
    )
    subject = models.ForeignKey(
        "school_structure.Subject",
        on_delete=models.CASCADE,
        related_name="class_teachers",
    )
    # Optional link to a Teacher record, OR just type the name below.
    teacher = models.ForeignKey(
        "staff.Teacher",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    teacher_name = models.CharField(
        max_length=150,
        blank=True,
        help_text="Used when the subject teacher has no Teacher record.",
    )

    class Meta:
        unique_together = ("class_arm", "subject")

    @property
    def display_name(self):
        if self.teacher_id:
            user = self.teacher.user
            return user.get_full_name() or user.username
        return self.teacher_name

    def __str__(self):
        return f"{self.class_arm} - {self.subject}: {self.display_name or '-'}"


class ResultRelease(models.Model):
    """Admin switch: may class teachers see/download results for this class, term and exam?"""
 
    term = models.ForeignKey(
        "school_structure.Term", on_delete=models.CASCADE, related_name="result_releases"
    )
    class_arm = models.ForeignKey(
        "school_structure.ClassArm", on_delete=models.CASCADE, related_name="result_releases"
    )
    exam_type = models.CharField(
        max_length=20,
        choices=[("MID_TERM", "Mid Term"), ("FULL_TERM", "Full Term")],
    )
    is_released = models.BooleanField(default=False)
    released_at = models.DateTimeField(null=True, blank=True)
    released_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
 
    class Meta:
        unique_together = ("term", "class_arm", "exam_type")
 
    def __str__(self):
        state = "released" if self.is_released else "not released"
        return f"{self.class_arm} - {self.term} - {self.get_exam_type_display()}: {state}"

