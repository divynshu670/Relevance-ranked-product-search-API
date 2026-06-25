from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class AuthenticationAPITests(APITestCase):
    def test_register_creates_user_and_returns_tokens(self):
        response = self.client.post(
            "/api/auth/register",
            {
                "username": "new_user",
                "email": "new_user@example.com",
                "password": "SecurePass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["username"], "new_user")
        self.assertIn("token", response.data)
        self.assertIn("refresh", response.data)
        self.assertTrue(User.objects.filter(username="new_user").exists())

    def test_register_rejects_short_password(self):
        response = self.client.post(
            "/api/auth/register",
            {
                "username": "weak_password_user",
                "email": "weak@example.com",
                "password": "short",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_register_rejects_duplicate_email(self):
        User.objects.create_user(
            username="existing_user",
            email="existing@example.com",
            password="SecurePass123!",
        )

        response = self.client.post(
            "/api/auth/register",
            {
                "username": "different_user",
                "email": "existing@example.com",
                "password": "SecurePass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_login_returns_access_and_refresh_tokens(self):
        User.objects.create_user(
            username="login_user",
            email="login@example.com",
            password="SecurePass123!",
        )

        response = self.client.post(
            "/api/auth/login",
            {
                "username": "login_user",
                "password": "SecurePass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["username"], "login_user")

    def test_login_rejects_invalid_credentials(self):
        User.objects.create_user(
            username="invalid_login_user",
            email="invalid_login@example.com",
            password="SecurePass123!",
        )

        response = self.client.post(
            "/api/auth/login",
            {
                "username": "invalid_login_user",
                "password": "WrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_blacklists_refresh_token(self):
        User.objects.create_user(
            username="logout_user",
            email="logout@example.com",
            password="SecurePass123!",
        )

        login_response = self.client.post(
            "/api/auth/login",
            {
                "username": "logout_user",
                "password": "SecurePass123!",
            },
            format="json",
        )

        access_token = login_response.data["token"]
        refresh_token = login_response.data["refresh"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        logout_response = self.client.post(
            "/api/auth/logout",
            {"refresh": refresh_token},
            format="json",
        )

        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            logout_response.data["message"],
            "Logged out successfully",
        )