from django.shortcuts import get_object_or_404
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from rest_framework import status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analytics.models import SearchHistory

from .models import Product
from .serializers import ProductSerializer, SearchResultSerializer
from .services.search_service import search_products


class ProductSearchView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Products"],
        summary="Search products with relevance ranking",
        description=(
            "Searches products using a three-tier ranking system: "
            "category matches first, then tag matches, then product name or "
            "description matches. Search is case-insensitive and supports partial "
            "matches, for example `phone` matches `smartphone`."
        ),
        parameters=[
            OpenApiParameter(
                name="q",
                type=str,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Search query. Example: smartphone",
            ),
            OpenApiParameter(
                name="limit",
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Maximum results per page. Default 20, maximum 100.",
            ),
            OpenApiParameter(
                name="page",
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Page number. Default 1.",
            ),
            OpenApiParameter(
                name="category_filter",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Optional exact category filter. Example: Smartphones",
            ),
        ],
        responses={
            200: OpenApiResponse(description="Ranked search results returned."),
            400: OpenApiResponse(description="Missing or invalid query parameters."),
            401: OpenApiResponse(description="Authentication required."),
        },
        examples=[
            OpenApiExample(
                "Smartphone search response",
                value={
                    "query": "smartphone",
                    "category_filter": None,
                    "page": 1,
                    "limit": 20,
                    "total_results": 430,
                    "total_pages": 22,
                    "returned_results": 20,
                    "results": [
                        {
                            "id": 5,
                            "product_name": "Samsung Galaxy S24 Variant 3",
                            "product_description": (
                                "High-performance flagship device"
                            ),
                            "category": "Smartphones",
                            "tags": ["5g", "camera", "performance"],
                            "relevance_score": 0.90,
                            "rank_reason": "Category match",
                        },
                        {
                            "id": 450,
                            "product_name": "USB-C Fast Charger Model 1",
                            "product_description": "Fast and reliable charging",
                            "category": "Chargers",
                            "tags": [
                                "fast-charging",
                                "portable",
                                "smartphone",
                            ],
                            "relevance_score": 0.75,
                            "rank_reason": "Tag match (smartphone)",
                        },
                    ],
                },
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    def get(self, request):
        query = request.query_params.get("q", "").strip()
        category_filter = request.query_params.get(
            "category_filter",
            "",
        ).strip()

        if not query:
            return Response(
                {
                    "detail": "Query parameter 'q' is required.",
                    "status_code": status.HTTP_400_BAD_REQUEST,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(query) > 100:
            return Response(
                {
                    "detail": (
                        "Query parameter 'q' must not exceed 100 characters."
                    ),
                    "status_code": status.HTTP_400_BAD_REQUEST,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        limit_value = request.query_params.get("limit", "20")
        page_value = request.query_params.get("page", "1")

        try:
            limit = int(limit_value)
        except ValueError:
            return Response(
                {
                    "detail": "Query parameter 'limit' must be an integer.",
                    "status_code": status.HTTP_400_BAD_REQUEST,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            page = int(page_value)
        except ValueError:
            return Response(
                {
                    "detail": "Query parameter 'page' must be an integer.",
                    "status_code": status.HTTP_400_BAD_REQUEST,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not 1 <= limit <= 100:
            return Response(
                {
                    "detail": (
                        "Query parameter 'limit' must be between 1 and 100."
                    ),
                    "status_code": status.HTTP_400_BAD_REQUEST,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if page < 1:
            return Response(
                {
                    "detail": (
                        "Query parameter 'page' must be greater than or equal to 1."
                    ),
                    "status_code": status.HTTP_400_BAD_REQUEST,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        ranked_results = search_products(
            query=query,
            category_filter=category_filter or None,
        )

        total_results = len(ranked_results)
        start_index = (page - 1) * limit
        end_index = start_index + limit
        paginated_results = ranked_results[start_index:end_index]

        serialized_results = [
            SearchResultSerializer(
                {
                    "id": ranked_item.product.id,
                    "product_name": ranked_item.product.product_name,
                    "product_description": (
                        ranked_item.product.product_description
                    ),
                    "category": ranked_item.product.category,
                    "tags": ranked_item.product.tags,
                    "relevance_score": ranked_item.relevance_score,
                    "rank_reason": ranked_item.rank_reason,
                }
            ).data
            for ranked_item in paginated_results
        ]

        SearchHistory.objects.create(
            user=request.user,
            query=query,
            category_filter=category_filter,
            total_results=total_results,
        )

        return Response(
            {
                "query": query,
                "category_filter": category_filter or None,
                "page": page,
                "limit": limit,
                "total_results": total_results,
                "total_pages": (
                    (total_results + limit - 1) // limit
                    if total_results > 0
                    else 0
                ),
                "returned_results": len(serialized_results),
                "results": serialized_results,
            },
            status=status.HTTP_200_OK,
        )


class ProductDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Products"],
        summary="Get a product by ID",
        description="Returns one product. Requires JWT Bearer authentication.",
        responses={
            200: ProductSerializer,
            401: OpenApiResponse(description="Authentication required."),
            404: OpenApiResponse(description="Product not found."),
        },
    )
    def get(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        serializer = ProductSerializer(product)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class ProductCategoryView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Products"],
        summary="List products by category",
        description="Returns all products in a category using case-insensitive matching.",
        responses={
            200: OpenApiResponse(description="Products returned successfully."),
            401: OpenApiResponse(description="Authentication required."),
        },
    )
    def get(self, request, category):
        products = Product.objects.filter(
            category__iexact=category
        ).order_by("id")

        serializer = ProductSerializer(products, many=True)

        return Response(
            {
                "category": category,
                "total_results": products.count(),
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class ProductCreateView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        tags=["Products"],
        summary="Create a product",
        description="Creates a product. Admin users only.",
        request=ProductSerializer,
        responses={
            201: ProductSerializer,
            400: OpenApiResponse(description="Validation error."),
            401: OpenApiResponse(description="Authentication required."),
            403: OpenApiResponse(description="Admin permission required."),
        },
        examples=[
            OpenApiExample(
                "Create product request",
                value={
                    "product_name": "Pixel 9 Pro",
                    "product_description": "Flagship Android smartphone.",
                    "category": "Smartphones",
                    "tags": ["5g", "camera", "android"],
                },
                request_only=True,
            ),
        ],
    )
    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = serializer.save()

        return Response(
            ProductSerializer(product).data,
            status=status.HTTP_201_CREATED,
        )