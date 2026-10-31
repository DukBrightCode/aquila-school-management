from django import forms
from django.contrib.auth import get_user_model
from apps.school_structure.models import ClassArm
from .models import Student

User = get_user_model()


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            "first_name",
            "last_name",
            "admission_number",
            "date_of_birth",
            "gender",
            "current_class_level",
            "current_class_arm",
            "guardian_name",
            "guardian_phone",
            "guardian_email",
            "address",
            "photo",
            "date_enrolled",
        ]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "date_enrolled": forms.DateInput(attrs={"type": "date"}),
            "address": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "current_class_level" in self.data:
            try:
                class_level_id = int(self.data.get("current_class_level"))
                self.fields["current_class_arm"].queryset = (
                    ClassArm.objects.filter(class_level_id=class_level_id)
                )
            except (ValueError, TypeError):
                pass
        elif self.instance and self.instance.pk and self.instance.current_class_level:
            self.fields["current_class_arm"].queryset = (
                self.instance.current_class_level.arms.all()
            )

    def save(self, commit=True):
        student = super().save(commit=False)

        if commit:
            student.save()
        return student