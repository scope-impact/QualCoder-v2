"""
Storage Context: Invariants (Business Rule Predicates)

Pure predicate functions that validate storage business rules.
"""

from __future__ import annotations

import re


# ============================================================
# S3 Bucket Name Invariants
# ============================================================

# S3 bucket naming rules (simplified):
# - 3-63 characters
# - lowercase letters, numbers, hyphens, dots
# - Must start/end with letter or number
_BUCKET_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9.\-]{1,61}[a-z0-9]$")


def is_valid_bucket_name(name: str) -> bool:
    """
    Check that an S3 bucket name is valid.

    Rules (simplified AWS S3 rules):
    - Between 3 and 63 characters
    - Only lowercase letters, numbers, hyphens, dots
    - Must start and end with a letter or number
    - No underscores
    """
    if not name or len(name) < 3 or len(name) > 63:
        return False
    return _BUCKET_NAME_PATTERN.match(name) is not None


# ============================================================
# S3 Key Invariants
# ============================================================


def is_valid_s3_key(key: str) -> bool:
    """
    Check that an S3 object key is valid.

    Rules:
    - Not empty or whitespace-only
    """
    return bool(key and key.strip())


# ============================================================
# Store Config Invariants
# ============================================================


def is_valid_store_config(bucket_name: str, region: str) -> bool:
    """
    Check that a complete store configuration is valid.

    Rules:
    - Valid bucket name
    - Non-empty region
    """
    return is_valid_bucket_name(bucket_name) and bool(region and region.strip())
