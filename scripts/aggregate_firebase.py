#!/usr/bin/env python3
"""
Aggregate Firebase Analytics Export

Starter script for transforming raw Firebase BigQuery exports
into participant profiles suitable for QualCoder case attributes.

Usage:
    python scripts/aggregate_firebase.py \
        --input raw/firebase_export.json \
        --output processed/participant_profiles.csv

Input format (Firebase BigQuery export JSON):
    {"events": [{"name": "session_start", "user_pseudo_id": "u001", ...}, ...]}

Output format (CSV for QualCoder import):
    participant_id,sessions,engagement_tier,first_seen,last_seen
    u001,12,power_user,2024-01-15,2024-03-01
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path


def aggregate(input_path: Path, output_path: Path) -> None:
    """Aggregate Firebase events into per-user profiles."""
    with open(input_path) as f:
        data = json.load(f)

    events = data.get("events", [])
    if not events:
        print(f"No events found in {input_path}", file=sys.stderr)
        sys.exit(1)

    # Aggregate by user
    users: dict[str, dict] = defaultdict(
        lambda: {"sessions": 0, "events": 0, "first_seen": None, "last_seen": None}
    )

    for event in events:
        uid = event.get("user_pseudo_id") or event.get("user", "unknown")
        users[uid]["events"] += 1
        if event.get("name") == "session_start":
            users[uid]["sessions"] += 1

    # Derive engagement tiers
    profiles = []
    for uid, stats in sorted(users.items()):
        sessions = stats["sessions"]
        if sessions >= 10:
            tier = "power_user"
        elif sessions >= 3:
            tier = "regular"
        else:
            tier = "casual"

        profiles.append(
            {
                "participant_id": uid,
                "sessions": sessions,
                "total_events": stats["events"],
                "engagement_tier": tier,
            }
        )

    # Write CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "participant_id",
                "sessions",
                "total_events",
                "engagement_tier",
            ],
        )
        writer.writeheader()
        writer.writerows(profiles)

    print(f"Wrote {len(profiles)} participant profiles to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Aggregate Firebase Analytics export")
    parser.add_argument("--input", required=True, help="Path to Firebase export JSON")
    parser.add_argument("--output", required=True, help="Path to output CSV")
    args = parser.parse_args()

    aggregate(Path(args.input), Path(args.output))


if __name__ == "__main__":
    main()
