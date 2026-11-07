from django.db.models import Q

from apps.academics.models import ClassSubjectTeacher, ResultRelease
from apps.school_structure.models import ClassArm, Subject


def scoreable_arms(teacher):
    """
    Returns the class arms where the teacher is the class teacher.
    """
    return ClassArm.objects.filter(class_teachers=teacher).select_related("class_level")


def offered_subjects(arm):
    """
    Returns the subjects offered by a class arm.
    """
    return arm.subjects.all()


def scoreable_subjects(teacher, arm):
    """
    Subjects this teacher may enter scores for in a given arm.
      - a class teacher of the arm: every subject the arm offers
      - an assigned subject teacher: only the subjects assigned to them in that arm
    """
    if arm.class_teachers.filter(pk=teacher.pk).exists():
        return offered_subjects(arm)
    assigned = ClassSubjectTeacher.objects.filter(
        class_arm=arm, teacher=teacher
    ).values_list("subject_id", flat=True)
    return arm.subjects.filter(pk__in=assigned)


def score_entry_arms(teacher):
    """
    Arms where this teacher may enter scores: the arms they lead as class teacher,
    plus every arm where they are the assigned subject teacher for something.
    (Only used for score entry. Students, remarks, skills and reports stay with
    scoreable_arms, i.e. class teachers only.)
    """
    return (
        ClassArm.objects.filter(
            Q(class_teachers=teacher) | Q(subject_teachers__teacher=teacher)
        )
        .select_related("class_level")
        .distinct()
    )


# ---- Result access (report cards) ---------------------------------------------

def is_admin(user):
    return bool(user.is_superuser or getattr(user, "role", None) == "ADMIN")


def is_released(term_id, arm_id, exam_type):
    """True if the admin has released this class's results for the term and exam type."""
    return ResultRelease.objects.filter(
        term_id=term_id, class_arm_id=arm_id, exam_type=exam_type, is_released=True
    ).exists()


def class_access_error(user, arm_id, term_id, exam_type):
    """
    None if this user may see results for this class/term/exam, otherwise a message.
    Admins: always. Class teachers: only their own arm AND only once released.
    """
    if is_admin(user):
        return None
    teacher = getattr(user, "teacher_profile", None)
    if not teacher or not arm_id or not scoreable_arms(teacher).filter(id=arm_id).exists():
        return "Permission denied. You are not the class teacher for this class."
    if not is_released(term_id, arm_id, exam_type):
        return "These results have not been released yet. Please contact the admin."
    return None


def result_access_error(user, student, term_id, exam_type):
    """Same check, for one student (uses the student's current class arm)."""
    return class_access_error(user, student.current_class_arm_id, term_id, exam_type)