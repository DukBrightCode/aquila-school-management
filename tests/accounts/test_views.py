from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class AccountsViewTests(TestCase):
    """Test suite for authentication, role assignments, and access control decorators/mixins."""

    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_user(username='admin_test', password='SecurePassword123!', role='ADMIN')
        self.student_user = User.objects.create_user(username='student_test', password='SecurePassword123!', role='STUDENT')

    def test_login_page_renders_successfully(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')

    def test_valid_user_login_redirects_to_dashboard_router(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'admin_test',
            'password': 'SecurePassword123!'
        })
        self.assertEqual(response.status_code, 302)
        # Expect the post-login routing view instead of a hardcoded target URL
        self.assertRedirects(response, reverse('dashboard:redirect'), fetch_redirect_response=False)

    def test_role_required_access_control_denial(self):
        # Authenticate as a student and attempt to access administrative endpoints
        self.client.login(username='student_test', password='SecurePassword123!')
        response = self.client.get(reverse('dashboard:admin'))
        self.assertIn(response.status_code, [302, 403])