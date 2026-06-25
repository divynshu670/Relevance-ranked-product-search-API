from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from apps.products.models import Product

User = get_user_model()


class ProductAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="product_user",
            email="product_user@example.com",
            password="SecurePass123!",
        )

        cls.smartphone = Product.objects.create(
            product_name="Galaxy Pro",
            product_description="Flagship device",
            category="Smartphones",
            tags=["5g", "camera"],
        )

        cls.charger = Product.objects.create(
            product_name="USB-C Charger",
            product_description="Fast charging adapter",
            category="Chargers",
            tags=["smartphone", "fast-charging"],
        )

    def setUp(self):
        token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_search_requires_authentication(self):
        self.client.credentials()

        response = self.client.get(
            "/api/products/search",
            {"q": "smartphone"},
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_search_returns_category_before_tag_match(self):
        response = self.client.get(
            "/api/products/search",
            {"q": "smartphone", "limit": 20},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        result_ids = [item["id"] for item in response.data["results"]]

        self.assertLess(
            result_ids.index(self.smartphone.id),
            result_ids.index(self.charger.id),
        )

        self.assertEqual(
            response.data["results"][0]["rank_reason"],
            "Category match",
        )

    def test_search_returns_400_when_query_is_missing(self):
        response = self.client.get("/api/products/search")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("q", response.data["detail"])

    def test_search_returns_empty_results_gracefully(self):
        response = self.client.get(
            "/api/products/search",
            {"q": "not-a-real-product"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_results"], 0)
        self.assertEqual(response.data["results"], [])

    def test_get_product_by_id(self):
        response = self.client.get(f"/api/products/{self.smartphone.id}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.smartphone.id)

    def test_get_product_by_id_returns_404_for_missing_product(self):
        response = self.client.get("/api/products/999999")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_category_endpoint_is_case_insensitive(self):
        response = self.client.get("/api/products/category/smartphones")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_results"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.smartphone.id)

def test_search_pagination_returns_different_pages(self):
    for index in range(25):
        Product.objects.create(
            product_name=f"Phone Model {index}",
            product_description="A smartphone device",
            category="Smartphones",
            tags=["5g"],
        )

    first_page_response = self.client.get(
        "/api/products/search",
        {"q": "smartphone", "limit": 10, "page": 1},
    )
    second_page_response = self.client.get(
        "/api/products/search",
        {"q": "smartphone", "limit": 10, "page": 2},
    )

    self.assertEqual(first_page_response.status_code, status.HTTP_200_OK)
    self.assertEqual(second_page_response.status_code, status.HTTP_200_OK)

    self.assertEqual(first_page_response.data["page"], 1)
    self.assertEqual(second_page_response.data["page"], 2)
    self.assertEqual(first_page_response.data["returned_results"], 10)
    self.assertEqual(second_page_response.data["returned_results"], 10)

    first_page_ids = {
        product["id"] for product in first_page_response.data["results"]
    }
    second_page_ids = {
        product["id"] for product in second_page_response.data["results"]
    }

    self.assertTrue(first_page_ids.isdisjoint(second_page_ids))


def test_search_rejects_invalid_page(self):
    response = self.client.get(
        "/api/products/search",
        {"q": "smartphone", "page": 0},
    )

    self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    self.assertIn("page", response.data["detail"])