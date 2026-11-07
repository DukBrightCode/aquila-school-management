import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.academics.models import AssessmentType, ClassSubjectTeacher, Score
from apps.school_structure.models import AcademicSession, ClassArm, ClassLevel, Subject, Term
from apps.staff.models import Teacher
from apps.students.models import Student

User = get_user_model()


class ScoreEntryPermissionTests(TestCase):
    def setUp(self):
        lead_u = User.objects.create_user("lead", password="x", role="TEACHER")
        sub_u = User.objects.create_user("sub", password="x", role="TEACHER")
        self.lead = Teacher.objects.create(user=lead_u, staff_id="T1", date_employed="2020-01-01")
        self.sub = Teacher.objects.create(user=sub_u, staff_id="T2", date_employed="2020-01-01")

        level = ClassLevel.objects.create(name="JSS1", category="JSS", order=1)
        self.arm_a = ClassArm.objects.create(class_level=level, name="A")
        self.arm_b = ClassArm.objects.create(class_level=level, name="B")
        self.arm_a.class_teachers.add(self.lead)

        self.maths = Subject.objects.create(name="Mathematics", code="MTH")
        self.english = Subject.objects.create(name="English", code="ENG")
        for s in (self.maths, self.english):
            self.arm_a.subjects.add(s)
            self.arm_b.subjects.add(s)
        ClassSubjectTeacher.objects.create(class_arm=self.arm_a, subject=self.maths, teacher=self.sub)

        session = AcademicSession.objects.create(name="2026/2027")
        self.term = Term.objects.create(session=session, name="FIRST", is_current=True)
        self.ca1 = AssessmentType.objects.create(
            term=self.term, name="1st CA", max_score=5, weight_percentage=5, exam_type="MID_TERM")
        self.full_exam = AssessmentType.objects.create(
            term=self.term, name="EXAM", max_score=70, weight_percentage=70, exam_type="FULL_TERM")

        self.s_a = Student.objects.create(
            first_name="Ada", last_name="Obi", gender="F",
            current_class_level=level, current_class_arm=self.arm_a, date_enrolled="2026-09-01")
        self.s_b = Student.objects.create(
            first_name="Ben", last_name="Eze", gender="M",
            current_class_level=level, current_class_arm=self.arm_b, date_enrolled="2026-09-01")

        self.save_url = reverse("academics:score_entry_save")
        self.subjects_url = reverse("academics:get_class_subjects")

    def save(self, arm, subject, rows, exam_type="MID_TERM"):
        payload = {
            "class_arm_id": arm.id, "subject_id": subject.id,
            "term_id": self.term.id, "exam_type": exam_type, "rows": rows,
        }
        return self.client.post(self.save_url, json.dumps(payload), content_type="application/json")

    def row(self, student, at, value):
        return {"student_id": student.id, "scores": {str(at.id): value}}

    def test_subject_teacher_saves_own_subject(self):
        self.client.login(username="sub", password="x")
        r = self.save(self.arm_a, self.maths, [self.row(self.s_a, self.ca1, 4)])
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Score.objects.get(student=self.s_a).score_value, 4)

    def test_subject_teacher_cannot_save_other_subject(self):
        self.client.login(username="sub", password="x")
        r = self.save(self.arm_a, self.english, [self.row(self.s_a, self.ca1, 4)])
        self.assertEqual(r.status_code, 403)
        self.assertFalse(Score.objects.exists())

    def test_subject_teacher_cannot_save_in_a_class_they_are_not_assigned_to(self):
        self.client.login(username="sub", password="x")
        r = self.save(self.arm_b, self.maths, [self.row(self.s_b, self.ca1, 4)])
        self.assertEqual(r.status_code, 403)

    def test_class_teacher_can_save_any_offered_subject(self):
        self.client.login(username="lead", password="x")
        r = self.save(self.arm_a, self.english, [self.row(self.s_a, self.ca1, 3)])
        self.assertEqual(r.status_code, 200)

    def test_subject_list_only_shows_own_subjects_for_subject_teacher(self):
        self.client.login(username="sub", password="x")
        names = [s["name"] for s in self.client.get(self.subjects_url, {"class_arm": self.arm_a.id}).json()["subjects"]]
        self.assertEqual(names, ["Mathematics"])

    def test_class_teacher_sees_all_offered_subjects(self):
        self.client.login(username="lead", password="x")
        names = [s["name"] for s in self.client.get(self.subjects_url, {"class_arm": self.arm_a.id}).json()["subjects"]]
        self.assertEqual(names, ["English", "Mathematics"])

    def test_score_above_maximum_is_rejected_and_nothing_saved(self):
        self.client.login(username="sub", password="x")
        r = self.save(self.arm_a, self.maths, [self.row(self.s_a, self.ca1, 9)])
        self.assertEqual(r.status_code, 400)
        self.assertFalse(Score.objects.exists())

    def test_student_from_another_class_is_rejected(self):
        self.client.login(username="sub", password="x")
        r = self.save(self.arm_a, self.maths, [self.row(self.s_b, self.ca1, 4)])
        self.assertEqual(r.status_code, 400)
        self.assertFalse(Score.objects.exists())

    def test_column_from_the_other_exam_type_is_rejected(self):
        self.client.login(username="sub", password="x")
        r = self.save(self.arm_a, self.maths, [self.row(self.s_a, self.full_exam, 10)])  # MID_TERM save, FULL_TERM column
        self.assertEqual(r.status_code, 400)
        self.assertFalse(Score.objects.exists())

    def test_save_uses_the_same_number_of_queries_however_many_students(self):
        """Guards the bulk save: query count must not grow with the size of the class."""
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        extra = [
            Student.objects.create(
                first_name=f"S{i}", last_name="Extra", gender="M",
                current_class_level=self.arm_a.class_level, current_class_arm=self.arm_a,
                date_enrolled="2026-09-01")
            for i in range(20)
        ]
        self.client.login(username="sub", password="x")

        with CaptureQueriesContext(connection) as one_student:
            self.save(self.arm_a, self.maths, [self.row(self.s_a, self.ca1, 4)])
        Score.objects.all().delete()

        rows = [self.row(s, self.ca1, 3) for s in [self.s_a] + extra]
        with CaptureQueriesContext(connection) as whole_class:
            response = self.save(self.arm_a, self.maths, rows)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Score.objects.count(), 21)
        self.assertEqual(len(one_student), len(whole_class))