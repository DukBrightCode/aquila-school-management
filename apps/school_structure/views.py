from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.accounts.permissions import role_required
from .models import AcademicSession, Term, ClassLevel, ClassArm, Subject, ClassSubject


@login_required
@role_required("ADMIN")
def academic_session_list(request):
    sessions = AcademicSession.objects.all()
    return render(request, 'school_structure/academic_session_list.html', {'sessions': sessions})


@login_required
@role_required("ADMIN")
def term_list(request):
    terms = Term.objects.select_related('session').all()
    return render(request, 'school_structure/term_list.html', {'terms': terms})


@login_required
@role_required("ADMIN")
def class_level_list(request):
    class_levels = ClassLevel.objects.all()
    return render(request, 'school_structure/class_level_list.html', {'class_levels': class_levels})


@login_required
@role_required("ADMIN")
def class_arm_list(request):
    class_arms = ClassArm.objects.select_related('class_level').all()
    return render(request, 'school_structure/class_arm_list.html', {'class_arms': class_arms})


@login_required
@role_required("ADMIN")
def subject_list(request):
    subjects = Subject.objects.all()
    return render(request, 'school_structure/subject_list.html', {'subjects': subjects})


@login_required
@role_required("ADMIN")
def class_subject_list(request):
    class_subjects = ClassSubject.objects.select_related('class_level', 'subject').all()
    return render(request, 'school_structure/class_subject_list.html', {'class_subjects': class_subjects})


@login_required
@role_required("TEACHER", "ADMIN")
def manage_class_subjects(request, class_arm_id=None):
    """
    Allows class teachers to manage subjects for their assigned classes.
    Admins can manage subjects for all classes.
    """
    user = request.user

    # Get the classes the user can manage
    if user.is_superuser or user.role == "ADMIN":
        manageable_arms = ClassArm.objects.select_related('class_level').all()
    else:
        teacher = getattr(user, "teacher_profile", None)
        manageable_arms = teacher.class_arms_assigned.select_related('class_level').all() if teacher else ClassArm.objects.none()

    # If class_arm_id is provided, check permission
    selected_arm = None
    if class_arm_id:
        selected_arm = get_object_or_404(manageable_arms, id=class_arm_id)

    # Handle POST request to add/remove subjects
    if request.method == "POST" and selected_arm:
        action = request.POST.get("action")
        subject_id = request.POST.get("subject_id")

        if action == "add" and subject_id:
            subject = get_object_or_404(Subject, id=subject_id)
            if not selected_arm.subjects.filter(id=subject_id).exists():
                selected_arm.subjects.add(subject)
                messages.success(request, f"Subject '{subject.name}' added to {selected_arm}.")
            else:
                messages.warning(request, f"Subject '{subject.name}' is already assigned to {selected_arm}.")

        elif action == "remove" and subject_id:
            subject = get_object_or_404(Subject, id=subject_id)
            selected_arm.subjects.remove(subject)
            messages.success(request, f"Subject '{subject.name}' removed from {selected_arm}.")

        return redirect("school_structure:manage_class_subjects", class_arm_id=class_arm_id)

    # Get all available subjects
    all_subjects = Subject.objects.all().order_by("name")

    context = {
        'manageable_arms': manageable_arms,
        'selected_arm': selected_arm,
        'all_subjects': all_subjects,
    }

    return render(request, 'school_structure/manage_class_subjects.html', context)
