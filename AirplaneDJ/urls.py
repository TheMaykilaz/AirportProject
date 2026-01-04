

from django.contrib import admin
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from django.urls import path, include, re_path
from django.views.static import serve
from django.conf import settings
from django.conf.urls.static import static
from user.views import  GoogleLoginView, GoogleCallbackView, AuthTestPageView, LogoutView
from rest_framework_simplejwt.views import (
        TokenObtainPairView,
        TokenRefreshView,
    )
from hotels.views import HotelsSearchView
from airport.views import FlightSearchPageView, FlightResultsPageView
from .views import ReactAppView



urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('user.urls')),
    path('api/airport/', include('airport.urls')),
    path('api/bookings/', include('bookings.urls')),
    path('api/hotels/', include('hotels.urls')),
    path("api/payments/", include("stripe_payment.urls")),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),


    # Legacy Google OAuth2 aliases (backward compatibility for existing redirect URIs)
    path("api/auth/google/login/", GoogleLoginView.as_view(), name="google-login-legacy"),
    path("api/auth/google/callback/", GoogleCallbackView.as_view(), name="google-callback-legacy"),

    # AI Chat
    path('', include('ai_chat.urls')),

    #Swagger
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("auth/test/", AuthTestPageView.as_view(), name="auth-test"),
    path("logout/", LogoutView.as_view(), name="logout"),
    
    # Hotels search page (before React catch-all)
    path("hotels/", HotelsSearchView.as_view(), name="hotels-search"),
    
    # Flight search pages (before React catch-all)
    path("search/", FlightSearchPageView.as_view(), name="flight-search-page"),
    path("search/results/", FlightResultsPageView.as_view(), name="flight-results-page"),
    
    # React app - catch all routes and serve React app
    # This should be last to catch all non-API routes
    re_path(r'^(?!api|admin|swagger|redoc|auth|logout|hotels|search).*$', ReactAppView.as_view(), name='react-app'),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

