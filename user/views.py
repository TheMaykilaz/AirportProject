from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import User
from .serializers import UserSerializer
from AirplaneDJ.permissions import IsAdmin


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
