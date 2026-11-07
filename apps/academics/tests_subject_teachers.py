from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.academics.models import ClassSubjectTeacher
from apps.academics.permissions import score_entry_arms, scoreable_arms, scoreable_subjects
from apps.school_structure.models import ClassArm, ClassLevel, Subject
from apps.staff.models import Teacher

User = get_user_model()


class SubjectTeacherScoringTests(TestCase):
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
        self.physics = Subject.objects.create(name="Physics", code="PHY")
        for s in (self.maths, self.english, self.physics):
            self.arm_a.subjects.add(s)
            self.arm_b.subjects.add(s)

        # the subject teacher teaches Maths and English in A, and Maths in B
        ClassSubjectTeacher.objects.create(class_arm=self.arm_a, subject=self.maths, teacher=self.sub)
        ClassSubjectTeacher.objects.create(class_arm=self.arm_a, subject=self.english, teacher=self.sub)
        ClassSubjectTeacher.objects.create(class_arm=self.arm_b, subject=self.maths, teacher=self.sub)

    def test_subject_teacher_scores_only_assigned_subjects(self):
        self.assertEqual(set(scoreable_subjects(self.sub, self.arm_a)), {self.maths, self.english})
        self.assertEqual(set(scoreable_subjects(self.sub, self.arm_b)), {self.maths})

    def test_subject_teacher_arms_for_scoring_include_both_classes(self):
        self.assertEqual(set(score_entry_arms(self.sub)), {self.arm_a, self.arm_b})

    def test_subject_teacher_is_not_a_class_teacher(self):
        self.assertEqual(scoreable_arms(self.sub).count(), 0)   # no students, remarks, skills, reports

    def test_class_teacher_still_scores_every_subject(self):
        self.assertEqual(set(scoreable_subjects(self.lead, self.arm_a)),
                         {self.maths, self.english, self.physics})

    def test_unassigned_teacher_has_no_access(self):
        other_u = User.objects.create_user("x", password="x", role="TEACHER")
        other = Teacher.objects.create(user=other_u, staff_id="T3", date_employed="2020-01-01")
        self.assertEqual(score_entry_arms(other).count(), 0)
        self.assertFalse(scoreable_subjects(other, self.arm_a).exists())

    def test_assignment_to_a_subject_the_class_does_not_offer_gives_no_access(self):
        self.arm_a.subjects.remove(self.english)
        self.assertEqual(set(scoreable_subjects(self.sub, self.arm_a)), {self.maths})


class ClassTeacherWhoAlsoTeachesElsewhereTests(TestCase):
    """E.g. the class teacher of SS1 A who also teaches Maths/Physics in JSS classes."""

    def setUp(self):
        user = User.objects.create_user("mixed", password="x", role="TEACHER")
        self.teacher = Teacher.objects.create(user=user, staff_id="T9", date_employed="2020-01-01")

        ss = ClassLevel.objects.create(name="SS1", category="SSS", order=10)
        jss1 = ClassLevel.objects.create(name="JSS1", category="JSS", order=1)
        jss3 = ClassLevel.objects.create(name="JSS3", category="JSS", order=3)
        self.ss1a = ClassArm.objects.create(class_level=ss, name="A")
        self.jss1a = ClassArm.objects.create(class_level=jss1, name="A")
        self.jss3a = ClassArm.objects.create(class_level=jss3, name="A")
        self.ss1a.class_teachers.add(self.teacher)               # class teacher of SS1 A

        self.maths = Subject.objects.create(name="Mathematics", code="MTH")
        self.physics = Subject.objects.create(name="Physics", code="PHY")
        self.biology = Subject.objects.create(name="Biology", code="BIO")
        for arm in (self.ss1a, self.jss1a, self.jss3a):
            for s in (self.maths, self.physics, self.biology):
                arm.subjects.add(s)

        # subject teacher in other classes
        ClassSubjectTeacher.objects.create(class_arm=self.jss1a, subject=self.maths, teacher=self.teacher)
        ClassSubjectTeacher.objects.create(class_arm=self.jss3a, subject=self.maths, teacher=self.teacher)
        ClassSubjectTeacher.objects.create(class_arm=self.jss3a, subject=self.physics, teacher=self.teacher)

    def test_all_their_classes_appear_for_scoring(self):
        self.assertEqual(set(score_entry_arms(self.teacher)), {self.ss1a, self.jss1a, self.jss3a})

    def test_full_rights_in_the_class_they_lead(self):
        self.assertEqual(set(scoreable_subjects(self.teacher, self.ss1a)),
                         {self.maths, self.physics, self.biology})

    def test_only_assigned_subjects_in_other_classes(self):
        self.assertEqual(set(scoreable_subjects(self.teacher, self.jss1a)), {self.maths})
        self.assertEqual(set(scoreable_subjects(self.teacher, self.jss3a)), {self.maths, self.physics})

    def test_class_teacher_powers_stay_limited_to_the_class_they_lead(self):
        self.assertEqual(set(scoreable_arms(self.teacher)), {self.ss1a})