from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple

from .models import (
    AcademicSession, Term, ClassLevel, ClassArm, Stream, Subject, ClassSubject,
)


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
    list_display = ("__str__", "class_level", "name", "class_teacher_names", "show_position")
    list_filter = ("class_level__category", "class_level", "show_position")
    search_fields = (
        "class_level__name", "name",
        "class_teachers__user__username",
        "class_teachers__user__first_name",
        "class_teachers__user__last_name",
    )
    filter_horizontal = ("class_teachers",)   # two-box picker: add as many class teachers as needed
    exclude = ("class_teacher",)              # old single field: hidden during the transition
    actions = ["turn_position_on", "turn_position_off"]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("class_teachers__user")

    @admin.display(description="Class teachers")
    def class_teacher_names(self, obj):
        names = [t.user.get_full_name() or t.user.username for t in obj.class_teachers.all()]
        return ", ".join(names) or "-"

    @admin.action(description="Show class position on report cards for the selected classes")
    def turn_position_on(self, request, queryset):
        updated = queryset.update(show_position=True)
        self.message_user(request, f"Class position is now shown for {updated} class(es).")

    @admin.action(description="Hide class position on report cards for the selected classes")
    def turn_position_off(self, request, queryset):
        updated = queryset.update(show_position=False)
        self.message_user(request, f"Class position is now hidden for {updated} class(es).")


class StreamAdminForm(forms.ModelForm):
    """Lets the admin pick all the subjects of a stream on ONE page."""

    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.all().order_by("name"),
        required=False,
        widget=FilteredSelectMultiple("subjects", is_stacked=False),
        help_text="Move the subjects taken by students of this stream to the right-hand box. "
                  "A subject that is in no stream (English, Mathematics...) is taken by everyone.",
    )

    class Meta:
        model = Stream
        fields = ("name", "order")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["subjects"].initial = self.instance.subjects.all()


@admin.register(Stream)
class StreamAdmin(admin.ModelAdmin):
    form = StreamAdminForm
    list_display = ("name", "order", "subject_names")
    list_editable = ("order",)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("subjects")

    @admin.display(description="Subjects")
    def subject_names(self, obj):
        return ", ".join(s.name for s in obj.subjects.all()) or "-"

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.subjects.set(form.cleaned_data["subjects"])


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "stream_names", "created_at")
    list_filter = ("streams",)
    search_fields = ("name", "code")
    filter_horizontal = ("streams",)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("streams")

    @admin.display(description="Streams")
    def stream_names(self, obj):
        names = [s.name for s in obj.streams.all()]
        return ", ".join(names) if names else "Everyone (core)"


@admin.register(ClassSubject)
class ClassSubjectAdmin(admin.ModelAdmin):
    list_display = ("class_level", "subject", "created_at")
    list_filter = ("class_level__category", "class_level", "subject")
    search_fields = ("class_level__name", "subject__name", "subject__code")