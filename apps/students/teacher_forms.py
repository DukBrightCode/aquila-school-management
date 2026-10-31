from django import forms
from apps.school_structure.models import ClassArm
from .models import Student


class TeacherStudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ["first_name", "last_name", "gender"]
        widgets = {
            "gender": forms.Select(attrs={"class": "border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"}),
            "first_name": forms.TextInput(attrs={"class": "border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"}),
            "last_name": forms.TextInput(attrs={"class": "border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"}),
        }

    def __init__(self, *args, **kwargs):
        arms = kwargs.pop('arms', None)
        super().__init__(*args, **kwargs)

        if arms:
            self.fields['class_arm'] = forms.ModelChoiceField(
                queryset=arms,
                label="Class Arm",
                empty_label=None,
                widget=forms.Select(attrs={"class": "border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"})
            )

    def save(self, commit=True):
        student = super().save(commit=False)
        arm = self.cleaned_data.get('class_arm')
        if arm:
            student.current_class_arm = arm
            student.current_class_level = arm.class_level
        if commit:
            student.save()
        return student

    def clean(self):
        cleaned_data = super().clean()
        first_name = cleaned_data.get('first_name', '').strip()
        last_name = cleaned_data.get('last_name', '').strip()
        arm = cleaned_data.get('class_arm')

        if arm and first_name and last_name:
            # Check for duplicate name in the same arm (case-insensitive)
            if Student.objects.filter(
                current_class_arm=arm,
                first_name__iexact=first_name,
                last_name__iexact=last_name
            ).exists():
                raise forms.ValidationError(
                    "A student with this name already exists in this class arm."
                )

        return cleaned_data
