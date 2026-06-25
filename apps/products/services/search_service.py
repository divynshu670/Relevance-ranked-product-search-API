from dataclasses import dataclass
from typing import Iterable

from apps.products.models import Product


@dataclass(frozen=True)
class RankedProduct:
    product: Product
    tier: int
    relevance_score: float
    rank_reason: str
    matching_tag_count: int = 0
    exact_tag_match: bool = False
    text_match_priority: int = 0


def normalize_text(value: str) -> str:
    return " ".join((value or "").lower().strip().split())


def singularize(value: str) -> str:
    """
    Simple singular normalization for this assignment's category names.

    smartphone -> smartphone
    smartphones -> smartphone
    chargers -> charger
    """
    value = normalize_text(value)

    if value.endswith("ies"):
        return f"{value[:-3]}y"

    if value.endswith("s") and not value.endswith("ss"):
        return value[:-1]

    return value


def is_category_match(category: str, query: str) -> bool:
    """
    Supports case-insensitive partial matching and singular/plural matching.

    Examples:
    smartphone -> Smartphones
    phone -> Smartphones
    charger -> Chargers
    cover -> Back Covers
    """
    normalized_category = normalize_text(category)
    normalized_query = normalize_text(query)

    if not normalized_query:
        return False

    return (
        normalized_query in normalized_category
        or singularize(normalized_query) in singularize(normalized_category)
    )


def get_matching_tags(tags: Iterable[str], query: str) -> list[str]:
    normalized_query = normalize_text(query)

    return [
        normalize_text(tag)
        for tag in (tags or [])
        if normalized_query in normalize_text(tag)
    ]


def calculate_rank(product: Product, query: str) -> RankedProduct | None:
    """
    Assignment ranking rules:

    Tier 1: category matches query.
            Sub-sort: higher number of matching tags first.

    Tier 2: tags contain query but category does not match.
            Sub-sort: exact tag match before partial tag match.

    Tier 3: product name or description contains query.
            Sub-sort: product-name match before description-only match.
    """
    normalized_query = normalize_text(query)

    if not normalized_query:
        return None

    normalized_name = normalize_text(product.product_name)
    normalized_description = normalize_text(product.product_description)
    normalized_tags = [normalize_text(tag) for tag in (product.tags or [])]

    matching_tags = get_matching_tags(normalized_tags, normalized_query)
    matching_tag_count = len(matching_tags)
    exact_tag_match = any(tag == normalized_query for tag in matching_tags)

    # Tier 1: category match
    if is_category_match(product.category, normalized_query):
        # Score is only for display; sorting uses matching_tag_count explicitly.
        score = min(1.0, 0.90 + (matching_tag_count * 0.02))

        return RankedProduct(
            product=product,
            tier=1,
            relevance_score=round(score, 2),
            rank_reason="Category match",
            matching_tag_count=matching_tag_count,
            exact_tag_match=exact_tag_match,
        )

    # Tier 2: tag match, excluding category matches
    if matching_tags:
        score = 0.75 if exact_tag_match else 0.65
        matched_tag = matching_tags[0]

        return RankedProduct(
            product=product,
            tier=2,
            relevance_score=score,
            rank_reason=f"Tag match ({matched_tag})",
            matching_tag_count=matching_tag_count,
            exact_tag_match=exact_tag_match,
        )

    # Tier 3: product name or description match
    name_match = normalized_query in normalized_name
    description_match = normalized_query in normalized_description

    if name_match:
        score = 0.55 if normalized_name == normalized_query else 0.50

        return RankedProduct(
            product=product,
            tier=3,
            relevance_score=score,
            rank_reason="Product name match",
            text_match_priority=2,
        )

    if description_match:
        return RankedProduct(
            product=product,
            tier=3,
            relevance_score=0.35,
            rank_reason="Description match",
            text_match_priority=1,
        )

    return None


def search_products(
    query: str,
    category_filter: str | None = None,
) -> list[RankedProduct]:
    normalized_query = normalize_text(query)

    if not normalized_query:
        return []

    queryset = Product.objects.all()

    if category_filter:
        queryset = queryset.filter(category__iexact=category_filter.strip())

    ranked_results: list[RankedProduct] = []

    for product in queryset.iterator(chunk_size=500):
        ranked_product = calculate_rank(product, normalized_query)

        if ranked_product is not None:
            ranked_results.append(ranked_product)

    ranked_results.sort(
        key=lambda item: (
            # Primary rule: Tier 1, then Tier 2, then Tier 3.
            item.tier,

            # Tier 1 sub-sort: products with more matching tags first.
            -item.matching_tag_count if item.tier == 1 else 0,

            # Tier 2 sub-sort: exact tag match first.
            -int(item.exact_tag_match) if item.tier == 2 else 0,

            # Tier 3 sub-sort: name match before description-only match.
            -item.text_match_priority if item.tier == 3 else 0,

            # Stable deterministic tie-breakers.
            item.product.product_name.lower(),
            item.product.id,
        )
    )

    return ranked_results