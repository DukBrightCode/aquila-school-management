import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.academics.models import AssessmentType, Score
from apps.academics.results import class_position_info
from apps.academics.streams import students_taking, subjects_for_student
from apps.school_structure.models import (
    AcademicSession, ClassArm, ClassLevel, Stream, Subject, Term,
)
from apps.staff.models import Teacher
from apps.students.models import Student

User = get_user_model()


class StreamTests(TestCase):
    def setUp(self):
        user = User.objects.create_user("lead", password="x", role="TEACHER")
        self.teacher = Teacher.objects.create(user=user, staff_id="T1", date_employed="2020-01-01")

        level = ClassLevel.objects.create(name="SS1", category="SSS", order=10)
        self.arm = ClassArm.objects.create(class_level=level, name="A")
        self.arm.class_teachers.add(self.teacher)

        self.science = Stream.objects.create(name="Science")
        self.art = Stream.objects.create(name="Art")
        self.commercial = Stream.objects.create(name="Commercial")

        self.english = Subject.objects.create(name="English", code="ENG")            # core
        self.biology = Subject.objects.create(name="Biology", code="BIO")
        self.history = Subject.objects.create(name="History", code="HIS")
        self.government = Subject.objects.create(name="Government", code="GOV")      # two streams
        self.biology.streams.add(self.science)
        self.history.streams.add(self.art)
        self.government.streams.add(self.art, self.commercial)
        for s in (self.english, self.biology, self.history, self.government):
            self.arm.subjects.add(s)

        def make(first, stream=None):
            return Student.objects.create(
                first_name=first, last_name="X", gender="M", current_class_level=level,
                current_class_arm=self.arm, stream=stream, date_enrolled="2026-09-01")

        self.sci = make("Sci", self.science)
        self.artist = make("Art", self.art)
        self.merchant = make("Com", self.commercial)
        self.unset = make("Unset", None)

        session = AcademicSession.objects.create(name="2026/2027")
        self.term = Term.objects.create(session=session, name="FIRST", is_current=True)
        self.ca = AssessmentType.objects.create(
            term=self.term, name="CA", max_score=20, weight_percentage=20, exam_type="MID_TERM")

    # ---- subject lists
    def names(self, qs):
        return set(qs.values_list("name", flat=True))

    def test_science_student_gets_core_and_science_subjects_only(self):
        self.assertEqual(self.names(subjects_for_student(self.sci)), {"English", "Biology"})

    def test_art_student(self):
        self.assertEqual(self.names(subjects_for_student(self.artist)), {"English", "History", "Government"})

    def test_subject_shared_by_two_streams_appears_for_both(self):
        self.assertIn("Government", self.names(subjects_for_student(self.artist)))
        self.assertIn("Government", self.names(subjects_for_student(self.merchant)))
        self.assertNotIn("Government", self.names(subjects_for_student(self.sci)))

    def test_student_with_no_stream_still_sees_every_subject(self):
        self.assertEqual(self.names(subjects_for_student(self.unset)),
                         {"English", "Biology", "History", "Government"})

    # ---- who is listed in score entry
    def test_only_students_who_take_a_subject_are_listed(self):
        ids = set(students_taking(self.arm.id, self.biology).values_list("id", flat=True))
        self.assertEqual(ids, {self.sci.id, self.unset.id})      # not art or commercial
        core_ids = set(students_taking(self.arm.id, self.english).values_list("id", flat=True))
        self.assertEqual(len(core_ids), 4)

    def test_save_rejects_a_student_who_does_not_take_the_subject(self):
        self.client.login(username="lead", password="x")
        payload = {
            "class_arm_id": self.arm.id, "subject_id": self.biology.id, "term_id": self.term.id,
            "exam_type": "MID_TERM",
            "rows": [{"student_id": self.artist.id, "scores": {str(self.ca.id): 10}}],
        }
        r = self.client.post(reverse("academics:score_entry_save"),
                             json.dumps(payload), content_type="application/json")
        self.assertEqual(r.status_code, 400)
        self.assertFalse(Score.objects.exists())

    # ---- class position uses each student's own subjects
    def test_position_compares_students_on_their_own_subjects(self):
        def score(student, subject, value):
            Score.objects.create(student=student, subject=subject, class_arm=self.arm,
                                 term=self.term, assessment_type=self.ca,
                                 exam_type="MID_TERM", score_value=value)
        score(self.sci, self.biology, 10)        # science student averages 10
        score(self.artist, self.history, 20)     # art student averages 20
        self.assertEqual(class_position_info(self.artist, self.term, "MID_TERM")[0], "1st")
        self.assertEqual(class_position_info(self.sci, self.term, "MID_TERM")[0], "2nd")