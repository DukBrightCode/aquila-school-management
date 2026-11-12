from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.academics.services.result_mailer import build_report_card_context
from apps.school_structure.models import AcademicSession, ClassArm, ClassLevel, Term
from apps.staff.models import Teacher
from apps.students.models import Student

User = get_user_model()


class PositionToggleTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user("admin1", password="x", role="ADMIN")
        t_user = User.objects.create_user("t1", password="x", role="TEACHER")
        o_user = User.objects.create_user("t2", password="x", role="TEACHER")
        self.teacher = Teacher.objects.create(user=t_user, staff_id="T1", date_employed="2020-01-01")
        self.other = Teacher.objects.create(user=o_user, staff_id="T2", date_employed="2020-01-01")

        level = ClassLevel.objects.create(name="JSS1", category="JSS", order=1)
        self.arm = ClassArm.objects.create(class_level=level, name="A")
        self.arm.class_teachers.add(self.teacher)
        self.arm_b = ClassArm.objects.create(class_level=level, name="B")
        self.arm_b.class_teachers.add(self.other)

        session = AcademicSession.objects.create(name="2026/2027")
        self.term = Term.objects.create(session=session, name="FIRST", is_current=True)
        self.student = Student.objects.create(
            first_name="Ada", last_name="Obi", gender="F",
            current_class_level=level, current_class_arm=self.arm, date_enrolled="2026-09-01")
        self.url = reverse("academics:toggle_class_position", args=[self.arm.id])

    def test_position_is_on_by_default(self):
        self.assertTrue(self.arm.show_position)

    def test_class_teacher_can_turn_off_and_on_for_their_class(self):
        self.client.login(username="t1", password="x")
        self.client.post(self.url)
        self.arm.refresh_from_db()
        self.assertFalse(self.arm.show_position)
        self.client.post(self.url)
        self.arm.refresh_from_db()
        self.assertTrue(self.arm.show_position)

    def test_other_class_teacher_cannot_change_it(self):
        self.client.login(username="t2", password="x")
        self.client.post(self.url)
        self.arm.refresh_from_db()
        self.assertTrue(self.arm.show_position)

    def test_admin_can_change_any_class(self):
        self.client.login(username="admin1", password="x")
        self.client.post(self.url)
        self.arm.refresh_from_db()
        self.assertFalse(self.arm.show_position)

    def test_get_request_does_nothing(self):
        self.client.login(username="t1", password="x")
        self.client.get(self.url)
        self.arm.refresh_from_db()
        self.assertTrue(self.arm.show_position)

    def test_report_hides_position_when_switched_off(self):
        self.arm.show_position = False
        self.arm.save()
        ctx = build_report_card_context(self.student.id, self.term.id, exam_type="MID_TERM")
        self.assertFalse(ctx["show_position"])
        self.assertIsNone(ctx["position"])
        self.assertEqual(ctx["total_students"], 1)     # the class size is still shown

    def test_report_calculates_position_when_switched_on(self):
        ctx = build_report_card_context(self.student.id, self.term.id, exam_type="MID_TERM")
        self.assertTrue(ctx["show_position"])
        self.assertEqual(ctx["position"], "N/A")        # no scores yet