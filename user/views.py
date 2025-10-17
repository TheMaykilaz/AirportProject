from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import User, EmailVerificationCode
from .serializers import (
    UserSerializer, 
    RegistrationSerializer, 
    EmailTokenObtainPairSerializer, 
    ChangePasswordSerializer,
    EmailLoginRequestSerializer,
    EmailLoginVerifySerializer
)
from .email_utils import send_verification_code
from AirplaneDJ.permissions import IsAdmin
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from requests_oauthlib import OAuth2Session
from django.conf import settings
from rest_framework.permissions import AllowAny
from django.shortcuts import redirect, render
from .google_auth import verify_google_token
from rest_framework import status
import requests as http_requests
from django.utils import timezone
from datetime import timedelta
from drf_spectacular.utils import extend_schema, OpenApiResponse

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_permissions(self):
        if self.action in ['list', 'destroy', 'make_admin', 'make_user']:
            return [IsAdmin()]
        return super().get_permissions()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def make_admin(self, request, pk=None):
        user = self.get_object()
        user.role = User.Role.ADMIN
        user.save()
        return Response({'status': f'{user.username} promoted to admin'})

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def make_user(self, request, pk=None):
        user = self.get_object()
        user.role = User.Role.USER
        user.save()
        return Response({'status': f'{user.username} demoted to user'})

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

""" GOOGLE AUTORISATION """

class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        force = request.GET.get("force") == "1"
        google = OAuth2Session(
            settings.GOOGLE_CLIENT_ID,
            redirect_uri=settings.GOOGLE_REDIRECT_URI,
            scope=["openid", "email", "profile"]
        )

        prompt = "select_account"
        if force:
            prompt = "consent select_account"

        authorization_url, _ = google.authorization_url(
            settings.GOOGLE_AUTHORIZATION_URL,
            access_type="offline",
            prompt=prompt
        )
        return redirect(authorization_url)


class GoogleCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # If the frontend asks for JSON explicitly, try to serve cached tokens from session
        # to avoid re-exchanging the one-time authorization code (which would cause invalid_grant).
        accept = request.headers.get('Accept', '')
        wants_json = 'application/json' in accept or request.GET.get('format') == 'json'
        cached = request.session.get('google_jwt_tokens')
        if wants_json and cached:
            return Response(cached)

        google = OAuth2Session(
            settings.GOOGLE_CLIENT_ID,
            redirect_uri=settings.GOOGLE_REDIRECT_URI
        )

        code = request.GET.get("code")
        if not code:
            return Response({"error": "No code provided"}, status=400)

        error_data = None
        token = None
        userinfo = None
        try:
            token = google.fetch_token(
                settings.GOOGLE_TOKEN_URL,
                client_secret=settings.GOOGLE_CLIENT_SECRET,
                code=code
            )
        except Exception as e:
            error_data = {"error": "google_token_exchange_failed", "detail": str(e)}

        if token and not error_data:
            try:
                userinfo = google.get(settings.GOOGLE_USERINFO_URL).json()
            except Exception as e:
                error_data = {"error": "google_userinfo_fetch_failed", "detail": str(e)}

        if error_data:
            # If JSON requested, return error payload; else render page which will fetch JSON
            if wants_json:
                return Response(error_data, status=400)
            return render(request, 'google_callback.html', status=400)

        if not userinfo.get("email"):
            return Response({"error": "No email returned"}, status=400)

        user, _ = User.objects.get_or_create(
            email=userinfo["email"],
            defaults={
                "username": userinfo["email"].split("@")[0],
                "first_name": userinfo.get("given_name", ""),
                "last_name": userinfo.get("family_name", ""),
                "role": User.Role.USER,
                "google_id": userinfo.get("sub"),
            }
        )

        refresh = RefreshToken.for_user(user)
        # Store Google OAuth token in session for potential revoke
        try:
            request.session["google_token"] = token
            # Also cache the issued JWTs and user info so the callback page can fetch them via ?format=json
            request.session["google_jwt_tokens"] = {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                },
            }
            request.session.modified = True
        except Exception:
            pass
        # Prefer HTML callback page for browsers so it can store tokens and redirect to /auth/test/
        if not wants_json or request.GET.get('html') == '1':
            return render(request, 'google_callback.html')

        return Response(request.session.get("google_jwt_tokens", {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
            }
        }))


class GoogleRevokeTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get("token")
        if not token:
            session_token = request.session.get("google_token") or {}
            token = session_token.get("access_token") or session_token.get("refresh_token")
        if not token:
            return Response({"error": "No Google token provided or stored in session"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            resp = http_requests.post("https://oauth2.googleapis.com/revoke", params={"token": token}, timeout=10)
            ok = resp.status_code in (200, 400)
            return Response({"revoked": ok, "status_code": resp.status_code})
        except Exception as e:
            return Response({"revoked": False, "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class GoogleLogoutRedirectView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # Redirect to Google's logout, then continue back to our test page
        continue_url = request.build_absolute_uri("/auth/test/")
        url = f"https://accounts.google.com/Logout?continue={continue_url}"
        # Also clear any stored Google token in session
        try:
            if "google_token" in request.session:
                del request.session["google_token"]
                request.session.modified = True
        except Exception:
            pass
        return redirect(url)


class AuthTestPageView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return render(request, 'auth_test.html')


class GoogleVerifyTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        id_token_str = request.data.get('id_token')
        if not id_token_str:
            return Response({"error": "Missing id_token"}, status=status.HTTP_400_BAD_REQUEST)

        userinfo = verify_google_token(id_token_str, settings.GOOGLE_CLIENT_ID)
        if not userinfo or not userinfo.get('email'):
            return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

        user, _ = User.objects.get_or_create(
            email=userinfo["email"],
            defaults={
                "username": userinfo["email"].split("@")[0],
                "first_name": userinfo.get("first_name", ""),
                "last_name": userinfo.get("last_name", ""),
                "role": User.Role.USER,
                "google_id": userinfo.get("google_sub"),
            }
        )

        refresh = RefreshToken.for_user(user)
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
            }
        })


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # Render the page that helps clear local tokens and optionally revoke refresh token via API
        return render(request, 'logout.html')

    def post(self, request):
        # Optional: blacklist the provided refresh token if blacklist app is enabled
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({"message": "No refresh provided; nothing to revoke."})

        try:
            token = RefreshToken(refresh_token)
            try:
                token.blacklist()
                blacklisted = True
            except Exception:
                blacklisted = False
            return Response({"message": "Refresh token processed.", "blacklisted": blacklisted})
        except Exception:
            return Response({"message": "Failed to process refresh token."}, status=status.HTTP_400_BAD_REQUEST)

class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=RegistrationSerializer,
        responses={
            201: OpenApiResponse(description='User created successfully'),
            400: OpenApiResponse(description='Validation error'),
        },
        summary="Register a new user",
        description="Create a new user account with email and password"
    )
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            "user": UserSerializer(user, context={'request': request}).data,
            "refresh": str(refresh),
            "access": str(refresh.access_token)
        }, status=status.HTTP_201_CREATED)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({"detail": "Current password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({"message": "Password changed."})


# Authorization test endpoints
class PublicPingView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        return Response({"ok": True, "scope": "public"})


class AuthPingView(APIView):
    def get(self, request):
        return Response({"ok": True, "scope": "authenticated", "user": UserSerializer(request.user, context={'request': request}).data})


class AdminPingView(APIView):
    def get_permissions(self):
        return [IsAdmin()]
    def get(self, request):
        return Response({"ok": True, "scope": "admin"})


""" EMAIL-BASED AUTHENTICATION (PASSWORDLESS) """


class EmailLoginRequestView(APIView):
    """
    Request a verification code to be sent to the user's email.
    POST /api/users/auth/email/request/
    Body: {"email": "user@example.com"}
    """
    permission_classes = [AllowAny]

    @extend_schema(
        request=EmailLoginRequestSerializer,
        responses={
            200: OpenApiResponse(description='Verification code sent'),
            429: OpenApiResponse(description='Rate limit exceeded'),
        },
        summary="Request email verification code",
        description="Send a verification code to the provided email address"
    )
    def post(self, request):
        serializer = EmailLoginRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        ip_address = self.get_client_ip(request)
        
        # Rate limiting: check if a code was sent recently (within last 60 seconds)
        recent_code = EmailVerificationCode.objects.filter(
            email=email,
            created_at__gte=timezone.now() - timedelta(seconds=60)
        ).first()
        
        if recent_code:
            return Response(
                {"error": "A verification code was recently sent. Please wait before requesting another."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        # Generate and send verification code
        verification = EmailVerificationCode.generate_code(email, ip_address=ip_address)
        
        # Send email - in development mode, this will always succeed
        email_sent = send_verification_code(email, verification.code)
        
        if not email_sent and not settings.DEBUG:
            return Response(
                {"error": "Failed to send verification email. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        response_data = {
            "message": "Verification code sent to your email",
            "email": email,
            "expires_in_minutes": 10
        }
        
        # In development mode, include the code in response for testing
        if settings.DEBUG:
            response_data["verification_code"] = verification.code
            response_data["dev_note"] = "Code included for development testing only"
        
        return Response(response_data)
    
    @staticmethod
    def get_client_ip(request):
        """Extract client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class EmailLoginVerifyView(APIView):
    """
    Verify the email code and issue JWT tokens.
    POST /api/users/auth/email/verify/
    Body: {"email": "user@example.com", "code": "123456"}
    """
    permission_classes = [AllowAny]

    @extend_schema(
        request=EmailLoginVerifySerializer,
        responses={
            200: OpenApiResponse(description='Login successful, tokens returned'),
            400: OpenApiResponse(description='Invalid or expired code'),
        },
        summary="Verify email code and login",
        description="Verify the email verification code and receive JWT tokens"
    )
    def post(self, request):
        serializer = EmailLoginVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        code = serializer.validated_data['code']
        
        # Find the most recent valid code for this email
        verification = EmailVerificationCode.objects.filter(
            email=email,
            code=code
        ).order_by('-created_at').first()
        
        if not verification:
            return Response(
                {"error": "Invalid verification code"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not verification.is_valid():
            return Response(
                {"error": "Verification code has expired or been used"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mark code as used
        verification.mark_used()
        
        # Get or create user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": email.split("@")[0],
                "role": User.Role.USER,
            }
        )
        
        # If user was created via email login, they don't have a password
        # This is intentional for passwordless login
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            "message": "Login successful" if not created else "Account created and logged in",
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
            }
        })