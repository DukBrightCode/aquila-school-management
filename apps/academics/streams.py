
from django.db.models import Q

from apps.school_structure.models import Subject
from apps.students.models import Student


def arm_subjects(arm):
    """Subjects the class offers (every subject if none are set, as the report did before)."""
    if arm is None:
        return Subject.objects.all()
    subjects = Subject.objects.filter(class_arms=arm)
    if not subjects.exists():
        subjects = Subject.objects.all()
    return subjects


def filter_by_stream(subjects, stream_id):
    if stream_id is None:
        return subjects
    return subjects.filter(Q(streams__isnull=True) | Q(streams__id=stream_id)).distinct()


def subjects_for_student(student):
    """The subjects that appear on this student's report card."""
    return filter_by_stream(arm_subjects(student.current_class_arm), student.stream_id).order_by("name")


def students_taking(arm_id, subject):
    """Students of the class who take this subject (used by score entry)."""
    students = Student.objects.filter(current_class_arm_id=arm_id)
    stream_ids = list(subject.streams.values_list("id", flat=True))
    if stream_ids:
        students = students.filter(Q(stream__isnull=True) | Q(stream_id__in=stream_ids))
    return students