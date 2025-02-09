from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from core.models import Business, Customer
from .models import Service, Booking
from datetime import datetime, timedelta
from django.utils import timezone

# Create your tests here.

class BookingTests(TestCase):
    def setUp(self):
        # Create business
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
        
        # Create service
        self.service = Service.objects.create(
            business=self.business,
            name='Test Service',
            duration=60,
            price=100.00
        )
        
        self.client = Client()

    def test_booking_page_load(self):
        response = self.client.get(
            reverse('scheduler:booking_page', 
                   kwargs={'booking_url': self.business.booking_url})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.service.name)

    def test_get_available_slots(self):
        response = self.client.get(
            reverse('scheduler:get_slots', 
                   kwargs={'business_id': self.business.id}),
            {'date': '2024-03-20', 'service': self.service.id}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('slots', response.json())

    def test_create_booking(self):
        # Use timezone-aware datetime
        start_time = timezone.now().replace(
            hour=10, minute=0, second=0, microsecond=0
        ) + timedelta(days=1)  # Book for tomorrow
        
        response = self.client.post(
            reverse('scheduler:create_booking'),
            {
                'business': self.business.id,
                'service': self.service.id,
                'name': 'Test Customer',
                'email': 'customer@test.com',
                'phone': '1234567890',
                'date': start_time.date().isoformat(),
                'time': start_time.strftime('%H:%M')
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        
        # Verify booking was created
        self.assertTrue(
            Booking.objects.filter(
                customer__email='customer@test.com'
            ).exists()
        )

class IntegrationTests(TestCase):
    def setUp(self):
        # Setup business and service
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
        self.service = Service.objects.create(
            business=self.business,
            name='Test Service',
            duration=60,
            price=100.00
        )
        self.client = Client()

    def test_full_booking_flow(self):
        # 1. Load booking page
        response = self.client.get(
            reverse('scheduler:booking_page', 
                   kwargs={'booking_url': self.business.booking_url})
        )
        self.assertEqual(response.status_code, 200)

        # Use timezone-aware datetime
        booking_date = timezone.now().date() + timedelta(days=1)
        
        # 2. Get available slots
        response = self.client.get(
            reverse('scheduler:get_slots', 
                   kwargs={'business_id': self.business.id}),
            {'date': booking_date.isoformat(), 'service': self.service.id}
        )
        slots = response.json()['slots']
        self.assertTrue(len(slots) > 0)

        # 3. Create booking
        response = self.client.post(
            reverse('scheduler:create_booking'),
            {
                'business': self.business.id,
                'service': self.service.id,
                'name': 'Test Customer',
                'email': 'customer@test.com',
                'phone': '1234567890',
                'date': booking_date.isoformat(),
                'time': slots[0]
            }
        )
        self.assertTrue(response.json()['success'])

        # 4. Verify in dashboard
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('core:dashboard'))
        self.assertContains(response, 'Test Customer')
