from django import forms
from apps.school_structure.models import ClassArm


class AttendanceFilterForm(forms.Form):
    class_arm = forms.ModelChoiceField(
        queryset=ClassArm.objects.all(),
        required=True,
        widget=forms.Select(attrs={"class": "form-select rounded-md shadow-sm border-gray-300"}),
    )
    date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-input rounded-md shadow-sm border-gray-300"}),
    )