from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict
from apps.academics.models import AssessmentType, GradingScale, Score, ClassSubjectTeacher

from apps.students.models import Student
TWO_PLACES = Decimal("0.01")


def components_for(term, exam_type):
    """Active assessment components that belong to this exam type for the term."""
    return AssessmentType.objects.filter(
        term=term, is_active=True, exam_type=exam_type
    ).order_by("id")


def out_of_for(term, exam_type):
    return sum((a.weight_percentage for a in components_for(term, exam_type)), Decimal("0"))


def grade_for(total, exam_type):
    # Highest grade whose minimum the total reaches: tolerant of gaps/overlaps.
    return (
        GradingScale.objects.filter(exam_type=exam_type, min_score__lte=total)
        .order_by("-min_score")
        .first()
    )


def compute_subject_result(student, subject, term, exam_type=Score.ExamType.FULL_TERM):
    """
    Returns {total_score, out_of, has_scores, parts[], grade_letter, remark}.
    Each part's contribution = raw / max_score * weight.
    """
    types = list(components_for(term, exam_type))
    scores = {
        s.assessment_type_id: s.score_value
        for s in Score.objects.filter(
            student=student, subject=subject, term=term,
            exam_type=exam_type, assessment_type__in=types,
        )
    }

    total = Decimal("0")
    out_of = Decimal("0")
    parts = []
    for at in types:
        out_of += at.weight_percentage
        raw = scores.get(at.id)
        earned = Decimal("0")
        if raw is not None:
            earned = Decimal(raw) / at.max_score * at.weight_percentage
        total += earned
        parts.append({
            "name": at.name,
            "raw": raw,
            "max": at.max_score,
            "weight": at.weight_percentage,
            "earned": earned.quantize(TWO_PLACES, rounding=ROUND_HALF_UP),
        })

    total = total.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    grade = grade_for(total, exam_type) if scores else None
    return {
        "total_score": total,
        "out_of": out_of,
        "has_scores": bool(scores),
        "parts": parts,
        "grade_letter": grade.grade_letter if grade else "-",
        "remark": grade.remark if grade else "-",
    }

def _teacher_label(teacher):
    user = getattr(teacher, "user", teacher)
    return user.get_full_name() or user.username


def subject_teacher_name(arm, subject):
    """Name of the teacher for this subject in this arm ('' if unknown)."""
    if arm is None:
        return ""

    assignment = (
        ClassSubjectTeacher.objects.filter(class_arm=arm, subject=subject)
        .select_related("teacher__user")
        .first()
    )
    if assignment and assignment.display_name:
        return assignment.display_name

    # Fallback: the timetable, if it records a teacher for this class and subject.
    try:
        from apps.timetable.models import TimetableSlot
        slot = (
            TimetableSlot.objects.filter(
                class_arm=arm, subject=subject, teacher__isnull=False
            )
            .select_related("teacher__user")
            .first()
        )
        if slot:
            return _teacher_label(slot.teacher)
    except Exception:
        pass
    return ""

def ordinal(n):
    """1 -> 1st, 2 -> 2nd, 3 -> 3rd, 11 -> 11th, 22 -> 22nd ..."""
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"
 
def report_components(term, exam_type):
    """
    Components that make up a report for this exam type.
    Works with the module you have now: if your full-term total includes the
    mid-term marks, the mid-term components are included here too.
    """
    comps = list(components_for(term, exam_type))
    includes_mid_term = globals().get("_includes_mid_term")
    if includes_mid_term and includes_mid_term(exam_type):
        comps = list(components_for(term, Score.ExamType.MID_TERM)) + comps
    return comps
 
 
def class_position_info(student, term, exam_type, subject_ids=None):
    """
    Returns (position_text, total_students) for a student's class arm.
 
    position_text is like "3rd", or "N/A" if the student has no scores or no class.
    Students are ranked by overall average (average of subject totals for the
    subjects that have scores), the same rule as the report's Overall Average.
    """
    arm_id = student.current_class_arm_id
    if not arm_id:
        return "N/A", 0
 
    student_ids = list(
        Student.objects.filter(current_class_arm_id=arm_id).values_list("id", flat=True)
    )
    total_students = len(student_ids)
 
    comps = report_components(term, exam_type)
    comp_by_id = {c.id: c for c in comps}
 
    scores = Score.objects.filter(
        student_id__in=student_ids, term=term, assessment_type__in=comps
    )
    if subject_ids is not None:
        scores = scores.filter(subject_id__in=subject_ids)
 
    # student -> subject -> total marks
    totals = defaultdict(lambda: defaultdict(Decimal))
    for sid, subject_id, at_id, value in scores.values_list(
        "student_id", "subject_id", "assessment_type_id", "score_value"
    ):
        comp = comp_by_id[at_id]
        totals[sid][subject_id] += Decimal(value) / comp.max_score * comp.weight_percentage
 
    averages = {}
    for sid, per_subject in totals.items():
        if per_subject:
            average = sum(per_subject.values()) / len(per_subject)
            averages[sid] = average.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
 
    if student.id not in averages:
        return "N/A", total_students
 
    mine = averages[student.id]
    position = 1 + sum(1 for other in averages.values() if other > mine)
    return ordinal(position), total_students
 