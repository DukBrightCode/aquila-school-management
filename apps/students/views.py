import logging
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, UpdateView
from apps.accounts.permissions import AdminRequiredMixin
from apps.school_structure.models import ClassArm, ClassLevel
from .forms import StudentForm
from .models import Student

logger = logging.getLogger(__name__)


class StudentListView(LoginRequiredMixin, ListView):
    model = Student
    template_name = "students/list.html"
    context_object_name = "students"

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .select_related("current_class_level", "current_class_arm")
        )
        class_level_id = self.request.GET.get("class_level")
        class_arm_id = self.request.GET.get("class_arm")

        if class_level_id:
            queryset = queryset.filter(current_class_level_id=class_level_id)
        if class_arm_id:
            queryset = queryset.filter(current_class_arm_id=class_arm_id)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["class_levels"] = ClassLevel.objects.all()
        context["selected_class_level"] = self.request.GET.get("class_level", "")
        if context["selected_class_level"]:
            context["class_arms"] = ClassArm.objects.filter(
                class_level_id=context["selected_class_level"]
            )
        else:
            context["class_arms"] = ClassArm.objects.none()
        context["selected_class_arm"] = self.request.GET.get("class_arm", "")
        return context


class StudentDetailView(LoginRequiredMixin, DetailView):
    model = Student
    template_name = "students/detail.html"
    context_object_name = "student"


class StudentCreateView(AdminRequiredMixin, CreateView):
    model = Student
    form_class = StudentForm
    template_name = "students/form.html"
    success_url = reverse_lazy("students:list")

    def form_valid(self, form):
        messages.success(self.request, "Student registered successfully.")
        return super().form_valid(form)


class StudentUpdateView(AdminRequiredMixin, UpdateView):
    model = Student
    form_class = StudentForm
    template_name = "students/form.html"
    success_url = reverse_lazy("students:list")

    def form_valid(self, form):
        messages.success(self.request, "Student record updated successfully.")
        return super().form_valid(form)


def promote_student(request, pk):
    if not request.user.is_authenticated or request.user.role != "ADMIN":
        messages.error(request, "Permission denied.")
        return redirect("students:list")

    if request.method == "POST":
        student = get_object_or_404(Student, pk=pk)
        current_level = student.current_class_level
        next_level = (
            ClassLevel.objects.filter(order__gt=current_level.order)
            .order_by("order")
            .first()
        )

        if next_level:
            old_level_str = str(current_level)
            student.current_class_level = next_level
            student.current_class_arm = None
            student.save()

            logger.info(
                f"Student {student.admission_number} promoted from {old_level_str} to {next_level} by {request.user.username}"
            )
            messages.success(
                request, f"Student successfully promoted to {next_level.name}."
            )
        else:
            messages.warning(
                request, "Student is already in the highest class level."
            )

    return redirect("students:detail", pk=pk)