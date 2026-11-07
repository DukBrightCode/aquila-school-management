from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.academics.models import PredefinedRemark, StudentReportRemark
from apps.school_structure.models import AcademicSession, ClassArm, ClassLevel, Term
from apps.staff.models import Teacher
from apps.students.models import Student

User = get_user_model()


class ClassRemarkTests(TestCase):
    def setUp(self):
        self.t_user = User.objects.create_user("t1", password="x", role="TEACHER")
        self.o_user = User.objects.create_user("t2", password="x", role="TEACHER")
        self.teacher = Teacher.objects.create(user=self.t_user, staff_id="T1", date_employed="2020-01-01")
        self.other = Teacher.objects.create(user=self.o_user, staff_id="T2", date_employed="2020-01-01")

        level = ClassLevel.objects.create(name="JSS1", category="JSS", order=1)
        self.arm = ClassArm.objects.create(class_level=level, name="A")
        self.arm.class_teachers.add(self.teacher)
        self.arm_b = ClassArm.objects.create(class_level=level, name="B")
        self.arm_b.class_teachers.add(self.other)

        session = AcademicSession.objects.create(name="2026/2027")
        self.term = Term.objects.create(session=session, name="FIRST", is_current=True)
        self.s1 = Student.objects.create(
            first_name="Ada", last_name="Obi", gender="F",
            current_class_level=level, current_class_arm=self.arm, date_enrolled="2026-09-01")
        self.s2 = Student.objects.create(
            first_name="Ben", last_name="Eze", gender="M",
            current_class_level=level, current_class_arm=self.arm_b, date_enrolled="2026-09-01")

        self.t_remark = PredefinedRemark.objects.create(type="TEACHER", text="Hard working.")
        self.p_remark = PredefinedRemark.objects.create(type="PRINCIPAL", text="Keep it up.")
        self.url = reverse("academics:class_remarks")

    def post(self, arm, data):
        payload = {"arm": arm.id, "term": self.term.id}
        payload.update(data)
        return self.client.post(self.url, payload)

    def test_class_teacher_saves_approved_remarks(self):
        self.client.login(username="t1", password="x")
        self.post(self.arm, {f"t_{self.s1.id}": str(self.t_remark.id),
                             f"p_{self.s1.id}": str(self.p_remark.id)})
        r = StudentReportRemark.objects.get(student=self.s1, term=self.term)
        self.assertEqual(r.teacher_remark, "Hard working.")
        self.assertEqual(r.principal_remark, "Keep it up.")

    def test_typed_text_is_rejected(self):
        self.client.login(username="t1", password="x")
        self.post(self.arm, {f"t_{self.s1.id}": "Something I typed myself"})
        self.assertFalse(StudentReportRemark.objects.filter(student=self.s1).exists())

    def test_teacher_remark_cannot_be_used_in_the_principal_box(self):
        self.client.login(username="t1", password="x")
        self.post(self.arm, {f"p_{self.s1.id}": str(self.t_remark.id)})
        self.assertFalse(StudentReportRemark.objects.filter(student=self.s1).exists())

    def test_teacher_cannot_write_remarks_for_another_class(self):
        self.client.login(username="t1", password="x")
        self.post(self.arm_b, {f"t_{self.s2.id}": str(self.t_remark.id)})
        self.assertFalse(StudentReportRemark.objects.filter(student=self.s2).exists())

    def test_blank_clears_missing_field_and_keep_leave_things_alone(self):
        self.client.login(username="t1", password="x")
        self.post(self.arm, {f"t_{self.s1.id}": str(self.t_remark.id),
                             f"p_{self.s1.id}": str(self.p_remark.id)})
        self.post(self.arm, {f"t_{self.s1.id}": ""})
        r = StudentReportRemark.objects.get(student=self.s1)
        self.assertIsNone(r.teacher_remark)
        self.assertEqual(r.principal_remark, "Keep it up.")
        self.post(self.arm, {f"p_{self.s1.id}": "keep"})
        self.assertEqual(StudentReportRemark.objects.get(student=self.s1).principal_remark, "Keep it up.")