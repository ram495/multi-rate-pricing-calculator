from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import RegisterSerializer, UserSerializer
from .throttles import AuthRateThrottle


class RegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthRateThrottle]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": {"id": user.id, "email": user.email},
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=201,
        )


class LoginView(TokenObtainPairView):
    """simplejwt's TokenObtainPairView with a tight throttle — login is the
    other endpoint (besides register) worth protecting from brute-force."""

    throttle_classes = [AuthRateThrottle]


class MeView(generics.RetrieveAPIView):
    """Who am I — the server-side source of truth for the current user's
    identity, so the frontend never has to guess from a stale localStorage
    value (e.g. a session that started before email persistence existed)."""

    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
