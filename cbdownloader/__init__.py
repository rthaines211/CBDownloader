"""Top level package for CBDownloader.

This module exposes the primary entry points for the comic book
Downloader functionality implemented in :mod:`cbdownloader.downloader`.
"""

from .downloader import ComicBookDownloader, DownloadError, PageSpec

__all__ = ["ComicBookDownloader", "DownloadError", "PageSpec"]
