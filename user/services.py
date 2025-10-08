"""
User-related services and business logic
"""
from django.contrib.auth import authenticate
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import User, UserProfile, EmailVerificationCode, LoginAttempt
from .email_utils import send_verification_email
import logging

logger = logging.getLogger(__name__)


class UserService:
    """Service class for user-related operations"""
    
    @staticmethod
    def create_user_with_profile(user_data, profile_data=None):
        """Create a user with optional profile data"""
        with transaction.atomic():
            user = User.objects.create_user(**user_data)
            
            if profile_data:
                UserProfile.objects.create(user=user, **profile_data)
            
            return user
    
    @staticmethod
    def send_verification_code(email, code_type=EmailVerificationCode.CodeType.LOGIN, 
                             request=None):
        """Send verification code to email"""
        ip_address = None
        user_agent = ""
        
        if request:
            ip_address = UserService._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Check rate limiting
        recent_codes = EmailVerificationCode.objects.filter(
            email=email,
            code_type=code_type,
            created_at__gte=timezone.now() - timezone.timedelta(minutes=1)
        ).count()
        
        if recent_codes >= 3:
            raise ValidationError("Too many verification codes requested. Please wait.")
        
        # Generate and send code
        verification_code = EmailVerificationCode.generate_code(
            email=email,
            code_type=code_type,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Send email
        try:
            send_verification_email(email, verification_code.code, code_type)
            logger.info(f"Verification code sent to {email}")
            return verification_code
        except Exception as e:
            logger.error(f"Failed to send verification code to {email}: {str(e)}")
            raise ValidationError("Failed to send verification code")
    
    @staticmethod
    def verify_email_code(email, code, code_type=EmailVerificationCode.CodeType.LOGIN):
        """Verify email verification code"""
        try:
            verification_code = EmailVerificationCode.objects.get(
                email=email,
                code=code,
                code_type=code_type,
                is_used=False
            )
            
            if not verification_code.is_valid():
                raise ValidationError("Verification code has expired")
            
            verification_code.mark_used()
            return True
            
        except EmailVerificationCode.DoesNotExist:
            raise ValidationError("Invalid verification code")
    
    @staticmethod
    def authenticate_with_email_code(email, code, request=None):
        """Authenticate user with email verification code"""
        ip_address = UserService._get_client_ip(request) if request else None
        user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''
        
        try:
            # Verify the code
            UserService.verify_email_code(email, code)
            
            # Get or create user
            user, created = User.objects.get_or_create(
                email=email,
                defaults={'username': email.split('@')[0]}
            )
            
            if created:
                logger.info(f"New user created via email login: {email}")
            
            # Log successful attempt
            LoginAttempt.log_attempt(
                email=email,
                attempt_type=LoginAttempt.AttemptType.EMAIL_CODE,
                status=LoginAttempt.Status.SUCCESS,
                ip_address=ip_address or '0.0.0.0',
                user_agent=user_agent
            )
            
            return user
            
        except ValidationError as e:
            # Log failed attempt
            LoginAttempt.log_attempt(
                email=email,
                attempt_type=LoginAttempt.AttemptType.EMAIL_CODE,
                status=LoginAttempt.Status.FAILED,
                ip_address=ip_address or '0.0.0.0',
                user_agent=user_agent,
                failure_reason=str(e)
            )
            raise
    
    @staticmethod
    def authenticate_with_password(email, password, request=None):
        """Authenticate user with email and password"""
        ip_address = UserService._get_client_ip(request) if request else None
        user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''
        
        # Check for too many recent failures
        recent_failures = LoginAttempt.get_recent_failures(email, hours=1)
        if recent_failures >= 5:
            LoginAttempt.log_attempt(
                email=email,
                attempt_type=LoginAttempt.AttemptType.PASSWORD,
                status=LoginAttempt.Status.BLOCKED,
                ip_address=ip_address or '0.0.0.0',
                user_agent=user_agent,
                failure_reason="Too many failed attempts"
            )
            raise ValidationError("Account temporarily locked due to too many failed attempts")
        
        user = authenticate(username=email, password=password)
        
        if user:
            # Log successful attempt
            LoginAttempt.log_attempt(
                email=email,
                attempt_type=LoginAttempt.AttemptType.PASSWORD,
                status=LoginAttempt.Status.SUCCESS,
                ip_address=ip_address or '0.0.0.0',
                user_agent=user_agent
            )
            return user
        else:
            # Log failed attempt
            LoginAttempt.log_attempt(
                email=email,
                attempt_type=LoginAttempt.AttemptType.PASSWORD,
                status=LoginAttempt.Status.FAILED,
                ip_address=ip_address or '0.0.0.0',
                user_agent=user_agent,
                failure_reason="Invalid credentials"
            )
            raise ValidationError("Invalid email or password")
    
    @staticmethod
    def update_user_profile(user, profile_data):
        """Update or create user profile"""
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        for field, value in profile_data.items():
            setattr(profile, field, value)
        
        profile.save()
        return profile
    
    @staticmethod
    def verify_user_email(user):
        """Mark user's email as verified"""
        user.is_email_verified = True
        user.save(update_fields=['is_email_verified'])
        
        logger.info(f"Email verified for user: {user.email}")
    
    @staticmethod
    def can_user_book_international_flights(user):
        """Check if user can book international flights"""
        if not user.can_book_flights():
            return False, "Complete your profile to book flights"
        
        try:
            profile = user.profile
            if not profile.can_travel_internationally():
                return False, "Valid passport required for international flights"
        except UserProfile.DoesNotExist:
            return False, "Complete your travel profile"
        
        return True, "User can book international flights"
    
    @staticmethod
    def _get_client_ip(request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class UserAnalyticsService:
    """Service for user analytics and statistics"""
    
    @staticmethod
    def get_user_stats():
        """Get overall user statistics"""
        from django.db.models import Count, Q
        
        stats = User.objects.aggregate(
            total_users=Count('id'),
            verified_users=Count('id', filter=Q(is_email_verified=True)),
            premium_users=Count('id', filter=Q(role=User.Role.PREMIUM)),
            users_with_bookings=Count('id', filter=Q(orders__isnull=False))
        )
        
        return stats
    
    @staticmethod
    def get_login_stats(days=30):
        """Get login statistics for the past N days"""
        from django.db.models import Count
        
        since = timezone.now() - timezone.timedelta(days=days)
        
        stats = LoginAttempt.objects.filter(created_at__gte=since).aggregate(
            total_attempts=Count('id'),
            successful_logins=Count('id', filter=Q(status=LoginAttempt.Status.SUCCESS)),
            failed_attempts=Count('id', filter=Q(status=LoginAttempt.Status.FAILED)),
            blocked_attempts=Count('id', filter=Q(status=LoginAttempt.Status.BLOCKED))
        )
        
        return stats
    
    @staticmethod
    def get_top_users_by_bookings(limit=10):
        """Get users with most bookings"""
        from django.db.models import Count
        
        return User.objects.annotate(
            booking_count=Count('orders')
        ).filter(
            booking_count__gt=0
        ).order_by('-booking_count')[:limit]
