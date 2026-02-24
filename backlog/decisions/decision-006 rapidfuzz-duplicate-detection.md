---
id: decision-006
title: Use rapidfuzz for Duplicate Code Detection
status: Accepted
date: '2026-02-24'
deciders: []
labels:
  - coding
  - ai-agents
  - duplicate-detection
---

## Context

The `detect_duplicate_codes` MCP tool (QC-028.08) used `difflib.SequenceMatcher` from Python's stdlib for similarity scoring. `SequenceMatcher` operates at the **character level**, comparing raw character sequences. This caused false positives when codes shared common characters but were semantically unrelated.

### Example False Positive

| Code A | Code B | SequenceMatcher | Verdict |
|--------|--------|-----------------|---------|
| Sports & Recreation | Trust & Verification | **61%** | False positive at threshold 0.6 |

The character sequences `"S...r...t...&...Re...tion"` overlap significantly even though these are unrelated concepts.

## Decision

**Accepted: Replace `difflib.SequenceMatcher` with `rapidfuzz.fuzz.token_set_ratio`.**

### Why token_set_ratio

`token_set_ratio` operates on **word tokens**, not characters:

1. Splits each string into a set of unique, lowercased words
2. Computes the intersection and differences of the two word sets
3. Scores based on how much of the content overlaps at the word level

This means "Sports & Recreation" vs "Trust & Verification" only shares the token `"&"`, scoring ~36% instead of 61%.

### Memo-Aware Blending

When both codes have memos (descriptions), the score blends:

- **60% name similarity** (token_set_ratio on names)
- **40% memo similarity** (token_set_ratio on memos)

This lets codes with different names but similar descriptions surface as candidates.

## Options Considered

### Option 1: difflib.SequenceMatcher (Status Quo, Rejected)

| Pros | Cons |
|------|------|
| Stdlib, no dependency | Character-level false positives |
| Zero install cost | Cannot incorporate memo similarity |

**Rejected because:** Produces false positives on short code names with shared character patterns.

### Option 2: fuzzywuzzy (Rejected)

| Pros | Cons |
|------|------|
| Well-known API | Python-only, slower |
| Token-level matching | GPL dependency on python-Levenshtein |
| | Deprecated in favor of rapidfuzz |

**Rejected because:** GPL license conflict and deprecated.

### Option 3: LLM-Based Similarity (Rejected)

| Pros | Cons |
|------|------|
| Most semantically accurate | Requires API calls, latency, cost |
| Understands meaning | Offline incompatible |
| | Overkill for 2-5 word code names |

**Rejected because:** QualCoder must work offline and without API keys for core features.

### Option 4: TF-IDF / Embedding Cosine (Rejected)

| Pros | Cons |
|------|------|
| Good for longer text | Overkill for short code names |
| Semantic similarity | Requires embedding model (~100MB+) |

**Rejected because:** Code names are 2-5 words; embedding overhead not justified.

### Option 5: rapidfuzz (Accepted)

| Pros | Cons |
|------|------|
| Token-level matching | New dependency (~500KB) |
| Rust-based, fast | |
| MIT license | |
| Drop-in API | |

**Accepted because:** Solves the false positive problem with minimal dependency cost, MIT license, and works offline.

## Consequences

### Positive

- **Eliminates false positives** from character-level matching
- **Faster execution** due to Rust native implementation
- **Memo-aware scoring** surfaces related codes even when names differ
- **All 10 existing E2E tests pass** without modification

### Negative

- **New dependency**: `rapidfuzz>=3.0` (~500KB, MIT license, pre-built wheels for all platforms)

## Implementation

### Files Changed

| File | Change |
|------|--------|
| `pyproject.toml` | Added `rapidfuzz>=3.0` |
| `src/contexts/coding/interface/handlers/duplicate_handlers.py` | Replaced `SequenceMatcher` with `fuzz.token_set_ratio`, added memo-aware blending |

### Algorithm

```python
from rapidfuzz import fuzz

def _calculate_similarity(
    name_a: str, name_b: str,
    memo_a: str | None = None, memo_b: str | None = None,
) -> float:
    name_score = fuzz.token_set_ratio(name_a, name_b) / 100.0
    if memo_a and memo_b:
        memo_score = fuzz.token_set_ratio(memo_a, memo_b) / 100.0
        return 0.6 * name_score + 0.4 * memo_score
    return name_score
```

### Before / After

| Pair | Old (SequenceMatcher) | New (token_set_ratio) |
|------|----------------------|----------------------|
| Theme / Themes | ~91% | ~91% (correct match) |
| Positive Emotion / Positive Feeling | ~59% | ~67% (improved) |
| Sports & Recreation / Trust & Verification | **61% (false positive)** | **~36% (correctly rejected)** |
| Challenge / Learning | low | low (no change) |

## References

- [rapidfuzz documentation](https://rapidfuzz.github.io/RapidFuzz/)
- [token_set_ratio explanation](https://rapidfuzz.github.io/RapidFuzz/Usage/fuzz.html#token-set-ratio)
- Handler: `src/contexts/coding/interface/handlers/duplicate_handlers.py`
