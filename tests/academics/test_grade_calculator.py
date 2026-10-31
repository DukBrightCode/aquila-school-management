from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.academics.models import AssessmentType, GradingScale, Score
from apps.academics.services.grade_calculator import (
    AssessmentConfigurationError,
    calculate_term_result,
)


class GradeCalculatorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # These tests intentionally use the project's expected model relationships.
        from apps.accounts.models import User
        from apps.school_structure.models import AcademicSession, ClassArm, ClassLevel, Subject, Term
        from apps.staff.models import Teacher
        from apps.students.models import Student

        cls.user = User.objects.create_user(username="student1", password="test-pass")
        cls.teacher_user = User.objects.create_user(username="teacher1", password="test-pass")
        cls.session = AcademicSession.objects.create(name="2026/2027")
        cls.term = Term.objects.create(name="First Term", academic_session=cls.session)
        cls.class_level = ClassLevel.objects.create(name="Year 7")
        cls.class_arm = ClassArm.objects.create(name="A", class_level=cls.class_level)
        cls.subject = Subject.objects.create(name="Mathematics")
        cls.student = Student.objects.create(user=cls.user, current_class_level=cls.class_level, current_class_arm=cls.class_arm)
        cls.teacher = Teacher.objects.create(user=cls.teacher_user)
        cls.grading = GradingScale.objects.create(min_score=0, max_score=100, grade_letter="A1", remark="Excellent")

    def make_config(self, **weights):
        return [
            AssessmentType.objects.create(
                term=self.term,
                name=name,
                max_score=Decimal(str(max_score)),
                weight_percentage=Decimal(str(weight)),
            )
            for name, (max_score, weight) in weights.items()
        ]

    def test_admin_configured_max_scores_and_weights_drive_result(self):
        assessments = self.make_config(
            Project=(20, 20),
            Continuous_Assessment=(30, 30),
            Final_Exam=(50, 50),
        )
        values = [Decimal("10"), Decimal("24"), Decimal("40")]
        for assessment, value in zip(assessments, values):
            Score.objects.create(
                student=self.student,
                subject=self.subject,
                class_arm=self.class_arm,
                term=self.term,
                assessment_type=assessment,
                score_value=value,
                entered_by=self.teacher,
            )

        result = calculate_term_result(self.student, self.subject, self.term)
        self.assertEqual(result["total_score"], Decimal("74.00"))
        self.assertEqual(result["grade_letter"], "A1")

    def test_changing_weight_changes_result_without_code_change(self):
        assessments = self.make_config(
            Test=(10, 50),
            Final_Exam=(100, 50),
        )
        Score.objects.create(student=self.student, subject=self.subject, class_arm=self.class_arm, term=self.term, assessment_type=assessments[0], score_value=10, entered_by=self.teacher)
        Score.objects.create(student=self.student, subject=self.subject, class_arm=self.class_arm, term=self.term, assessment_type=assessments[1], score_value=50, entered_by=self.teacher)
        self.assertEqual(calculate_term_result(self.student, self.subject, self.term)["total_score"], Decimal("75.00"))

        assessments[0].weight_percentage = Decimal("20")
        assessments[1].weight_percentage = Decimal("80")
        assessments[0].save(update_fields=["weight_percentage"])
        assessments[1].save(update_fields=["weight_percentage"])
        self.assertEqual(calculate_term_result(self.student, self.subject, self.term)["total_score"], Decimal("58.00"))

    def test_non_100_active_weights_are_rejected_at_calculation(self):
        self.make_config(Test=(20, 20), Exam=(80, 70))
        with self.assertRaises(AssessmentConfigurationError):
            calculate_term_result(self.student, self.subject, self.term)

    def test_arbitrary_assessment_names_are_supported(self):
        assessments = self.make_config(
            Practical=(25, 25),
            Assignment=(25, 25),
            Mid_Term=(50, 50),
        )
        for assessment in assessments:
            Score.objects.create(
                student=self.student,
                subject=self.subject,
                class_arm=self.class_arm,
                term=self.term,
                assessment_type=assessment,
                score_value=assessment.max_score,
                entered_by=self.teacher,
            )
        self.assertEqual(calculate_term_result(self.student, self.subject, self.term)["total_score"], Decimal("100.00"))

    def test_score_cannot_exceed_configured_maximum(self):
        assessment = self.make_config(Project=(20, 100))[0]
        score = Score(
            student=self.student,
            subject=self.subject,
            class_arm=self.class_arm,
            term=self.term,
            assessment_type=assessment,
            score_value=Decimal("21"),
            entered_by=self.teacher,
        )
        with self.assertRaises(ValidationError):
            score.full_clean()
