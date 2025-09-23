"""Feature catalogue describing current and planned capabilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

CURRENT_FEATURES: Tuple[str, ...] = (
    "Download remote comic pages and assemble them into CBZ archives with automatic naming and extension detection.",
    "Follow GetComics Direct Download links to fetch ready-made archives with optional filename overrides.",
    "Provide per-page configuration including custom filenames and HTTP headers for advanced sources.",
    "Expose a browser UI and JSON API for configuring downloads, folders, and viewing status updates.",
    "Run the service inside a Docker container so it can be deployed without a local Python environment.",
)

FUTURE_FEATURES: Tuple[str, ...] = (
    "Queue multiple comics and process them sequentially with progress tracking in the UI.",
    "Import metadata from comic databases to pre-fill titles, cover images, and series information.",
    "Integrate additional content sources such as shared drives or authenticated cloud buckets.",
    "Support alternative archive formats like PDF and CBR alongside CBZ output.",
    "Offer optional authentication and API tokens for shared or hosted deployments.",
)


@dataclass(frozen=True)
class FeatureCatalog:
    """Immutable representation of the downloader feature roadmap."""

    current: Tuple[str, ...]
    future: Tuple[str, ...]

    def to_dict(self) -> Dict[str, List[str]]:
        """Return a serialisable dictionary of the catalogue."""

        return {
            "current": list(self.current),
            "future": list(self.future),
        }


def get_current_features() -> List[str]:
    """Return a copy of the current feature list."""

    return list(CURRENT_FEATURES)


def get_future_features() -> List[str]:
    """Return a copy of the planned feature list."""

    return list(FUTURE_FEATURES)


def get_feature_catalog() -> FeatureCatalog:
    """Build a :class:`FeatureCatalog` combining current and future items."""

    return FeatureCatalog(current=CURRENT_FEATURES, future=FUTURE_FEATURES)

