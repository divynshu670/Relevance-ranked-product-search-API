from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SearchHistory
from .serializers import SearchHistorySerializer


class SearchHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Analytics"],
        summary="Get the current user's search history",
        description="Returns recent searches made by the authenticated user.",
        parameters=[
            OpenApiParameter(
                name="limit",
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Maximum history records to return. Default 20, maximum 100.",
            ),
        ],
        responses={
            200: OpenApiResponse(description="Search history returned."),
            400: OpenApiResponse(description="Invalid limit."),
            401: OpenApiResponse(description="Authentication required."),
        },
    )
    def get(self, request):
        limit_value = request.query_params.get("limit", "20")

        try:
            limit = int(limit_value)
        except ValueError:
            return Response(
                {
                    "detail": "Query parameter 'limit' must be an integer.",
                    "status_code": 400,
                },
                status=400,
            )

        if not 1 <= limit <= 100:
            return Response(
                {
                    "detail": "Query parameter 'limit' must be between 1 and 100.",
                    "status_code": 400,
                },
                status=400,
            )

        history = SearchHistory.objects.filter(user=request.user)[:limit]

        return Response(
            {
                "total_results": SearchHistory.objects.filter(
                    user=request.user
                ).count(),
                "results": SearchHistorySerializer(history, many=True).data,
            }
        )