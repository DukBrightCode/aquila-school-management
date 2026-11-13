"""
Who takes which subject. apps/academics/streams.py  (replaces the earlier version)

A student's subjects are:
  1. the class's CORE subjects: not elective, and either in no stream or in the student's stream
     (a student with no stream set takes every non-elective subject the class offers)
  2. plus the ELECTIVE subjects (is_elective) that the student has been given.
Electives are never given by default.
"""
from collections import defaultdict

from django.db.models import Q

from apps.school_structure.models import Subject
from apps.students.models import Student

StudentElective = Student.elective_subjects.through


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
    offered = arm_subjects(student.current_class_arm)
    regular = filter_by_stream(offered.filter(is_elective=False), student.stream_id)
    chosen = offered.filter(is_elective=True, id__in=student.elective_subjects.values("id"))
    return Subject.objects.filter(
        Q(pk__in=regular.values("pk")) | Q(pk__in=chosen.values("pk"))
    ).order_by("name")


def students_taking(arm_id, subject):
    """Students of the class who take this subject (used by score entry)."""
    students = Student.objects.filter(current_class_arm_id=arm_id)
    if subject.is_elective:
        return students.filter(elective_subjects=subject)
    stream_ids = list(subject.streams.values_list("id", flat=True))
    if stream_ids:
        students = students.filter(Q(stream__isnull=True) | Q(stream_id__in=stream_ids))
    return students


def allowed_subject_ids_by_student(arm):
    """{student_id: set of subject ids that student takes}: used for class position."""
    students = list(Student.objects.filter(current_class_arm_id=arm.id).values_list("id", "stream_id"))
    offered = arm_subjects(arm)

    regular = offered.filter(is_elective=False)
    by_stream = {
        stream_id: set(filter_by_stream(regular, stream_id).values_list("id", flat=True))
        for stream_id in {stream_id for _, stream_id in students}
    }

    elective_ids = set(offered.filter(is_elective=True).values_list("id", flat=True))
    chosen = defaultdict(set)
    rows = StudentElective.objects.filter(student_id__in=[sid for sid, _ in students]).values_list(
        "student_id", "subject_id"
    )
    for student_id, subject_id in rows:
        if subject_id in elective_ids:
            chosen[student_id].add(subject_id)

    return {sid: by_stream[stream_id] | chosen[sid] for sid, stream_id in students}