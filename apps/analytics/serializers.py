from rest_framework import serializers

from .models import SearchHistory


class SearchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchHistory
        fields = (
            "id",
            "query",
            "category_filter",
            "total_results",
            "created_at",
        )