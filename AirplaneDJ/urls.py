

from django.contrib import admin
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from django.urls import path, include
from user.views import  GoogleLoginView, GoogleCallbackView, AuthTestPageView, LogoutView
from rest_framework_simplejwt.views import (
        TokenObtainPairView,
        TokenRefreshView,
    )



urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('user.urls')),
    path('api/airport/', include('airport.urls')),
    path('api/bookings/', include('bookings.urls')),
    path("api/payments/", include("stripe_payment.urls")),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),


    # Legacy Google OAuth2 aliases (backward compatibility for existing redirect URIs)
    path("api/auth/google/login/", GoogleLoginView.as_view(), name="google-login-legacy"),
    path("api/auth/google/callback/", GoogleCallbackView.as_view(), name="google-callback-legacy"),


    #Swagger
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("auth/test/", AuthTestPageView.as_view(), name="auth-test"),
    path("logout/", LogoutView.as_view(), name="logout"),
]

