# src/apps/users/views.py
from rest_framework import generics, permissions, viewsets, status
from rest_framework.response import Response
from django.contrib.auth import get_user_model

from .serializers import UserSerializer, UserCreateSerializer, AdminUserSerializer

User = get_user_model()

class CurrentUserView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]  # Anyone can register
    serializer_class = UserCreateSerializer


class AdminUserViewSet(viewsets.ReadOnlyModelViewSet):  # ReadOnly + Destroy
    """
    Allows Admins to list and delete users.
    """

    queryset = (
        User.objects.select_related("profile").all().order_by("id")
    )  # Get all users
    serializer_class = AdminUserSerializer  # Use the Admin specific serializer
    permission_classes = [permissions.IsAdminUser]  # Only Admins

    # Override destroy for custom logic or just use default
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_superuser:
            return Response(
                {"detail": "Cannot delete superuser."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Perform standard delete directly on the model instance
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # Optional: Add custom actions if needed later
