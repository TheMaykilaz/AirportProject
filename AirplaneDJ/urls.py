

from django.contrib import admin
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from django.urls import path, include
from user.views import  GoogleLoginView, GoogleCallbackView
from rest_framework_simplejwt.views import (
        TokenObtainPairView,
        TokenRefreshView,
    )



urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('user.urls')),
    path('api/airport/', include('airport.urls')),

    path("api/payments/", include("strip_payment.urls")),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),


        # Google OAuth2
    path("api/auth/google/login/", GoogleLoginView.as_view(), name="google-login"),
    path("api/auth/google/callback/", GoogleCallbackView.as_view(), name="google-callback"),

    #Swagger
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

