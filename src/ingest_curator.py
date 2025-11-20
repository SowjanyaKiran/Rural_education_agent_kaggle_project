# src/ingest_curator.py
"""
Resource ingestion and simple curation utilities.
Expect a CSV with: id, url, title, language, size_kb, tags
"""

import pandas as pd
from typing import List


def read_resource_manifest(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    expected = ["id", "url", "title", "language", "size_kb", "tags"]
    for c in expected:
        if c not in df.columns:
            df[c] = None
    return df[expected]


def filter_by_bandwidth(df: pd.DataFrame, max_size_kb: int) -> pd.DataFrame:
    """Return resources smaller than or equal to max_size_kb"""
    return df[df["size_kb"].fillna(0) <= max_size_kb].copy()


def sample_resources_for_demo(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Return a random subset of n resources."""
    return df.sample(min(n, len(df))).reset_index(drop=True)


# ---------------------------------------------------------
# MAIN BLOCK → Runs when executing: python ingest_curator.py
# ---------------------------------------------------------
if __name__ == "__main__":
    print("\nRunning ingest_curator.py directly...\n")

    # Path to CSV relative to this file
    csv_path = "../data/sample_resources.csv"

    print(f"Loading resource manifest from: {csv_path}")
    df = read_resource_manifest(csv_path)

    print("\n🔹 Full DataFrame:")
    print(df)

    print("\n🔹 Filtered resources (<=150 KB):")
    small = filter_by_bandwidth(df, max_size_kb=150)
    print(small)

    print("\n🔹 Random sample of 3 resources:")
    sample = sample_resources_for_demo(df, n=3)
    print(sample)

    print("\nDone.\n")
