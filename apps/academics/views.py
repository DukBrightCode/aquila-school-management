from io import BytesIO

import json
import logging
import os

from decimal import Decimal, InvalidOperation
from django.conf import settings
from django.db import transaction
from django.urls import reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from django.templatetags.static import static
from django.contrib import messages
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.utils.text import slugify
from django.utils import timezone
from django.db.models import Avg


from .models import StudentReportRemark, PredefinedRemark, Skill, StudentSkillRating
from .permissions import scoreable_arms, offered_subjects, scoreable_subjects



from apps.accounts.permissions import role_required
from apps.school_structure.models import ClassArm, Subject, Term, Stream
from apps.students.models import Student
from apps.academics.models import AssessmentType, Score, ResultRelease, Skill, StudentSkillRating, PredefinedRemark, StudentReportRemark
from apps.academics.services.result_mailer import build_report_card_context, send_result_email
from apps.academics.streams import students_taking
from apps.academics.permissions import (
    class_access_error,
    is_admin,
    result_access_error,
    scoreable_arms,
    is_admin,
    score_entry_arms,
    offered_subjects,
    scoreable_subjects,                               
)
from utils.pdf_generator import render_html_to_pdf, pdf_file_response

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# STAGE 6B VIEWS
# ----------------------------------------------------------------------

EXAM_TYPES = ("MID_TERM", "FULL_TERM")
 
 
def _score_entry_access(user, class_arm_id, subject_id=None):
    """
    Returns (teacher, class_arm, error). `error` is a JsonResponse when access is refused,
    otherwise None. `teacher` is None for admins.
    """
    if not str(class_arm_id).isdigit():
        return None, None, JsonResponse({"error": "Invalid class."}, status=400)
    class_arm = ClassArm.objects.filter(id=class_arm_id).first()
    if class_arm is None:
        return None, None, JsonResponse({"error": "Class not found."}, status=404)
 
    teacher = None
    if not is_admin(user):
        teacher = getattr(user, "teacher_profile", None)
        if not teacher or not score_entry_arms(teacher).filter(id=class_arm.id).exists():
            return teacher, class_arm, JsonResponse(
                {"error": "Permission denied. You are not assigned to this class."}, status=403
            )
 
    if subject_id is not None:
        if not str(subject_id).isdigit():
            return teacher, class_arm, JsonResponse({"error": "Invalid subject."}, status=400)
        if not offered_subjects(class_arm).filter(id=subject_id).exists():
            return teacher, class_arm, JsonResponse(
                {"error": "This subject is not offered for this class."}, status=403
            )
        if teacher and not scoreable_subjects(teacher, class_arm).filter(id=subject_id).exists():
            return teacher, class_arm, JsonResponse(
                {"error": "You are not authorized to enter scores for this subject."}, status=403
            )
 
    return teacher, class_arm, None
 

@role_required("TEACHER", "ADMIN")
@require_GET
def score_entry(request):
    """
    Score Entry page shell with filter dropdowns.
    Teachers see the classes they lead plus the classes where they are an assigned subject teacher.
    """
    user = request.user
    if is_admin(user):
        class_arms = ClassArm.objects.all().order_by("name")
    else:
        teacher = getattr(user, "teacher_profile", None)
        class_arms = score_entry_arms(teacher) if teacher else ClassArm.objects.none()
 
    context = {
        "class_arms": class_arms,
        "subjects": Subject.objects.all().order_by("name"),
        "terms": Term.objects.select_related("session").all().order_by("-is_current", "-id"),
    }
    return render(request, "academics/score_entry.html", context)


@role_required("TEACHER", "ADMIN")
@require_GET
def get_class_subjects(request):
    """
    JSON API: the subjects this user may enter scores for in the selected class.
    Class teachers and admins get every subject the class offers; a subject teacher
    gets only the subjects assigned to them.
    """
    class_arm_id = request.GET.get("class_arm")
    if not class_arm_id:
        return JsonResponse({"error": "Missing class_arm parameter."}, status=400)
 
    teacher, class_arm, error = _score_entry_access(request.user, class_arm_id)
    if error:
        return error
 
    subjects = scoreable_subjects(teacher, class_arm) if teacher else offered_subjects(class_arm)
    return JsonResponse({
        "subjects": [
            {"id": s.id, "name": s.name, "code": s.code}
            for s in subjects.order_by("name")
        ]
    })


@role_required("TEACHER", "ADMIN")
@require_GET
def score_entry_data(request):
    """
    JSON API: assessment columns, student roster and entered raw scores.
    """
    class_arm_id = request.GET.get("class_arm")
    subject_id = request.GET.get("subject")
    term_id = request.GET.get("term")
    exam_type = request.GET.get("exam_type", "FULL_TERM")
 
    if not all([class_arm_id, subject_id, term_id]):
        return JsonResponse({"error": "Missing required filter parameters."}, status=400)
    if not str(term_id).isdigit() or exam_type not in EXAM_TYPES:
        return JsonResponse({"error": "Invalid term or exam type."}, status=400)
 
    teacher, class_arm, error = _score_entry_access(request.user, class_arm_id, subject_id)
    if error:
        return error
 
    # Only the columns that belong to the chosen exam type for this term
    assessment_types = list(
        AssessmentType.objects.filter(term_id=term_id, is_active=True, exam_type=exam_type)
        .order_by("id")
        .values("id", "name", "max_score", "weight_percentage")
    )
    for at in assessment_types:
        at["max_score"] = float(at["max_score"])
        at["weight_percentage"] = float(at["weight_percentage"])
 
    subject = Subject.objects.get(id=subject_id)
    # only the students who take this subject (by stream)
    students_qs = students_taking(class_arm.id, subject).order_by("last_name", "first_name")
    students = [
        {"id": st.id, "admission_number": st.admission_number, "full_name": st.full_name}
        for st in students_qs
    ]
 
    scores_qs = Score.objects.filter(
        subject_id=subject_id,
        term_id=term_id,
        class_arm_id=class_arm.id,
        exam_type=exam_type,
        assessment_type__is_active=True,
        assessment_type__exam_type=exam_type,
    ).values("student_id", "assessment_type_id", "score_value")
 
    scores_dict = {
        f"{sc['student_id']}-{sc['assessment_type_id']}": float(sc["score_value"])
        for sc in scores_qs
    }
 
    return JsonResponse({
        "assessment_types": assessment_types,
        "students": students,
        "scores": scores_dict,
    })
    
 
@role_required("TEACHER", "ADMIN")
@require_POST
def score_entry_save(request):
    """
    Bulk upserts raw scores for a class, subject, term and exam type.
    Everything is validated first; if anything is invalid, nothing is saved.
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON payload."}, status=400)
 
    subject_id = data.get("subject_id")
    term_id = data.get("term_id")
    class_arm_id = data.get("class_arm_id")
    exam_type = data.get("exam_type", "FULL_TERM")
    rows = data.get("rows", [])
 
    if not all([subject_id, term_id, class_arm_id]):
        return JsonResponse({"error": "Missing subject_id, term_id, or class_arm_id."}, status=400)
    if not str(term_id).isdigit() or exam_type not in EXAM_TYPES or not isinstance(rows, list):
        return JsonResponse({"error": "Invalid term, exam type or rows."}, status=400)
 
    teacher, class_arm, error = _score_entry_access(request.user, class_arm_id, subject_id)
    if error:
        return error
 
    # What this save is allowed to touch
    components = {
        c.id: c
        for c in AssessmentType.objects.filter(term_id=term_id, is_active=True, exam_type=exam_type)
    }
    subject = Subject.objects.get(id=subject_id)
    class_student_ids = set(students_taking(class_arm.id, subject).values_list("id", flat=True))
 
    # ---- validate everything before writing anything -------------------------
    parsed = []          # (student_id, assessment_type_id, Decimal value)
    errors = set()
    for row in rows:
        if not isinstance(row, dict) or not row.get("student_id"):
            continue
        try:
            student_id = int(row["student_id"])
        except (TypeError, ValueError):
            errors.add("Invalid student.")
            continue
        if student_id not in class_student_ids:
            errors.add("A student in the list is not in this class or does not take this subject. Please reload the page.")
            continue
 
        scores = row.get("scores") or {}
        if not isinstance(scores, dict):
            errors.add("Invalid scores.")
            continue
        for at_id_str, val in scores.items():
            if val is None or str(val).strip() == "":
                continue
            try:
                at_id = int(at_id_str)
                score_val = Decimal(str(val).strip())
            except (ValueError, InvalidOperation):
                errors.add("Scores must be numbers.")
                continue
            component = components.get(at_id)
            if component is None:
                errors.add("A score column is not valid for this term and exam type. Please reload the page.")
                continue
            if not score_val.is_finite() or score_val < 0 or score_val > component.max_score:
                errors.add(f"{component.name} must be between 0 and {component.max_score:g}.")
                continue
            parsed.append((student_id, at_id, score_val.quantize(Decimal("0.01"))))
 
    if errors:
        return JsonResponse({"error": " ".join(sorted(errors)), "saved": 0}, status=400)
    if not parsed:
        return JsonResponse({"saved": 0})
 
    # ---- one query for existing scores, then one atomic write ----------------
    student_ids = {p[0] for p in parsed}
    existing = {
        (s.student_id, s.assessment_type_id): s
        for s in Score.objects.filter(
            subject_id=subject_id, term_id=term_id, exam_type=exam_type, student_id__in=student_ids
        )
    }
 
    to_create, to_update = [], []
    for student_id, at_id, value in parsed:
        score_obj = existing.get((student_id, at_id))
        if score_obj:
            score_obj.score_value = value
            score_obj.class_arm_id = class_arm.id
            score_obj.entered_by = teacher
            to_update.append(score_obj)
        else:
            to_create.append(Score(
                student_id=student_id,
                subject_id=subject_id,
                term_id=term_id,
                assessment_type_id=at_id,
                exam_type=exam_type,
                class_arm_id=class_arm.id,
                score_value=value,
                entered_by=teacher,
            ))
 
    with transaction.atomic():
        if to_create:
            Score.objects.bulk_create(to_create)
        if to_update:
            Score.objects.bulk_update(to_update, ["score_value", "class_arm_id", "entered_by"])
 
    return JsonResponse({"saved": len(parsed)})

@role_required("TEACHER", "ADMIN")
def rate_skills(request):
    """Teacher picks class + term, rates every student, and can add new skills."""
    user = request.user
    if user.is_superuser or user.role == "ADMIN":
        class_arms_qs = ClassArm.objects.all().order_by("name")
    else:
        teacher = getattr(user, "teacher_profile", None)
        class_arms_qs = scoreable_arms(teacher) if teacher else ClassArm.objects.none()

    terms = Term.objects.select_related("session").order_by("-is_current", "-id")
    arm_id = request.GET.get("class_arm")
    term_id = request.GET.get("term")
    ctx = {"class_arms": class_arms_qs, "terms": terms,
           "sel_arm": arm_id or "", "sel_term": term_id or ""}

    if not (arm_id and term_id):
        return render(request, "academics/rate_skills.html", ctx)

    arm = get_object_or_404(class_arms_qs, pk=arm_id)
    term = get_object_or_404(Term, pk=term_id)
    students = (Student.objects.filter(current_class_arm=arm)
                .order_by("last_name", "first_name"))

    if request.method == "POST":
        # (a) add a new skill to the master list (shared by all classes)
        new_name = request.POST.get("new_skill", "").strip()
        if new_name:
            skill = Skill.objects.filter(name__iexact=new_name).first()
            if skill:
                messages.info(request, f"'{skill.name}' is already on the list.")
            else:
                skill = Skill.objects.create(
                    name=new_name, created_by=request.user,
                    display_order=Skill.objects.count() + 1)
                messages.success(request, f"'{skill.name}' added to the list.")

        # (b) save ratings; field names look like  r_<student_id>_<skill_id>
        valid_students = {str(s.id) for s in students}
        saved = 0
        for key, val in request.POST.items():
            if not key.startswith("r_") or val not in {"1", "2", "3", "4", "5"}:
                continue
            try:
                _, sid, kid = key.split("_")
            except ValueError:
                continue
            if sid not in valid_students:
                continue
            StudentSkillRating.objects.update_or_create(
                student_id=sid, term=term, skill_id=kid,
                defaults={"rating": int(val), "rated_by": request.user})
            saved += 1
        if saved:
            messages.success(request, f"{saved} ratings saved.")
        return redirect(request.get_full_path())

    skills = Skill.objects.filter(is_active=True)
    existing = {(r.student_id, r.skill_id): r.rating
                for r in StudentSkillRating.objects.filter(student__in=students, term=term)}
    ctx["rows"] = [
        {"student": s,
         "cells": [{"skill": k, "value": existing.get((s.id, k.id), "")} for k in skills]}
        for s in students]
    ctx["skills"] = skills
    ctx["arm"], ctx["term"] = arm, term
    return render(request, "academics/rate_skills.html", ctx)


@login_required
@require_GET
def report_card(request, student_id: int, term_id: int, report_type: str = 'full', exam_type: str = 'FULL_TERM'):
    """Web report card. Admins: any student. Class teachers: own class, once released."""
    student = get_object_or_404(Student, id=student_id)
 
    error = result_access_error(request.user, student, term_id, exam_type)
    if error:
        messages.error(request, error)
        return redirect("academics:report_card_list")
 
    logo_url = request.build_absolute_uri(static("src/images/logo.jpg"))
    context = build_report_card_context(student_id, term_id, logo_url=logo_url, report_type=report_type, exam_type=exam_type)
 
    context['today_date'] = timezone.now().date()
    context['report_remark'] = StudentReportRemark.objects.filter(
        student_id=student_id,
        term_id=term_id
    ).first()
    context['report_type'] = report_type
    context['exam_type'] = exam_type
    context['can_email'] = is_admin(request.user)   # template hides Send Email unless True
 
    return render(request, "academics/report_card.html", context)


# ----------------------------------------------------------------------
# STAGE 6C VIEWS (PDF GENERATION & EMAIL DISPATCH)
# ----------------------------------------------------------------------

@login_required
@require_GET
# ---- C) REPLACE generate_report_card_pdf with these two functions ------------
def _render_report_card_pdf(request, student, term_id, report_type, exam_type):
    """Builds one student's report card PDF and returns the bytes."""
    logo_url = request.build_absolute_uri(static("src/images/logo.jpg"))
    context = build_report_card_context(student.id, term_id, logo_url=logo_url, report_type=report_type, exam_type=exam_type)
 
    context['today_date'] = timezone.now().date()
    context['report_remark'] = StudentReportRemark.objects.filter(
        student_id=student.id,
        term_id=term_id
    ).first()
    context['report_type'] = report_type
    context['exam_type'] = exam_type
 
    # Student photo (default avatar fallback)
    student_photo_path = None
    if student.photo and hasattr(student.photo, 'path') and os.path.exists(student.photo.path):
        student_photo_path = student.photo.path
    else:
        default_avatar = os.path.join(settings.BASE_DIR, 'static', 'src', 'images', 'default_avatar.png')
        if os.path.exists(default_avatar):
            student_photo_path = default_avatar
        elif hasattr(settings, 'STATIC_ROOT') and settings.STATIC_ROOT:
            default_avatar_root = os.path.join(settings.STATIC_ROOT, 'src', 'images', 'default_avatar.png')
            if os.path.exists(default_avatar_root):
                student_photo_path = default_avatar_root
 
    # School logo
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'src', 'images', 'logo.jpg')
    if not os.path.exists(logo_path) and hasattr(settings, 'STATIC_ROOT') and settings.STATIC_ROOT:
        logo_path = os.path.join(settings.STATIC_ROOT, 'src', 'images', 'logo.jpg')
        if not os.path.exists(logo_path):
            logo_path = None
 
    context["pdf_student_photo"] = student_photo_path
    context["pdf_logo_path"] = logo_path
 
    html_string = render_to_string("academics/report_card.html", context, request=request)
    return render_html_to_pdf(html_string)


@login_required
def generate_report_card_pdf(request, student_id: int, term_id: int, report_type: str = 'full', exam_type: str = 'FULL_TERM'):
    """PDF of one report card. Admins: any student. Class teachers: own class, once released."""
    student = get_object_or_404(Student, id=student_id)
 
    error = result_access_error(request.user, student, term_id, exam_type)
    if error:
        messages.error(request, error)
        return redirect("academics:report_card_list")
 
    pdf_bytes = _render_report_card_pdf(request, student, term_id, report_type, exam_type)
    filename = f"Report_Card_{student.admission_number}_Term_{term_id}_{report_type}.pdf".replace("/", "-")
    return pdf_file_response(pdf_bytes, filename)
 

@role_required("TEACHER", "ADMIN")
@login_required
def send_single_result_email(request, student_id: int, term_id: int):
    student = get_object_or_404(Student, id=student_id)
    term = get_object_or_404(Term, id=term_id)
 
    recipient_email = student.guardian_email or (student.user.email if student.user else '')
 
    if request.method == "POST":
        custom_subject = request.POST.get("subject", "").strip()
        custom_body = request.POST.get("message", "").strip()
        recipient = request.POST.get("recipient_email", "").strip()
 
        if not recipient:
            messages.error(request, "Please enter a valid recipient email address.")
            return redirect("academics:send_single_result_email", student_id=student_id, term_id=term_id)
 
        try:
            email = EmailMessage(
                subject=custom_subject,
                body=custom_body,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                to=[recipient],
            )
 
            for file in request.FILES.getlist('attachments'):
                email.attach(file.name, file.read(), file.content_type)
 
            email.send(fail_silently=False)
            messages.success(request, f"Result email successfully sent to {recipient}.")
            # report_card_legacy takes (student_id, term_id); "report_card" needs four arguments
            return redirect("academics:report_card_legacy", student_id=student_id, term_id=term_id)
 
        except Exception as e:
            messages.error(request, f"Failed to send email: {str(e)}")
            return redirect("academics:send_single_result_email", student_id=student_id, term_id=term_id)
 
    default_subject = f"Academic Report Card - {student.full_name} ({term.name})"
    default_body = (
        f"Dear Parent/Guardian,\n\n"
        f"Please find attached the academic report card for {student.full_name} "
        f"for {term.name}.\n\n"
        f"Warm regards,\n"
        f"Aquila British International School"
    )
 
    context = {
        'student': student,
        'term': term,
        'recipient_email': recipient_email,
        'default_subject': default_subject,
        'default_body': default_body,
    }
    return render(request, 'academics/compose_email.html', context)
 
 


@role_required("ADMIN")
@require_POST
def send_class_result_emails(request, class_arm_id: int, term_id: int):
    """Bulk sends report card PDFs via email to all students in a class arm (admin only)."""
    students = Student.objects.filter(current_class_arm_id=class_arm_id)
    sent_count = 0
    fail_count = 0
 
    for student in students:
        if send_result_email(student=student.id, term=term_id):
            sent_count += 1
        else:
            fail_count += 1
 
    messages.info(
        request,
        f"Bulk Email Process Complete: {sent_count} sent successfully, {fail_count} failed."
    )
    return redirect(request.META.get("HTTP_REFERER", "academics:report_card_list"))


@role_required("TEACHER", "ADMIN")
def class_results_summary(request, class_arm_id: int, term_id: int):
    """
    Provides a summary of results for a class.
    """
    user = request.user
    if not (user.is_superuser or user.role == "ADMIN"):
        teacher = getattr(user, "teacher_profile", None)
        if not teacher or not scoreable_arms(teacher).filter(id=class_arm_id).exists():
            messages.error(request, "Permission denied. You are not the class teacher for this class.")
            return redirect("academics:score_entry")

    # Retrieve class arm and term objects
    class_arm = get_object_or_404(ClassArm, id=class_arm_id)
    term = get_object_or_404(Term, id=term_id)

    # Add your logic here to gather class results...

    context = {
        'class_arm': class_arm,
        'term': term,
    }
    return render(request, 'academics/class_results_summary.html', context)




@login_required
@role_required("TEACHER", "ADMIN")
def report_card_list(request):
    """
    Report cards page. Admins see everyone and control releases.
    Class teachers see only the classes they lead.
    """
    user = request.user
    admin = is_admin(user)
 
    terms = Term.objects.select_related("session").order_by("-is_current", "-id")
    term_param = request.GET.get("term", "")
    term = terms.filter(pk=term_param).first() if term_param.isdigit() else None
    term = term or terms.filter(is_current=True).first() or terms.first()
 
    if admin:
        arms = ClassArm.objects.select_related("class_level")
        students = Student.objects.all()
    else:
        teacher = getattr(user, "teacher_profile", None)
        arms = scoreable_arms(teacher) if teacher else ClassArm.objects.none()
        students = Student.objects.filter(current_class_arm__in=arms)
 
    arm_param = request.GET.get("arm", "")
    selected_arm_id = int(arm_param) if arm_param.isdigit() else None
    if selected_arm_id:
        students = students.filter(current_class_arm_id=selected_arm_id)
        arms_shown = arms.filter(pk=selected_arm_id)
    else:
        arms_shown = arms
 
    students = list(
        students.select_related("current_class_level", "current_class_arm")
        .order_by("current_class_level__order", "current_class_arm__name", "last_name", "first_name")
    )
 
    released = set()
    if term:
        released = set(
            ResultRelease.objects.filter(term=term, is_released=True)
            .values_list("class_arm_id", "exam_type")
        )
    for s in students:
        s.can_open_mid = admin or (s.current_class_arm_id, "MID_TERM") in released
        s.can_open_full = admin or (s.current_class_arm_id, "FULL_TERM") in released
 
    release_rows = [
        {
            "arm": a,
            "mid_released": (a.id, "MID_TERM") in released,
            "full_released": (a.id, "FULL_TERM") in released,
        }
        for a in arms_shown
    ]
 
    context = {
        "students": students,
        "term": term,
        "current_term": term,          # kept: the old template used this name
        "terms": terms,
        "arms": arms,
        "selected_arm_id": selected_arm_id,
        "release_rows": release_rows,
        "is_admin": admin,
        "can_email": admin,
    }
    return render(request, "academics/report_card_list.html", context)


# API endpoint for teachers/admins to fetch remarks dynamically
def api_get_predefined_remarks(request):
    remarks = list(PredefinedRemark.objects.values('id', 'type', 'text'))
    return JsonResponse({'remarks': remarks})

@role_required("TEACHER", "ADMIN")
@require_GET
def class_report_cards_pdf(request, class_arm_id: int, term_id: int, exam_type: str):
    """One PDF with every student's report card in the class (one card per page set)."""
    if exam_type not in ("MID_TERM", "FULL_TERM"):
        raise Http404("Unknown exam type")
 
    arm = get_object_or_404(ClassArm.objects.select_related("class_level"), id=class_arm_id)
    get_object_or_404(Term, id=term_id)
 
    error = class_access_error(request.user, arm.id, term_id, exam_type)
    if error:
        messages.error(request, error)
        return redirect("academics:report_card_list")
 
    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError:
        messages.error(request, "PDF merging is not installed. Run: pip install pypdf")
        return redirect("academics:report_card_list")
 
    #report_type = "mid" if exam_type == "MID_TERM" else "full"
    report_type = "full"   # same value the existing View/PDF links use
    students = Student.objects.filter(current_class_arm=arm).order_by("last_name", "first_name")
 
    writer = PdfWriter()
    added = 0
    for student in students:
        try:
            pdf_bytes = _render_report_card_pdf(request, student, term_id, report_type, exam_type)
            for page in PdfReader(BytesIO(pdf_bytes)).pages:
                writer.add_page(page)
            added += 1
        except Exception as exc:   # one bad card must not stop the whole class
            print(f"[CLASS PDF] skipped {student}: {exc!r}")
 
    if not added:
        messages.error(request, "No report cards could be generated for this class.")
        return redirect("academics:report_card_list")
 
    out = BytesIO()
    writer.write(out)
    filename = f"Class_Results_{slugify(str(arm))}_{exam_type}.pdf"
    return pdf_file_response(out.getvalue(), filename)

@role_required("ADMIN")
@require_POST
def toggle_result_release(request, class_arm_id: int, term_id: int, exam_type: str):
    if exam_type not in ("MID_TERM", "FULL_TERM"):
        raise Http404("Unknown exam type")
 
    arm = get_object_or_404(ClassArm, id=class_arm_id)
    term = get_object_or_404(Term, id=term_id)
 
    release, _ = ResultRelease.objects.get_or_create(
        term=term, class_arm=arm, exam_type=exam_type
    )
    release.is_released = not release.is_released
    release.released_at = timezone.now() if release.is_released else None
    release.released_by = request.user if release.is_released else None
    release.save()
 
    state = "released to" if release.is_released else "withdrawn from"
    messages.success(request, f"{arm} {exam_type.replace('_', ' ').title()} results {state} the class teacher.")
    return redirect(f"{reverse('academics:report_card_list')}?term={term.id}")
 
 

SKILL_SCALE = [5, 4, 3, 2, 1]   # 5 = Excellent ... 1 = Poor
 
 
@role_required("TEACHER", "ADMIN")
def class_skill_ratings(request):
    """
    One page for a whole class: students down the side, skills across the top.
    Class teachers can rate only the arms they lead. Skills are managed by the admin.
    """
    user = request.user
    if is_admin(user):
        arms = ClassArm.objects.select_related("class_level")
    else:
        teacher = getattr(user, "teacher_profile", None)
        arms = scoreable_arms(teacher) if teacher else ClassArm.objects.none()
 
    terms = Term.objects.select_related("session").order_by("-is_current", "-id")
 
    data = request.POST if request.method == "POST" else request.GET
    arm_param = data.get("arm", "")
    term_param = data.get("term", "")
 
    arm = arms.filter(pk=arm_param).first() if arm_param.isdigit() else None
    if arm is None and not arm_param and arms.count() == 1:
        arm = arms.first()
 
    term = terms.filter(pk=term_param).first() if term_param.isdigit() else None
    term = term or terms.filter(is_current=True).first() or terms.first()
 
    skills = list(Skill.objects.filter(is_active=True))
    students = []
    if arm:
        students = list(
            Student.objects.filter(current_class_arm=arm).order_by("last_name", "first_name")
        )
 
    existing = {}
    if students and skills and term:
        existing = {
            (r.student_id, r.skill_id): r
            for r in StudentSkillRating.objects.filter(
                student__in=students, term=term, skill__in=skills
            )
        }
 
    # ---------------------------------------------------------------- save
    if request.method == "POST":
        if not (arm and term):
            messages.error(request, "Please choose a class and a term.")
            return redirect("academics:class_skill_ratings")
 
        to_create, to_update, to_delete = [], [], []
        invalid = 0
        for s in students:
            for sk in skills:
                key = f"r_{s.id}_{sk.id}"
                if key not in request.POST:          # field not on the page: leave as is
                    continue
                raw = request.POST[key].strip()
                current = existing.get((s.id, sk.id))
                if raw == "":                        # cleared by the teacher
                    if current:
                        to_delete.append(current.pk)
                    continue
                if not raw.isdigit() or not 1 <= int(raw) <= 5:
                    invalid += 1
                    continue
                value = int(raw)
                if current:
                    if current.rating != value:
                        current.rating = value
                        current.rated_by = user
                        to_update.append(current)
                else:
                    to_create.append(StudentSkillRating(
                        student=s, term=term, skill=sk, rating=value, rated_by=user
                    ))
 
        with transaction.atomic():
            if to_delete:
                StudentSkillRating.objects.filter(pk__in=to_delete).delete()
            if to_create:
                StudentSkillRating.objects.bulk_create(to_create)
            if to_update:
                StudentSkillRating.objects.bulk_update(to_update, ["rating", "rated_by"])
 
        messages.success(request, f"Skills and behaviour saved for {arm}.")
        if invalid:
            messages.warning(request, f"{invalid} invalid value(s) were ignored (use 1 to 5).")
        return redirect(f"{reverse('academics:class_skill_ratings')}?arm={arm.id}&term={term.id}")
 
    # ---------------------------------------------------------------- show
    rows = [
        {
            "student": s,
            "cells": [
                {
                    "field": f"r_{s.id}_{sk.id}",
                    "value": existing[(s.id, sk.id)].rating if (s.id, sk.id) in existing else "",
                }
                for sk in skills
            ],
        }
        for s in students
    ]
 
    return render(request, "academics/class_skill_ratings.html", {
        "arms": arms,
        "terms": terms,
        "arm": arm,
        "term": term,
        "skills": skills,
        "rows": rows,
        "scale": SKILL_SCALE,
    })
    
    

KEEP = "keep"   # form value meaning "leave the current remark as it is"
@role_required("TEACHER", "ADMIN")
def class_remarks(request):
    """
    One page for a whole class: for every student, the class teacher's remark and the
    principal's remark, each chosen from the admin's ready-made list.
    Class teachers can only do this for the classes they lead.
    Remarks belong to the term, so they show on both the Mid Term and Full Term report.
    """
    user = request.user
    if is_admin(user):
        arms = ClassArm.objects.select_related("class_level")
    else:
        teacher = getattr(user, "teacher_profile", None)
        arms = scoreable_arms(teacher) if teacher else ClassArm.objects.none()
 
    terms = Term.objects.select_related("session").order_by("-is_current", "-id")
 
    data = request.POST if request.method == "POST" else request.GET
    arm_param = data.get("arm", "")
    term_param = data.get("term", "")
 
    arm = arms.filter(pk=arm_param).first() if arm_param.isdigit() else None
    if arm is None and not arm_param and arms.count() == 1:
        arm = arms.first()
 
    term = terms.filter(pk=term_param).first() if term_param.isdigit() else None
    term = term or terms.filter(is_current=True).first() or terms.first()
 
    # The only allowed choices: what the admin put in Predefined remarks.
    teacher_options = list(PredefinedRemark.objects.filter(type="TEACHER").order_by("text"))
    principal_options = list(PredefinedRemark.objects.filter(type="PRINCIPAL").order_by("text"))
    teacher_by_id = {str(p.id): p.text for p in teacher_options}
    principal_by_id = {str(p.id): p.text for p in principal_options}
 
    students = []
    if arm:
        students = list(
            Student.objects.filter(current_class_arm=arm).order_by("last_name", "first_name")
        )
 
    existing = {}
    if students and term:
        existing = {
            r.student_id: r
            for r in StudentReportRemark.objects.filter(student__in=students, term=term)
        }
 
    def resolve(raw, allowed, current_text):
        """Returns (new_text, ok). KEEP leaves it as is, '' clears it, an id must be in `allowed`."""
        raw = (raw or "").strip()
        if raw == KEEP:
            return current_text, True
        if raw == "":
            return None, True
        if raw in allowed:
            return allowed[raw], True
        return current_text, False        # not one of the admin's remarks: ignored
 
    # ---------------------------------------------------------------- save
    if request.method == "POST":
        if not (arm and term):
            messages.error(request, "Please choose a class and a term.")
            return redirect("academics:class_remarks")
 
        to_create, to_update = [], []
        rejected = 0
        for s in students:
            teacher_key, principal_key = f"t_{s.id}", f"p_{s.id}"
            if teacher_key not in request.POST and principal_key not in request.POST:
                continue                      # fields not on the page: leave as they are
 
            current = existing.get(s.id)
            cur_teacher = current.teacher_remark if current else None
            cur_principal = current.principal_remark if current else None
            new_teacher, new_principal = cur_teacher, cur_principal
 
            if teacher_key in request.POST:
                new_teacher, ok = resolve(request.POST[teacher_key], teacher_by_id, cur_teacher)
                rejected += 0 if ok else 1
            if principal_key in request.POST:
                new_principal, ok = resolve(request.POST[principal_key], principal_by_id, cur_principal)
                rejected += 0 if ok else 1
 
            if current:
                if (cur_teacher, cur_principal) != (new_teacher, new_principal):
                    current.teacher_remark = new_teacher
                    current.principal_remark = new_principal
                    to_update.append(current)
            elif new_teacher or new_principal:
                to_create.append(StudentReportRemark(
                    student=s, term=term,
                    teacher_remark=new_teacher, principal_remark=new_principal,
                ))
 
        with transaction.atomic():
            if to_create:
                StudentReportRemark.objects.bulk_create(to_create)
            if to_update:
                StudentReportRemark.objects.bulk_update(to_update, ["teacher_remark", "principal_remark"])
 
        messages.success(request, f"Remarks saved for {arm}.")
        if rejected:
            messages.warning(request, f"{rejected} choice(s) were ignored because they are not in the approved list.")
        return redirect(f"{reverse('academics:class_remarks')}?arm={arm.id}&term={term.id}")
 
    # ---------------------------------------------------------------- show
    teacher_id_by_text = {text: pid for pid, text in teacher_by_id.items()}
    principal_id_by_text = {text: pid for pid, text in principal_by_id.items()}
 
    def selected_value(current_text, id_by_text):
        if not current_text:
            return ""
        return id_by_text.get(current_text, KEEP)   # custom text from the admin: shown, kept
 
    rows = []
    for s in students:
        r = existing.get(s.id)
        t_text = r.teacher_remark if r else None
        p_text = r.principal_remark if r else None
        t_sel = selected_value(t_text, teacher_id_by_text)
        p_sel = selected_value(p_text, principal_id_by_text)
        rows.append({
            "student": s,
            "teacher_selected": t_sel,
            "teacher_custom": t_text if t_sel == KEEP else "",
            "principal_selected": p_sel,
            "principal_custom": p_text if p_sel == KEEP else "",
        })
 
    return render(request, "academics/class_remarks.html", {
        "arms": arms,
        "terms": terms,
        "arm": arm,
        "term": term,
        "rows": rows,
        "teacher_options": teacher_options,
        "principal_options": principal_options,
        "keep": KEEP,
    })

@role_required("TEACHER", "ADMIN")
def class_streams(request):
    """
    One page per class: tick Science / Art / Commercial for each student.
    Only the class teachers of that class (and admins) can do this.
    A student's stream decides which subjects appear on their report and in score entry.
    """
    user = request.user
    if is_admin(user):
        arms = ClassArm.objects.select_related("class_level")
    else:
        teacher = getattr(user, "teacher_profile", None)
        arms = scoreable_arms(teacher) if teacher else ClassArm.objects.none()
 
    data = request.POST if request.method == "POST" else request.GET
    arm_param = data.get("arm", "")
    arm = arms.filter(pk=arm_param).first() if arm_param.isdigit() else None
    if arm is None and not arm_param and arms.count() == 1:
        arm = arms.first()
 
    streams = list(Stream.objects.order_by("order", "name"))
    students = []
    if arm:
        students = list(Student.objects.filter(current_class_arm=arm).order_by("last_name", "first_name"))
 
    # ---------------------------------------------------------------- save
    if request.method == "POST":
        if not arm:
            messages.error(request, "Please choose a class.")
            return redirect("academics:class_streams")
 
        valid_ids = {str(s.id): s.id for s in streams}
        to_update, rejected = [], 0
        for st in students:
            key = f"s_{st.id}"
            if key not in request.POST:
                continue                                 # not on the page: leave as it is
            raw = request.POST[key].strip()
            if raw == "":
                new_stream = None
            elif raw in valid_ids:
                new_stream = valid_ids[raw]
            else:
                rejected += 1
                continue
            if st.stream_id != new_stream:
                st.stream_id = new_stream
                to_update.append(st)
 
        with transaction.atomic():
            if to_update:
                Student.objects.bulk_update(to_update, ["stream"])
 
        messages.success(request, f"Streams saved for {arm}.")
        if rejected:
            messages.warning(request, f"{rejected} choice(s) were ignored because they are not valid streams.")
        return redirect(f"{reverse('academics:class_streams')}?arm={arm.id}")
 
    # ---------------------------------------------------------------- show
    rows = [{"student": s, "stream_id": s.stream_id} for s in students]
    counts = [
        {"name": st.name, "count": sum(1 for s in students if s.stream_id == st.id)}
        for st in streams
    ]
    counts.append({"name": "Not set", "count": sum(1 for s in students if s.stream_id is None)})
 
    return render(request, "academics/class_streams.html", {
        "arms": arms, "arm": arm, "streams": streams, "rows": rows, "counts": counts,
    })