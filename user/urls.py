from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet,
    GoogleVerifyTokenView,
    LogoutView,
    GoogleLoginView,
    GoogleCallbackView,
    AuthTestPageView,
    EmailTokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
    RegisterView,
    ChangePasswordView,
    PublicPingView,
    AuthPingView,
    AdminPingView,
    GoogleRevokeTokenView,
    GoogleLogoutRedirectView,
    EmailLoginRequestView,
    EmailLoginVerifyView,
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    # Auth HTML test pages and OAuth endpoints
    path('auth/test/', AuthTestPageView.as_view(), name='auth-test'),
    path('auth/google/login/', GoogleLoginView.as_view(), name='google-login'),
    path('auth/google/callback/', GoogleCallbackView.as_view(), name='google-callback'),
    path('auth/google/verify/', GoogleVerifyTokenView.as_view(), name='google-verify'),
    path('auth/google/revoke/', GoogleRevokeTokenView.as_view(), name='google-revoke'),
    path('auth/google/logout/', GoogleLogoutRedirectView.as_view(), name='google-logout'),
    path('auth/logout/', LogoutView.as_view(), name='api-logout'),
    # Email-based authentication (passwordless)
    path('auth/email/request/', EmailLoginRequestView.as_view(), name='email-login-request'),
    path('auth/email/verify/', EmailLoginVerifyView.as_view(), name='email-login-verify'),
    # JWT core under user
    path('auth/token/', EmailTokenObtainPairView.as_view(), name='token_obtain_pair_email'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh_user'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify_user'),
    # Registration and password change
    path('auth/register/', RegisterView.as_view(), name='auth_register'),
    path('auth/password/change/', ChangePasswordView.as_view(), name='auth_change_password'),
    # Authorization test endpoints
    path('auth/test/public/', PublicPingView.as_view(), name='auth_test_public'),
    path('auth/test/authenticated/', AuthPingView.as_view(), name='auth_test_authenticated'),
    path('auth/test/admin/', AdminPingView.as_view(), name='auth_test_admin'),
]

