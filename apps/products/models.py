from django.contrib.postgres.indexes import GinIndex
from django.db import models


class Product(models.Model):
    product_name = models.CharField(max_length=255)
    product_description = models.TextField(blank=True)
    category = models.CharField(max_length=100)
    tags = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]
        indexes = [
            models.Index(
                fields=["category"],
                name="product_category_idx",
            ),
            models.Index(
                fields=["product_name"],
                name="product_name_idx",
            ),
            GinIndex(
                fields=["tags"],
                name="product_tags_gin_idx",
            ),
        ]

    def __str__(self):
        return f"{self.product_name} ({self.category})"