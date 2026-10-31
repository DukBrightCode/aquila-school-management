from django import forms
from django.contrib.auth import get_user_model
from .models import NonTeachingStaff, Teacher

User = get_user_model()


class TeacherForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    username = forms.CharField(max_length=150, required=False)

    class Meta:
        model = Teacher
        fields = [
            "staff_id",
            "subjects_taught",
            "class_arms_assigned",
            "date_employed",
        ]
        widgets = {
            "date_employed": forms.DateInput(attrs={"type": "date"}),
            "subjects_taught": forms.SelectMultiple(
                attrs={"class": "form-multiselect"}
            ),
            "class_arms_assigned": forms.SelectMultiple(
                attrs={"class": "form-multiselect"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.user:
            self.fields["first_name"].initial = self.instance.user.first_name
            self.fields["last_name"].initial = self.instance.user.last_name
            self.fields["email"].initial = self.instance.user.email
            self.fields["username"].initial = self.instance.user.username
            self.fields["username"].widget.attrs["readonly"] = True

    def save(self, commit=True):
        teacher = super().save(commit=False)
        first_name = self.cleaned_data["first_name"]
        last_name = self.cleaned_data["last_name"]
        email = self.cleaned_data["email"]

        if not teacher.pk:
            username = (
                self.cleaned_data.get("username") or teacher.staff_id.lower()
            )
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                role="TEACHER",
            )
            teacher.user = user
        else:
            user = teacher.user
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.save()

        if commit:
            teacher.save()
            self.save_m2m()
        return teacher


class NonTeachingStaffForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    username = forms.CharField(max_length=150, required=False)

    class Meta:
        model = NonTeachingStaff
        fields = ["staff_id", "designation"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.user:
            self.fields["first_name"].initial = self.instance.user.first_name
            self.fields["last_name"].initial = self.instance.user.last_name
            self.fields["email"].initial = self.instance.user.email
            self.fields["username"].initial = self.instance.user.username
            self.fields["username"].widget.attrs["readonly"] = True

    def save(self, commit=True):
        staff = super().save(commit=False)
        first_name = self.cleaned_data["first_name"]
        last_name = self.cleaned_data["last_name"]
        email = self.cleaned_data["email"]

        if not staff.pk:
            username = (
                self.cleaned_data.get("username") or staff.staff_id.lower()
            )
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                role="ADMIN",
            )
            staff.user = user
        else:
            user = staff.user
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.save()

        if commit:
            staff.save()
        return staff