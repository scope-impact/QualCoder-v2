"""
Storage Context: Invariant Unit Tests (TDD RED phase)

Tests for storage business rule predicates.
"""

from __future__ import annotations

import pytest
import allure


pytestmark = [
    pytest.mark.unit,
    allure.epic("QualCoder v2"),
    allure.feature("QC-047 S3 Data Store"),
]


@allure.story("QC-047.01 Domain Invariants")
class TestBucketNameValidation:
    """Invariants for S3 bucket name validation."""

    @allure.title("Valid bucket name passes validation")
    @pytest.mark.parametrize(
        "name",
        ["research-data", "my.bucket.2026", "a-bucket-name"],
        ids=["hyphen", "dots", "long-hyphen"],
    )
    def test_valid_bucket_names(self, name):
        from src.contexts.storage.core.invariants import is_valid_bucket_name

        assert is_valid_bucket_name(name) is True

    @allure.title("Invalid bucket name fails validation")
    @pytest.mark.parametrize(
        "name",
        ["", "AB", "bucket_with_underscore", "a" * 64, "-start-dash", "end-dash-"],
        ids=["empty", "too_short", "underscore", "too_long", "start_dash", "end_dash"],
    )
    def test_invalid_bucket_names(self, name):
        from src.contexts.storage.core.invariants import is_valid_bucket_name

        assert is_valid_bucket_name(name) is False


@allure.story("QC-047.01 Domain Invariants")
class TestS3KeyValidation:
    """Invariants for S3 key (file path) validation."""

    @allure.title("Valid S3 key passes validation")
    @pytest.mark.parametrize(
        "key",
        ["raw/data.json", "processed/profiles.csv", "file.txt"],
        ids=["nested", "deep", "root"],
    )
    def test_valid_keys(self, key):
        from src.contexts.storage.core.invariants import is_valid_s3_key

        assert is_valid_s3_key(key) is True

    @allure.title("Invalid S3 key fails validation")
    @pytest.mark.parametrize(
        "key",
        ["", "   "],
        ids=["empty", "whitespace"],
    )
    def test_invalid_keys(self, key):
        from src.contexts.storage.core.invariants import is_valid_s3_key

        assert is_valid_s3_key(key) is False


@allure.story("QC-047.01 Domain Invariants")
class TestStoreConfigValidation:
    """Invariants for complete store configuration."""

    @allure.title("Valid store config passes validation")
    def test_valid_store_config(self):
        from src.contexts.storage.core.invariants import is_valid_store_config

        assert is_valid_store_config(
            bucket_name="research-data",
            region="us-east-1",
        ) is True

    @allure.title("Store config with empty region fails")
    def test_empty_region_fails(self):
        from src.contexts.storage.core.invariants import is_valid_store_config

        assert is_valid_store_config(
            bucket_name="research-data",
            region="",
        ) is False

    @allure.title("Store config with invalid bucket fails")
    def test_invalid_bucket_fails(self):
        from src.contexts.storage.core.invariants import is_valid_store_config

        assert is_valid_store_config(
            bucket_name="",
            region="us-east-1",
        ) is False
