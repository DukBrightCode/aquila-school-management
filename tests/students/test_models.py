from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.students.models import Student
from apps.school_structure.models import ClassLevel, ClassArm

User = get_user_model()

class StudentModelTests(TestCase):
    """Test suite validating Student profile integrity and structural relationships."""

    def setUp(self):
        self.user = User.objects.create_user(username='johndoe', password='Password123!', role='STUDENT', first_name='John', last_name='Doe')
        self.class_level = ClassLevel.objects.create(name='Primary 3', category='PRIMARY', order=3)
        self.class_arm = ClassArm.objects.create(class_level=self.class_level, name='B')

    def test_student_creation_and_string_representation(self):
        student = Student.objects.create(
            user=self.user,
            admission_number='ABIS/2026/999',
            date_of_birth='2015-04-10',
            gender='M',
            current_class_level=self.class_level,
            current_class_arm=self.class_arm,
            guardian_name='Mr. Doe',
            guardian_phone='08098765432',
            address='Wuse Zone 4, Abuja'
        )
        self.assertEqual(str(student), f"John Doe (ABIS/2026/999)")
        self.assertEqual(student.current_class_level.category, 'PRIMARY')
        self.assertEqual(student.current_class_arm.name, 'B')