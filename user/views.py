from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import User
from .serializers import UserSerializer
from AirplaneDJ.permissions import IsAdmin
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from requests_oauthlib import OAuth2Session
from django.conf import settings
from rest_framework.permissions import AllowAny
from django.shortcuts import redirect

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
        google = OAuth2Session(
            settings.GOOGLE_CLIENT_ID,
            redirect_uri=settings.GOOGLE_REDIRECT_URI,
            scope=["openid", "email", "profile"]
        )

        authorization_url, _ = google.authorization_url(
            settings.GOOGLE_AUTHORIZATION_URL,
            access_type="offline",
            prompt="select_account"
        )

        return redirect(authorization_url)


class GoogleCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        google = OAuth2Session(
            settings.GOOGLE_CLIENT_ID,
            redirect_uri=settings.GOOGLE_REDIRECT_URI
        )

        code = request.GET.get("code")
        if not code:
            return Response({"error": "No code provided"}, status=400)

        token = google.fetch_token(
            settings.GOOGLE_TOKEN_URL,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            code=code
        )

        userinfo = google.get(settings.GOOGLE_USERINFO_URL).json()

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
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
            }
        })