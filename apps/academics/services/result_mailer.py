from decimal import Decimal, ROUND_HALF_UP
import logging
from email.mime.image import MIMEImage
from pathlib import Path

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.staticfiles import finders


from apps.students.models import Student
from apps.school_structure.models import Term, Subject
from apps.academics.models import Score, StudentSkillRating, GradingScale
from apps.academics.streams import subjects_for_student


from apps.academics.services.grade_calculator import calculate_term_result
from utils.pdf_generator import render_html_to_pdf


from apps.academics.results import (
    compute_subject_result, out_of_for, subject_teacher_name, class_position_info,
)

logger = logging.getLogger(__name__)


def build_report_card_context(student, term, *, logo_cid=None, logo_url=None, report_type='full', exam_type='FULL_TERM') -> dict:
    """
    Builds the standardized context dictionary required for rendering student report cards.
    Accepts student and term as model instances or primary key integers.
    report_type can be 'mid' for mid-term or 'full' for full-term.
    exam_type can be 'MID_TERM' or 'FULL_TERM' to filter scores by exam type.
    """
    if isinstance(student, int):
        student = Student.objects.select_related("current_class_arm").get(pk=student)

    if isinstance(term, int):
        term = Term.objects.select_related("session").get(pk=term)

    #subjects = Subject.objects.filter(class_arms=student.current_class_arm).order_by("name")
    #if not subjects.exists():
        #subjects = Subject.objects.all().order_by("name")
    subjects = subjects_for_student(student)
    
    results_table = []
    total_scores_sum = Decimal("0.00")
    graded_count = 0

    results_table = []
    total_scores_sum = Decimal("0.00")
    graded_count = 0
 
    for subject in subjects:
        res = compute_subject_result(student, subject, term, exam_type)
 
        # Column display (weighted marks), matched by component name.
        ca1 = ca2 = exam = Decimal("0.00")
        for p in res["parts"]:
            name = p["name"].upper()
            if "1ST" in name or "1CA" in name or "CA1" in name:
                ca1 = p["earned"]
            elif "2ND" in name or "2CA" in name or "CA2" in name:
                ca2 = p["earned"]
            elif "EXAM" in name:
                exam = p["earned"]
 
        if res["has_scores"]:
            total_scores_sum += res["total_score"]
            graded_count += 1
 
        results_table.append({
            "subject": subject.name,
            "ca1": ca1,
            "ca2": ca2,
            "exam": exam,
            "total_score": res["total_score"],
            "grade_letter": res["grade_letter"],
            "remark": res["remark"],
            "parts": res["parts"],
            "teacher": subject_teacher_name(student.current_class_arm, subject),
        })
        
    overall_average = (
        (total_scores_sum / Decimal(graded_count)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if graded_count > 0
        else Decimal("0.00")
    )

    school_name = getattr(settings, 'SCHOOL_NAME', 'Aquila British International School')
    school_motto = getattr(settings, 'SCHOOL_MOTTO', 'Excellence in Knowledge and Character')
    skill_ratings = (
    StudentSkillRating.objects
        .filter(student=student, term=term, skill__is_active=True)
        .select_related("skill")
    )
    
    arm = student.current_class_arm
    show_position = arm.show_position if arm else True
    if show_position:
        position, total_students = class_position_info(student, term, exam_type)
    else:
        position = None
        total_students = Student.objects.filter(current_class_arm=arm).count()

    return {
        "student": student,
        "term": term,
        "results_table": results_table,
        "overall_average": overall_average,
        "logo_cid": logo_cid,
        "logo_url": logo_url,
        "school_name": school_name,
        "school_motto": school_motto,
        "report_type": report_type,
        "exam_type": exam_type,
        "skill_ratings": skill_ratings,
        "out_of": out_of_for(term, exam_type),
        "grading_scale": list(
            GradingScale.objects.filter(exam_type=exam_type).order_by("-min_score")
        ),
        "position": position,
        "show_position": show_position,
        "total_students": total_students,
    
    }


def send_result_email(student, term) -> bool:
    """
    Generates a student's term result PDF and emails it to the guardian with an embedded logo.
    Returns True if sent successfully, False otherwise.
    """
    if isinstance(student, int):
        try:
            student = Student.objects.get(pk=student)
        except Student.DoesNotExist:
            logger.warning(f"Failed to send result email: Student ID {student} not found.")
            return False

    if isinstance(term, int):
        try:
            term = Term.objects.select_related("session").get(pk=term)
        except Term.DoesNotExist:
            logger.warning(f"Failed to send result email: Term ID {term} not found.")
            return False

    guardian_email = getattr(student, 'guardian_email', None)
    if not guardian_email:
        logger.warning(f"Failed to send result email: Student ID {student.id} ({student}) has no guardian_email.")
        return False

    try:
        school_name = getattr(settings, 'SCHOOL_NAME', 'Aquila British International School')
        student_display = student.full_name
        subject = f"[{school_name}] Term Result - {student_display}"
        
        logo_cid = "school_logo_cid"
        context = build_report_card_context(student, term, logo_cid=logo_cid)
        
        # Render HTML content for email body and PDF attachment
        html_content = render_to_string('academics/report_card.html', context)
        
        # Generate PDF in-memory
        pdf_bytes = render_html_to_pdf(html_content)

        # Build email message
        text_content = f"Dear Parent/Guardian,\n\nPlease find attached the term result for {student_display} for {term.name}.\n\nBest regards,\n{school_name}"
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[guardian_email]
        )
        email.attach_alternative(html_content, "text/html")

        # Attach PDF
        admission_num = getattr(student, 'admission_number', student.id)
        pdf_filename = f"Report_Card_{admission_num}_{term.name}.pdf"
        email.attach(pdf_filename, pdf_bytes, 'application/pdf')

        # Attach static/src/images/logo.jpg as inline CID
        logo_path = finders.find('src/images/logo.jpg')
        if logo_path and Path(logo_path).exists():
            with open(logo_path, 'rb') as img_f:
                logo_data = img_f.read()
                mime_image = MIMEImage(logo_data)
                mime_image.add_header('Content-ID', f'<{logo_cid}>')
                mime_image.add_header('Content-Disposition', 'inline', filename='logo.jpg')
                email.attach(mime_image)

        email.send(fail_silently=False)
        return True

    except Exception as e:
        logger.error(f"Error sending result email for student ID {getattr(student, 'id', student)}: {str(e)}", exc_info=True)
        return False