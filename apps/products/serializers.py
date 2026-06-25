from rest_framework import serializers

from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            "id",
            "product_name",
            "product_description",
            "category",
            "tags",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_product_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError("Product name cannot be empty.")

        return value

    def validate_category(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError("Category cannot be empty.")

        return value

    def validate_tags(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Tags must be a list.")

        cleaned_tags = []

        for tag in value:
            if not isinstance(tag, str):
                raise serializers.ValidationError("Every tag must be a string.")

            normalized_tag = tag.strip().lower()

            if normalized_tag:
                cleaned_tags.append(normalized_tag)

        return list(dict.fromkeys(cleaned_tags))


class SearchResultSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    product_name = serializers.CharField()
    product_description = serializers.CharField()
    category = serializers.CharField()
    tags = serializers.ListField(child=serializers.CharField())
    relevance_score = serializers.FloatField()
    rank_reason = serializers.CharField()