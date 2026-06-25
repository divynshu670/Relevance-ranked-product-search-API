from django.contrib import admin

from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "product_name", "category", "created_at")
    list_filter = ("category",)
    search_fields = ("product_name", "product_description", "category")
    ordering = ("id",)