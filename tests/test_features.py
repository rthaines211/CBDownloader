from __future__ import annotations

from cbdownloader.features import (
    FeatureCatalog,
    get_current_features,
    get_feature_catalog,
    get_future_features,
)


EXPECTED_CURRENT_FEATURES = [
    "Download remote comic pages and assemble them into CBZ archives with automatic naming and extension detection.",
    "Follow GetComics Direct Download links to fetch ready-made archives with optional filename overrides.",
    "Provide per-page configuration including custom filenames and HTTP headers for advanced sources.",
    "Expose a browser UI and JSON API for configuring downloads, folders, and viewing status updates.",
    "Run the service inside a Docker container so it can be deployed without a local Python environment.",
]

EXPECTED_FUTURE_FEATURES = [
    "Queue multiple comics and process them sequentially with progress tracking in the UI.",
    "Import metadata from comic databases to pre-fill titles, cover images, and series information.",
    "Integrate additional content sources such as shared drives or authenticated cloud buckets.",
    "Support alternative archive formats like PDF and CBR alongside CBZ output.",
    "Offer optional authentication and API tokens for shared or hosted deployments.",
]


def test_get_current_features_returns_copy():
    current = get_current_features()
    assert current == EXPECTED_CURRENT_FEATURES

    current.append("extra")
    assert get_current_features() == EXPECTED_CURRENT_FEATURES


def test_get_future_features_returns_copy():
    future = get_future_features()
    assert future == EXPECTED_FUTURE_FEATURES

    future.append("extra")
    assert get_future_features() == EXPECTED_FUTURE_FEATURES


def test_get_feature_catalog_structure():
    catalog = get_feature_catalog()
    assert isinstance(catalog, FeatureCatalog)
    assert catalog.current == tuple(EXPECTED_CURRENT_FEATURES)
    assert catalog.future == tuple(EXPECTED_FUTURE_FEATURES)
    assert catalog.to_dict() == {
        "current": EXPECTED_CURRENT_FEATURES,
        "future": EXPECTED_FUTURE_FEATURES,
    }
