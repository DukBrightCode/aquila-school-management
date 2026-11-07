from django.contrib import admin
from .models import AcademicSession, Term, ClassLevel, ClassArm, Subject, ClassSubject


@admin.register(AcademicSession)
class AcademicSessionAdmin(admin.ModelAdmin):
    list_display = ("name", "is_current", "created_at")
    list_filter = ("is_current",)
    search_fields = ("name",)


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ("name", "session", "is_current", "created_at")
    list_filter = ("is_current", "session", "name")
    search_fields = ("session__name",)


@admin.register(ClassLevel)
class ClassLevelAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "order")
    list_filter = ("category",)
    search_fields = ("name",)
    ordering = ("order",)


@admin.register(ClassArm)
class ClassArmAdmin(admin.ModelAdmin):
    list_display = ("__str__", "class_level", "name", "class_teacher_names")
    list_filter = ("class_level__category", "class_level")
    search_fields = (
        "class_level__name", "name",
        "class_teachers__user__username",
        "class_teachers__user__first_name",
        "class_teachers__user__last_name",
    )
    filter_horizontal = ("class_teachers",)
    exclude = ("class_teacher",)   # old single field, hidden during the transition

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("class_teachers__user")

    @admin.display(description="Class teachers")
    def class_teacher_names(self, obj):
        names = [t.user.get_full_name() or t.user.username for t in obj.class_teachers.all()]
        return ", ".join(names) or "-"


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "created_at")
    search_fields = ("name", "code")


@admin.register(ClassSubject)
class ClassSubjectAdmin(admin.ModelAdmin):
    list_display = ("class_level", "subject", "created_at")
    list_filter = ("class_level__category", "class_level", "subject")
    search_fields = ("class_level__name", "subject__name", "subject__code")