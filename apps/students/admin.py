from django.contrib import admin, messages
from django.contrib.admin.helpers import ActionForm
from django import forms
from django.db.models import Q
from .models import Student, AdmissionCounter


class StudentAdminForm(forms.ModelForm):
    create_login = forms.BooleanField(
        required=False,
        label="Create login account",
        help_text="Create a login account for this student with username=admission_number"
    )

    class Meta:
        model = Student
        fields = '__all__'

class HasLoginFilter(admin.SimpleListFilter):
    title = "login account"
    parameter_name = "has_login"

    def lookups(self, request, model_admin):
        return (("yes", "Has login"), ("no", "No login"))

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(user__isnull=False)
        if self.value() == "no":
            return queryset.filter(user__isnull=True)
        return queryset


class ProfileFilter(admin.SimpleListFilter):
    title = "profile"
    parameter_name = "profile"

    def lookups(self, request, model_admin):
        return (("incomplete", "Incomplete"), ("complete", "Complete"))

    def queryset(self, request, queryset):
        incomplete = (
            Q(date_of_birth__isnull=True) | Q(guardian_name="") | Q(guardian_phone="")
        )
        if self.value() == "incomplete":
            return queryset.filter(incomplete)
        if self.value() == "complete":
            return queryset.exclude(incomplete)
        return queryset
    
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    form = StudentAdminForm
    list_display = (
        "admission_number",
        "full_name",
        "current_class_level",
        "current_class_arm",
        "stream",
        "has_login",
        "is_profile_complete",
        "guardian_name",
        "guardian_phone",
    )
    search_fields = (
        "admission_number",
        "first_name",
        "last_name",
        "guardian_name",
    )
    list_filter = (
        ProfileFilter, 
        HasLoginFilter, 
        "current_class_level", 
        "current_class_arm", 
        "stream", 
        "gender"
    )
    
    # Update or add your fieldsets configuration to include 'stream' under 'Class':
    fieldsets = (
        # ... your other fieldsets ...
        ("Class", {"fields": ("current_class_level", "current_class_arm", "stream")}),
    )

    def has_login(self, obj):
        return bool(obj.user)
    has_login.boolean = True
    has_login.short_description = "Has Login"

    def is_profile_complete(self, obj):
        return obj.is_profile_complete
    is_profile_complete.boolean = True
    is_profile_complete.short_description = "Profile Complete"

    def save_model(self, request, obj, form, change):
        create_login = form.cleaned_data.get('create_login', False)
        super().save_model(request, obj, form, change)

        if create_login:
            try:
                username, password = obj.create_login_account()
                messages.warning(
                    request,
                    f"Login account created for {obj.full_name}. Username: {username}, Password: {password}"
                )
            except ValueError as e:
                messages.error(request, str(e))

    actions = ['create_login_accounts_action']

    @admin.action(description='Create login accounts for selected students')
    def create_login_accounts_action(self, request, queryset):
        count = 0
        for student in queryset:
            try:
                username, password = student.create_login_account()
                messages.warning(
                    request,
                    f"Login account created for {student.full_name}. Username: {username}, Password: {password}"
                )
                count += 1
            except ValueError as e:
                messages.error(request, f"Failed for {student.full_name}: {str(e)}")

        if count > 0:
            messages.success(request, f"Successfully created {count} login account(s).")
        else:
            messages.warning(request, "No login accounts were created.")


@admin.register(AdmissionCounter)
class AdmissionCounterAdmin(admin.ModelAdmin):
    list_display = ("class_level", "year", "last_number")
    list_filter = ("year", "class_level")
    search_fields = ("class_level__name",)