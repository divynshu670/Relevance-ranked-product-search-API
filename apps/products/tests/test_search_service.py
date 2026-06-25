from django.test import TestCase

from apps.products.models import Product
from apps.products.services.search_service import (
    calculate_rank,
    search_products,
)


class SearchServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Tier 1: actual products in the Smartphones category.
        cls.smartphone_without_matching_tag = Product.objects.create(
            product_name="Alpha Phone",
            product_description="A flagship mobile device.",
            category="Smartphones",
            tags=["5g", "camera"],
        )

        cls.smartphone_with_one_matching_tag = Product.objects.create(
            product_name="Beta Phone",
            product_description="A flagship mobile device.",
            category="Smartphones",
            tags=["smartphone", "camera"],
        )

        cls.smartphone_with_two_matching_tags = Product.objects.create(
            product_name="Gamma Phone",
            product_description="A flagship mobile device.",
            category="Smartphones",
            tags=["smartphone", "smartphones", "camera"],
        )

        # Tier 2: accessories only match because of tags.
        cls.exact_tag_charger = Product.objects.create(
            product_name="USB-C Charger",
            product_description="Fast charger.",
            category="Chargers",
            tags=["smartphone", "fast-charging"],
        )

        cls.partial_tag_cover = Product.objects.create(
            product_name="Protective Cover",
            product_description="Protective accessory.",
            category="Back Covers",
            tags=["smartphone-compatible", "durable"],
        )

        # Tier 3: text-only matches.
        cls.name_match_product = Product.objects.create(
            product_name="Pro Smartphone Stand",
            product_description="Desk accessory.",
            category="Accessories",
            tags=["stand"],
        )

        cls.description_match_product = Product.objects.create(
            product_name="Desk Stand",
            product_description="A stand designed for a smartphone.",
            category="Accessories",
            tags=["stand"],
        )

    def test_category_match_is_tier_one(self):
        ranked = calculate_rank(self.smartphone_without_matching_tag, "smartphone")

        self.assertIsNotNone(ranked)
        self.assertEqual(ranked.tier, 1)
        self.assertEqual(ranked.rank_reason, "Category match")

    def test_category_match_supports_partial_query(self):
        ranked = calculate_rank(self.smartphone_without_matching_tag, "phone")

        self.assertIsNotNone(ranked)
        self.assertEqual(ranked.tier, 1)

    def test_exact_tag_match_is_tier_two(self):
        ranked = calculate_rank(self.exact_tag_charger, "smartphone")

        self.assertIsNotNone(ranked)
        self.assertEqual(ranked.tier, 2)
        self.assertTrue(ranked.exact_tag_match)
        self.assertEqual(ranked.rank_reason, "Tag match (smartphone)")

    def test_partial_tag_match_is_tier_two(self):
        ranked = calculate_rank(self.partial_tag_cover, "smartphone")

        self.assertIsNotNone(ranked)
        self.assertEqual(ranked.tier, 2)
        self.assertFalse(ranked.exact_tag_match)
        self.assertEqual(ranked.rank_reason, "Tag match (smartphone-compatible)")

    def test_name_match_is_tier_three(self):
        ranked = calculate_rank(self.name_match_product, "smartphone")

        self.assertIsNotNone(ranked)
        self.assertEqual(ranked.tier, 3)
        self.assertEqual(ranked.rank_reason, "Product name match")

    def test_description_match_is_tier_three(self):
        ranked = calculate_rank(self.description_match_product, "smartphone")

        self.assertIsNotNone(ranked)
        self.assertEqual(ranked.tier, 3)
        self.assertEqual(ranked.rank_reason, "Description match")

    def test_category_results_always_come_before_tag_and_text_results(self):
        results = search_products("smartphone")
        result_ids = [item.product.id for item in results]

        first_tier_two_index = result_ids.index(self.exact_tag_charger.id)
        first_tier_three_index = result_ids.index(self.name_match_product.id)

        self.assertLess(
            result_ids.index(self.smartphone_without_matching_tag.id),
            first_tier_two_index,
        )
        self.assertLess(
            result_ids.index(self.smartphone_with_one_matching_tag.id),
            first_tier_two_index,
        )
        self.assertLess(
            result_ids.index(self.smartphone_with_two_matching_tags.id),
            first_tier_two_index,
        )
        self.assertLess(first_tier_two_index, first_tier_three_index)

    def test_tier_one_is_sorted_by_matching_tag_count_descending(self):
        results = search_products("smartphone")
        result_ids = [item.product.id for item in results]

        self.assertLess(
            result_ids.index(self.smartphone_with_two_matching_tags.id),
            result_ids.index(self.smartphone_with_one_matching_tag.id),
        )
        self.assertLess(
            result_ids.index(self.smartphone_with_one_matching_tag.id),
            result_ids.index(self.smartphone_without_matching_tag.id),
        )

    def test_tier_two_exact_tag_match_is_before_partial_tag_match(self):
        results = search_products("smartphone")
        result_ids = [item.product.id for item in results]

        self.assertLess(
            result_ids.index(self.exact_tag_charger.id),
            result_ids.index(self.partial_tag_cover.id),
        )

    def test_tier_three_name_match_is_before_description_match(self):
        results = search_products("smartphone")
        result_ids = [item.product.id for item in results]

        self.assertLess(
            result_ids.index(self.name_match_product.id),
            result_ids.index(self.description_match_product.id),
        )

    def test_category_filter_limits_results_to_requested_category(self):
        results = search_products(
            query="smartphone",
            category_filter="Chargers",
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].product.id, self.exact_tag_charger.id)

    def test_unknown_query_returns_empty_list(self):
        results = search_products("unicornlaptop999")

        self.assertEqual(results, [])