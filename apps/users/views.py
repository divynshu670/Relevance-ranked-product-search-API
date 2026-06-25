from django.contrib.auth import authenticate
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
)
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import LoginSerializer, RegisterSerializer


def build_token_response(user):
    refresh = RefreshToken.for_user(user)

    return {
        "token": str(refresh.access_token),
        "refresh": str(refresh),
        "user": {
            "id": user.id,
            "username": user.username,
        },
    }


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Authentication"],
        summary="Register a new user",
        description=(
            "Creates a new user account and returns JWT access and refresh tokens. "
            "Password must contain at least 8 characters."
        ),
        request=RegisterSerializer,
        responses={
            201: OpenApiResponse(
                description="User registered successfully.",
            ),
            400: OpenApiResponse(
                description="Validation error, duplicate username/email, or weak password.",
            ),
        },
        examples=[
            OpenApiExample(
                "Register request",
                value={
                    "username": "divyanshu",
                    "email": "divyanshu@example.com",
                    "password": "SecurePass123!",
                },
                request_only=True,
            ),
            OpenApiExample(
                "Register success response",
                value={
                    "id": 1,
                    "username": "divyanshu",
                    "token": "eyJhbGciOiJIUzI1Ni...",
                    "refresh": "eyJhbGciOiJIUzI1Ni...",
                },
                response_only=True,
                status_codes=["201"],
            ),
        ],
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        token_data = build_token_response(user)

        return Response(
            {
                "id": user.id,
                "username": user.username,
                "token": token_data["token"],
                "refresh": token_data["refresh"],
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Authentication"],
        summary="Login and receive JWT tokens",
        description="Authenticates a user using username and password.",
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(description="Login successful."),
            401: OpenApiResponse(description="Invalid username or password."),
        },
        examples=[
            OpenApiExample(
                "Login request",
                value={
                    "username": "divyanshu",
                    "password": "SecurePass123!",
                },
                request_only=True,
            ),
            OpenApiExample(
                "Login success response",
                value={
                    "token": "eyJhbGciOiJIUzI1Ni...",
                    "refresh": "eyJhbGciOiJIUzI1Ni...",
                    "user": {
                        "id": 1,
                        "username": "divyanshu",
                    },
                },
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )

        if user is None:
            return Response(
                {"detail": "Invalid username or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {"detail": "This user account is inactive."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(build_token_response(user), status=status.HTTP_200_OK)


class LogoutSerializer(LoginSerializer):
    refresh = serializers.CharField(
        write_only=True,
        help_text="JWT refresh token returned during login.",
    )

    class Meta:
        fields = ("refresh",)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Authentication"],
        summary="Logout and blacklist refresh token",
        description=(
            "Requires a valid Bearer access token. "
            "Blacklists the supplied refresh token so it cannot be used again."
        ),
        request=LogoutSerializer,
        responses={
            200: OpenApiResponse(description="Logged out successfully."),
            400: OpenApiResponse(description="Missing, invalid, or expired refresh token."),
            401: OpenApiResponse(description="Missing or invalid access token."),
        },
        examples=[
            OpenApiExample(
                "Logout request",
                value={
                    "refresh": "eyJhbGciOiJIUzI1Ni...",
                },
                request_only=True,
            ),
            OpenApiExample(
                "Logout success response",
                value={
                    "message": "Logged out successfully",
                },
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"detail": "Refresh token is required to log out."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response(
                {"detail": "Invalid or expired refresh token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"message": "Logged out successfully"},
            status=status.HTTP_200_OK,
        )