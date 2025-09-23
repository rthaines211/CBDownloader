"""Top level package for CBDownloader.

This module exposes the primary entry points for the comic book
Downloader functionality implemented in :mod:`cbdownloader.downloader`.
"""

from .downloader import ComicBookDownloader, DownloadError, PageSpec
from .features import FeatureCatalog, get_current_features, get_feature_catalog, get_future_features

__all__ = [
    "ComicBookDownloader",
    "DownloadError",
    "FeatureCatalog",
    "PageSpec",
    "get_current_features",
    "get_feature_catalog",
    "get_future_features",
]
