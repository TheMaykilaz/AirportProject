from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, timedelta
from user.models import User, EmailVerificationCode, UserProfile, LoginAttempt


class UserModelTest(TestCase):
    """Test User model"""

    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'date_of_birth': date(1990, 1, 1)
        }

    def test_create_user(self):
        """Test creating a regular user"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(user.role, User.Role.USER)

    def test_create_superuser(self):
        """Test creating a superuser"""
        user = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User'
        )
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_user_full_name(self):
        """Test full_name property"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.full_name, 'Test User')

    def test_user_age_calculation(self):
        """Test age property"""
        user = User.objects.create_user(**self.user_data)
        expected_age = (date.today() - date(1990, 1, 1)).days // 365
        self.assertEqual(user.age, expected_age)

    def test_user_age_none_without_dob(self):
        """Test age is None when date_of_birth not set"""
        data = self.user_data.copy()
        data.pop('date_of_birth')
        user = User.objects.create_user(**data)
        self.assertIsNone(user.age)

    def test_can_book_flights_with_required_info(self):
        """Test can_book_flights returns True with all required info"""
        user = User.objects.create_user(**self.user_data)
        user.is_email_verified = True
        user.save()
        self.assertTrue(user.can_book_flights())

    def test_cannot_book_flights_without_verification(self):
        """Test can_book_flights returns False without email verification"""
        user = User.objects.create_user(**self.user_data)
        self.assertFalse(user.can_book_flights())


class EmailVerificationCodeTest(TestCase):
    """Test EmailVerificationCode model"""

    def test_generate_code(self):
        """Test generating a verification code"""
        code_obj = EmailVerificationCode.generate_code(
            email='test@example.com',
            code_type=EmailVerificationCode.CodeType.LOGIN
        )
        self.assertEqual(len(code_obj.code), 6)
        self.assertTrue(code_obj.code.isdigit())
        self.assertFalse(code_obj.is_used)

    def test_code_is_valid(self):
        """Test code validity check"""
        code_obj = EmailVerificationCode.generate_code('test@example.com')
        self.assertTrue(code_obj.is_valid())

    def test_expired_code_is_invalid(self):
        """Test expired code is invalid"""
        code_obj = EmailVerificationCode.generate_code(
            email='test@example.com',
            expiry_minutes=-1  # Already expired
        )
        self.assertFalse(code_obj.is_valid())

    def test_mark_code_as_used(self):
        """Test marking code as used"""
        code_obj = EmailVerificationCode.generate_code('test@example.com')
        code_obj.mark_used()
        self.assertTrue(code_obj.is_used)
        self.assertFalse(code_obj.is_valid())


class UserProfileTest(TestCase):
    """Test UserProfile model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

    def test_create_user_profile(self):
        """Test creating a user profile"""
        profile = UserProfile.objects.create(
            user=self.user,
            passport_number='AB123456',
            passport_country='USA'
        )
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.passport_number, 'AB123456')

    def test_passport_validity(self):
        """Test passport validity check"""
        profile = UserProfile.objects.create(
            user=self.user,
            passport_number='AB123456',
            passport_expiry=date.today() + timedelta(days=365)
        )
        self.assertTrue(profile.is_passport_valid)

    def test_expired_passport_is_invalid(self):
        """Test expired passport is invalid"""
        profile = UserProfile.objects.create(
            user=self.user,
            passport_number='AB123456',
            passport_expiry=date.today() - timedelta(days=1)
        )
        self.assertFalse(profile.is_passport_valid)


class LoginAttemptTest(TestCase):
    """Test LoginAttempt model"""

    def test_log_successful_attempt(self):
        """Test logging a successful login attempt"""
        attempt = LoginAttempt.log_attempt(
            email='test@example.com',
            attempt_type=LoginAttempt.AttemptType.PASSWORD,
            status=LoginAttempt.Status.SUCCESS,
            ip_address='127.0.0.1'
        )
        self.assertEqual(attempt.status, LoginAttempt.Status.SUCCESS)
        self.assertEqual(attempt.email, 'test@example.com')

    def test_get_recent_failures(self):
        """Test getting recent failed attempts"""
        email = 'test@example.com'
        # Create 3 failed attempts
        for _ in range(3):
            LoginAttempt.log_attempt(
                email=email,
                attempt_type=LoginAttempt.AttemptType.PASSWORD,
                status=LoginAttempt.Status.FAILED,
                ip_address='127.0.0.1'
            )
        
        failures = LoginAttempt.get_recent_failures(email, hours=1)
        self.assertEqual(failures, 3)
