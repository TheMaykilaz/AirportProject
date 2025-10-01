from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Test email configuration by sending a test email'

    def add_arguments(self, parser):
        parser.add_argument(
            'recipient',
            type=str,
            help='Email address to send test email to'
        )

    def handle(self, *args, **options):
        recipient = options['recipient']
        
        self.stdout.write(self.style.WARNING(f'Attempting to send test email to: {recipient}'))
        self.stdout.write(f'Using backend: {settings.EMAIL_BACKEND}')
        
        if 'console' in settings.EMAIL_BACKEND.lower():
            self.stdout.write(self.style.WARNING(
                '\nWARNING: You are using console.EmailBackend - the email will be printed below, not sent.\n'
            ))
        
        try:
            send_mail(
                subject='Test Email from AirplaneDJ',
                message='This is a test email. If you received this, your email configuration is working!',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )
            
            if 'console' in settings.EMAIL_BACKEND.lower():
                self.stdout.write(self.style.SUCCESS(
                    '\nSUCCESS: Email printed to console above. Check your terminal output.\n'
                ))
                self.stdout.write(self.style.WARNING(
                    'To send real emails, update EMAIL_BACKEND in your .env file.\n'
                    'See EMAIL_SETUP_GUIDE.md for instructions.'
                ))
            else:
                self.stdout.write(self.style.SUCCESS(
                    f'\nSUCCESS: Test email sent successfully to {recipient}!\n'
                    'Check your inbox (and spam folder).'
                ))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nERROR: Failed to send email: {str(e)}\n'))
            self.stdout.write('Check your email configuration in .env file.')
            self.stdout.write('See EMAIL_SETUP_GUIDE.md for troubleshooting.')
