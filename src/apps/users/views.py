# src/apps/users/views.py (or a common location)
from rest_framework import generics, permissions
from .serializers import UserSerializer # Adjust import path

class CurrentUserView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated] # Ensure user is logged in

    def get_object(self):
        return self.request.user # Returns the user associated with the request token
