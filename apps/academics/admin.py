from django.contrib import admin

from .models import (
    AssessmentType, GradingScale, Score, PredefinedRemark, StudentReportRemark,
    Skill, StudentSkillRating, ClassSubjectTeacher, ResultRelease
)


@admin.register(AssessmentType)
class AssessmentTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "term", "max_score", "weight_percentage", "is_active")
    list_filter = ("term", "is_active")
    search_fields = ("name",)


@admin.register(GradingScale)
class GradingScaleAdmin(admin.ModelAdmin):
    list_display = ("grade_letter", "min_score", "max_score", "remark")
    ordering = ("-min_score",)


@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ("student", "subject", "class_arm", "term", "assessment_type", "exam_type", "score_value", "entered_by")
    list_filter = ("term", "subject", "class_arm", "exam_type")
    search_fields = ("student__admission_number", "student__user__first_name", "student__user__last_name")


@admin.register(PredefinedRemark)
class PredefinedRemarkAdmin(admin.ModelAdmin):
    list_display = ('text', 'type')
    list_filter = ('type',)
    search_fields = ('text',)


@admin.register(StudentReportRemark)
class StudentReportRemarkAdmin(admin.ModelAdmin):
    list_display = ('student', 'term', 'date_printed')
    search_fields = ('student__user__first_name', 'student__user__last_name', 'student__admission_number')


# ---------- NEW: Skills and Behaviour ----------

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "display_order", "created_by")
    list_editable = ("is_active", "display_order")
    list_filter = ("is_active",)
    search_fields = ("name",)
    ordering = ("display_order", "name")

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(StudentSkillRating)
class StudentSkillRatingAdmin(admin.ModelAdmin):
    list_display = ("student", "term", "skill", "rating", "rated_by")
    list_filter = ("term", "skill", "rating")
    search_fields = ("student__user__first_name", "student__user__last_name",
                     "student__admission_number")
    
@admin.register(ClassSubjectTeacher)
class ClassSubjectTeacherAdmin(admin.ModelAdmin):
    list_display = ("class_arm", "subject", "teacher", "teacher_name")
    list_filter = ("class_arm",)
    search_fields = ("subject__name", "teacher_name")
    
@admin.register(ResultRelease)
class ResultReleaseAdmin(admin.ModelAdmin):
    list_display = ("class_arm", "term", "exam_type", "is_released", "released_at")
    list_filter = ("term", "exam_type", "is_released")