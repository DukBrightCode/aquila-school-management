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


class ElectiveTests(TestCase):
    def setUp(self):
        user = User.objects.create_user("lead", password="x", role="TEACHER")
        other_user = User.objects.create_user("other", password="x", role="TEACHER")
        self.teacher = Teacher.objects.create(user=user, staff_id="T1", date_employed="2020-01-01")
        self.other = Teacher.objects.create(user=other_user, staff_id="T2", date_employed="2020-01-01")

        level = ClassLevel.objects.create(name="SS1", category="SSS", order=10)
        self.arm = ClassArm.objects.create(class_level=level, name="A")
        self.arm.class_teachers.add(self.teacher)
        self.arm_b = ClassArm.objects.create(class_level=level, name="B")
        self.arm_b.class_teachers.add(self.other)

        self.science = Stream.objects.create(name="Science")
        self.commercial = Stream.objects.create(name="Commercial")

        self.english = Subject.objects.create(name="English", code="ENG")                 # core
        self.biology = Subject.objects.create(name="Biology", code="BIO")
        self.economics = Subject.objects.create(name="Economics", code="ECO")
        self.fashion = Subject.objects.create(name="Fashion Design", code="FSH", is_elective=True)
        self.irs = Subject.objects.create(name="IRS", code="IRS", is_elective=True)
        self.biology.streams.add(self.science)
        self.economics.streams.add(self.commercial)
        for s in (self.english, self.biology, self.economics, self.fashion):
            self.arm.subjects.add(s)                    # note: the class does NOT offer IRS

        def make(first, stream):
            return Student.objects.create(
                first_name=first, last_name="X", gender="M", current_class_level=level,
                current_class_arm=self.arm, stream=stream, date_enrolled="2026-09-01")

        self.sci = make("Sci", self.science)
        self.com = make("Com", self.commercial)

        session = AcademicSession.objects.create(name="2026/2027")
        self.term = Term.objects.create(session=session, name="FIRST", is_current=True)
        self.ca = AssessmentType.objects.create(
            term=self.term, name="CA", max_score=20, weight_percentage=20, exam_type="MID_TERM")

    def names(self, student):
        return set(subjects_for_student(student).values_list("name", flat=True))

    # ---- subject lists
    def test_nobody_gets_an_elective_by_default(self):
        self.assertEqual(self.names(self.sci), {"English", "Biology"})
        self.assertEqual(self.names(self.com), {"English", "Economics"})

    def test_a_chosen_elective_is_added_for_that_student_only(self):
        self.sci.elective_subjects.add(self.fashion)
        self.assertEqual(self.names(self.sci), {"English", "Biology", "Fashion Design"})
        self.assertEqual(self.names(self.com), {"English", "Economics"})

    def test_an_elective_the_class_does_not_offer_is_ignored(self):
        self.sci.elective_subjects.add(self.irs)
        self.assertNotIn("IRS", self.names(self.sci))

    # ---- score entry
    def test_only_students_who_chose_an_elective_are_listed_for_it(self):
        self.com.elective_subjects.add(self.fashion)
        ids = set(students_taking(self.arm.id, self.fashion).values_list("id", flat=True))
        self.assertEqual(ids, {self.com.id})

    def test_core_subject_listing_is_unchanged(self):
        ids = set(students_taking(self.arm.id, self.english).values_list("id", flat=True))
        self.assertEqual(ids, {self.sci.id, self.com.id})

    # ---- class position
    def test_position_counts_each_students_electives(self):
        self.sci.elective_subjects.add(self.fashion)

        def score(student, subject, value):
            Score.objects.create(student=student, subject=subject, class_arm=self.arm,
                                 term=self.term, assessment_type=self.ca,
                                 exam_type="MID_TERM", score_value=value)
        score(self.sci, self.biology, 10)
        score(self.sci, self.fashion, 20)       # science student averages 15
        score(self.com, self.economics, 20)     # commercial student averages 20
        self.assertEqual(class_position_info(self.com, self.term, "MID_TERM")[0], "1st")
        self.assertEqual(class_position_info(self.sci, self.term, "MID_TERM")[0], "2nd")

    # ---- the class teacher's page
    def post(self, arm, data):
        payload = {"arm": arm.id}
        payload.update(data)
        return self.client.post(reverse("academics:class_electives"), payload)

    def test_class_teacher_gives_and_removes_an_elective(self):
        self.client.login(username="lead", password="x")
        self.post(self.arm, {f"row_{self.sci.id}": "1", f"e_{self.sci.id}": [str(self.fashion.id)]})
        self.assertEqual(set(self.sci.elective_subjects.all()), {self.fashion})
        self.post(self.arm, {f"row_{self.sci.id}": "1"})                     # unticked
        self.assertFalse(self.sci.elective_subjects.exists())

    def test_a_subject_the_class_does_not_offer_cannot_be_ticked(self):
        self.client.login(username="lead", password="x")
        self.post(self.arm, {f"row_{self.sci.id}": "1", f"e_{self.sci.id}": [str(self.irs.id)]})
        self.assertFalse(self.sci.elective_subjects.exists())

    def test_another_classes_teacher_cannot_change_these_students(self):
        self.client.login(username="other", password="x")
        self.post(self.arm, {f"row_{self.sci.id}": "1", f"e_{self.sci.id}": [str(self.fashion.id)]})
        self.assertFalse(self.sci.elective_subjects.exists())

    def test_a_row_that_is_not_on_the_page_is_left_alone(self):
        self.sci.elective_subjects.add(self.fashion)
        self.client.login(username="lead", password="x")
        self.post(self.arm, {f"row_{self.com.id}": "1"})                     # sci's row not sent
        self.assertEqual(set(self.sci.elective_subjects.all()), {self.fashion})