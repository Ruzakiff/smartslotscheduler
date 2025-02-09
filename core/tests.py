from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Business

# Create your tests here.

class BusinessTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.business = Business.objects.create(
            owner=self.user,
            name='Test Business',
            email='test@business.com',
            phone='1234567890'
        )

    def test_business_creation(self):
        self.assertEqual(self.business.name, 'Test Business')
        self.assertEqual(self.business.booking_url, 'test-business')

    def test_business_signup(self):
        response = self.client.post(reverse('core:signup'), {
            'username': 'newbusiness',
            'password1': 'complex123',
            'password2': 'complex123',
            'business_name': 'New Business',
            'email': 'new@business.com',
            'phone': '0987654321'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after signup
        self.assertTrue(Business.objects.filter(name='New Business').exists())

    def test_dashboard_access(self):
        # Test unauthenticated
        response = self.client.get(reverse('core:dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

        # Test authenticated
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('core:dashboard'))
        self.assertEqual(response.status_code, 200)
