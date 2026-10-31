from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, UpdateView
from apps.accounts.permissions import AdminRequiredMixin, role_required
from .forms import NonTeachingStaffForm, TeacherForm
from .models import NonTeachingStaff, Teacher


class StaffListView(AdminRequiredMixin, ListView):
    template_name = "staff/list.html"
    context_object_name = "teachers"
    queryset = Teacher.objects.select_related("user").all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["non_teaching_staff"] = NonTeachingStaff.objects.select_related(
            "user"
        ).all()
        return context


class TeacherDetailView(AdminRequiredMixin, DetailView):
    model = Teacher
    template_name = "staff/detail.html"
    context_object_name = "teacher"


class TeacherCreateView(AdminRequiredMixin, CreateView):
    model = Teacher
    form_class = TeacherForm
    template_name = "staff/form.html"
    success_url = reverse_lazy("staff:list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["staff_type"] = "Teacher"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Teacher added successfully.")
        return super().form_valid(form)


class TeacherUpdateView(AdminRequiredMixin, UpdateView):
    model = Teacher
    form_class = TeacherForm
    template_name = "staff/form.html"
    success_url = reverse_lazy("staff:list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["staff_type"] = "Teacher"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Teacher record updated successfully.")
        return super().form_valid(form)


class NonTeachingStaffCreateView(AdminRequiredMixin, CreateView):
    model = NonTeachingStaff
    form_class = NonTeachingStaffForm
    template_name = "staff/form.html"
    success_url = reverse_lazy("staff:list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["staff_type"] = "Non-Teaching Staff"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Staff member added successfully.")
        return super().form_valid(form)


class NonTeachingStaffUpdateView(AdminRequiredMixin, UpdateView):
    model = NonTeachingStaff
    form_class = NonTeachingStaffForm
    template_name = "staff/form.html"
    success_url = reverse_lazy("staff:list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["staff_type"] = "Non-Teaching Staff"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Staff record updated successfully.")
        return super().form_valid(form)


@login_required
@role_required("ADMIN")
def non_teaching_staff_list(request):
    """
    Admin view to manage non-teaching staff.
    """
    non_teaching_staff = NonTeachingStaff.objects.select_related("user").all()

    context = {
        "non_teaching_staff": non_teaching_staff,
    }
    return render(request, "staff/non_teaching_list.html", context)