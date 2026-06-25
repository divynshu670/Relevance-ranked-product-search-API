from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from apps.analytics.models import SearchHistory
from apps.products.models import Product

User = get_user_model()


class SearchHistoryAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="analytics_user",
            email="analytics_user@example.com",
            password="SecurePass123!",
        )

        cls.other_user = User.objects.create_user(
            username="other_analytics_user",
            email="other_analytics@example.com",
            password="SecurePass123!",
        )

        Product.objects.create(
            product_name="Galaxy Pro",
            product_description="Flagship smartphone",
            category="Smartphones",
            tags=["5g", "camera"],
        )

    def setUp(self):
        token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_search_creates_history_record(self):
        response = self.client.get(
            "/api/products/search",
            {"q": "smartphone"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        history = SearchHistory.objects.get(user=self.user)

        self.assertEqual(history.query, "smartphone")
        self.assertEqual(history.total_results, 1)
        self.assertEqual(history.category_filter, "")

    def test_history_returns_only_current_users_records(self):
        SearchHistory.objects.create(
            user=self.user,
            query="smartphone",
            total_results=1,
        )
        SearchHistory.objects.create(
            user=self.other_user,
            query="charger",
            total_results=0,
        )

        response = self.client.get("/api/analytics/search-history")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_results"], 1)
        self.assertEqual(response.data["results"][0]["query"], "smartphone")

    def test_history_requires_authentication(self):
        self.client.credentials()

        response = self.client.get("/api/analytics/search-history")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_history_rejects_invalid_limit(self):
        response = self.client.get(
            "/api/analytics/search-history",
            {"limit": "invalid"},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)