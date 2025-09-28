from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import User
from .serializers import UserSerializer
from AirplaneDJ.permissions import IsAdmin
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .google_auth import verify_google_token
from django.conf import settings
from rest_framework.permissions import AllowAny

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

class GoogleLoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        print(request.data)
        token = request.data.get("token")
        if not token:
            return Response({"error": "Token is required"}, status=status.HTTP_400_BAD_REQUEST)

        user_info = verify_google_token(token, settings.GOOGLE_CLIENT_ID)
        if not user_info or not user_info.get("email"):
            return Response({"error": "Invalid Google token"}, status=status.HTTP_400_BAD_REQUEST)

        user, _ = User.objects.get_or_create(
            email=user_info["email"],
            defaults={
                "username": user_info["email"].split("@")[0],
                "first_name": user_info.get("given_name", ""),
                "last_name": user_info.get("family_name", ""),
                "role": User.Role.USER
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
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role
            }
        })