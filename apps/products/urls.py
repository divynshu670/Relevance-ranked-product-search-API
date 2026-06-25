from django.urls import path

from .views import (
    ProductCategoryView,
    ProductCreateView,
    ProductDetailView,
    ProductSearchView,
)

urlpatterns = [
    path("search", ProductSearchView.as_view(), name="product-search"),
    path("category/<str:category>", ProductCategoryView.as_view(), name="product-category"),
    path("", ProductCreateView.as_view(), name="product-create"),
    path("<int:product_id>", ProductDetailView.as_view(), name="product-detail"),
]