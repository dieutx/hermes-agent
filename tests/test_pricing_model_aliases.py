"""Tests for model alias resolution in usage pricing.

The pricing table uses dated model names (claude-opus-4-20250514) but the
model catalog lists undated aliases (claude-opus-4-6) as the default.
Without alias resolution, /usage shows "Pricing unknown" for most
Anthropic direct-provider users.
"""

from agent.usage_pricing import (
    _lookup_official_docs_pricing,
    resolve_billing_route,
    get_pricing_entry,
    BillingRoute,
)


class TestModelAliasResolution:

    def test_dated_model_has_pricing(self):
        """The dated name should always work."""
        route = BillingRoute(provider="anthropic", model="claude-opus-4-20250514", base_url="", billing_mode="official_docs_snapshot")
        entry = _lookup_official_docs_pricing(route)
        assert entry is not None

    def test_dot_versioned_opus_alias_resolves(self):
        """claude-opus-4.6 (actual default model name) should resolve."""
        route = BillingRoute(provider="anthropic", model="claude-opus-4.6", base_url="", billing_mode="official_docs_snapshot")
        entry = _lookup_official_docs_pricing(route)
        assert entry is not None
        assert entry.input_cost_per_million > 0

    def test_dot_versioned_sonnet_alias_resolves(self):
        """claude-sonnet-4.6 should resolve."""
        route = BillingRoute(provider="anthropic", model="claude-sonnet-4.6", base_url="", billing_mode="official_docs_snapshot")
        entry = _lookup_official_docs_pricing(route)
        assert entry is not None

    def test_hyphen_versioned_opus_alias_resolves(self):
        """claude-opus-4-6 (alternate format) should also resolve."""
        route = BillingRoute(provider="anthropic", model="claude-opus-4-6", base_url="", billing_mode="official_docs_snapshot")
        entry = _lookup_official_docs_pricing(route)
        assert entry is not None

    def test_older_dated_alias_resolves(self):
        """claude-opus-4-5-20251101 should resolve."""
        route = BillingRoute(provider="anthropic", model="claude-opus-4-5-20251101", base_url="", billing_mode="official_docs_snapshot")
        entry = _lookup_official_docs_pricing(route)
        assert entry is not None

    def test_haiku_alias_resolves(self):
        """claude-haiku-4-5 should resolve to 3-5-haiku pricing."""
        route = BillingRoute(provider="anthropic", model="claude-haiku-4-5", base_url="", billing_mode="official_docs_snapshot")
        entry = _lookup_official_docs_pricing(route)
        assert entry is not None

    def test_unknown_model_returns_none(self):
        """A model not in the table or aliases returns None."""
        route = BillingRoute(provider="anthropic", model="claude-unknown-99", base_url="", billing_mode="official_docs_snapshot")
        entry = _lookup_official_docs_pricing(route)
        assert entry is None

    def test_full_pipeline_opus_46_dot(self):
        """End-to-end: get_pricing_entry for anthropic/claude-opus-4.6 (real model string)."""
        entry = get_pricing_entry("anthropic/claude-opus-4.6", provider="anthropic")
        assert entry is not None
        assert entry.source == "official_docs_snapshot"
