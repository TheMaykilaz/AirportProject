"""
Management command to clean up expired user data
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from user.models import EmailVerificationCode, LoginAttempt


class Command(BaseCommand):
    help = 'Clean up expired user data (verification codes, old login attempts)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to keep login attempts (default: 30)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        days = options['days']

        self.stdout.write(
            self.style.SUCCESS(f'Starting cleanup (dry_run={dry_run})...')
        )

        # Clean up expired verification codes
        expired_codes = EmailVerificationCode.objects.filter(
            expires_at__lt=timezone.now() - timezone.timedelta(hours=24)
        )
        codes_count = expired_codes.count()
        
        if not dry_run:
            EmailVerificationCode.cleanup_expired()
        
        self.stdout.write(
            f'{"Would delete" if dry_run else "Deleted"} {codes_count} expired verification codes'
        )

        # Clean up old login attempts
        old_attempts = LoginAttempt.objects.filter(
            created_at__lt=timezone.now() - timezone.timedelta(days=days)
        )
        attempts_count = old_attempts.count()
        
        if not dry_run:
            LoginAttempt.cleanup_old_attempts(days=days)
        
        self.stdout.write(
            f'{"Would delete" if dry_run else "Deleted"} {attempts_count} login attempts older than {days} days'
        )

        self.stdout.write(
            self.style.SUCCESS('Cleanup completed successfully!')
        )
