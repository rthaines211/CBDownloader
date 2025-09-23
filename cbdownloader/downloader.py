"""Utilities for downloading comic book pages and packaging them as CBZ files."""

from __future__ import annotations

from dataclasses import dataclass
import mimetypes
from pathlib import Path
import re
from typing import Iterable, Mapping, MutableSet, Sequence
from urllib.parse import urlparse
import zipfile

import requests

__all__ = ["ComicBookDownloader", "DownloadError", "PageSpec"]


class DownloadError(RuntimeError):
    """Raised when the downloader fails to retrieve a page."""


@dataclass(frozen=True)
class PageSpec:
    """Specification describing a single comic book page.

    Parameters
    ----------
    url:
        The URL pointing to the page asset.
    filename:
        Optional explicit filename to use within the archive. If omitted the
        downloader will derive a name based on the page order and the content
        type.
    headers:
        Optional HTTP headers to be sent when requesting the resource. This is
        useful for APIs that require additional information such as auth
        tokens.
    """

    url: str
    filename: str | None = None
    headers: Mapping[str, str] | None = None


class ComicBookDownloader:
    """Download comic pages and build a CBZ archive."""

    _AMBIGUOUS_EXTENSIONS = frozenset({".bin", ".html", ".htm", ".txt"})

    def __init__(
        self,
        *,
        session: requests.Session | None = None,
        timeout: float | tuple[float, float] | None = 10.0,
        chunk_size: int = 32 * 1024,
        default_headers: Mapping[str, str] | None = None,
    ) -> None:
        """Create a new :class:`ComicBookDownloader` instance.

        Parameters
        ----------
        session:
            Optional pre-configured :class:`requests.Session` used for network
            requests. A new session is created if omitted.
        timeout:
            Timeout value forwarded to :func:`requests.get`.
        chunk_size:
            Number of bytes read at a time while streaming responses. This
            mainly exists to make tests deterministic, it is not exposed as a
            public attribute.
        default_headers:
            Headers merged into every request.
        """

        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")

        self._session = session or requests.Session()
        self._timeout = timeout
        self._chunk_size = chunk_size
        self._default_headers = dict(default_headers or {})

    def download_cbz(
        self,
        issue_name: str,
        pages: Sequence[PageSpec] | Iterable[PageSpec],
        output_dir: str | Path,
    ) -> Path:
        """Download ``pages`` and package them as a CBZ archive.

        Parameters
        ----------
        issue_name:
            The friendly name for the issue. It is converted into a filesystem
            safe file name for the resulting archive.
        pages:
            Iterable of :class:`PageSpec` objects describing the pages to
            download. Each page is stored sequentially in the order provided.
        output_dir:
            Destination folder. It will be created if it does not already
            exist.

        Returns
        -------
        pathlib.Path
            Path to the created CBZ file.

        Raises
        ------
        ValueError
            If ``issue_name`` is empty or ``pages`` is empty.
        DownloadError
            If any of the pages cannot be retrieved.
        """

        if not issue_name:
            raise ValueError("issue_name must be provided")

        page_list = list(pages)
        if not page_list:
            raise ValueError("pages must contain at least one item")

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        archive_path = output_path / f"{self._slugify(issue_name)}.cbz"

        seen_names: MutableSet[str] = set()
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
            total = len(page_list)
            for index, page in enumerate(page_list, start=1):
                data, extension = self._fetch_page(page)
                filename = self._determine_filename(page, index, total, extension, seen_names)
                info = zipfile.ZipInfo(filename)
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, data)

        return archive_path

    # ------------------------------------------------------------------
    # Helper methods
    def _fetch_page(self, page: PageSpec) -> tuple[bytes, str]:
        headers = dict(self._default_headers)
        if page.headers:
            headers.update(page.headers)

        content_type: str | None = None
        try:
            with self._session.get(
                page.url,
                headers=headers,
                timeout=self._timeout,
                stream=True,
            ) as response:
                response.raise_for_status()
                content = self._read_response(response)
                content_type = response.headers.get("Content-Type")
        except requests.RequestException as exc:  # pragma: no cover - exercised in tests
            raise DownloadError(f"Failed to download {page.url}") from exc

        filename_ext = self._extension_from_filename(page.filename)
        url_ext = self._extension_from_url(page.url)
        content_type_ext = self._extension_from_content_type(content_type)

        extension = self._choose_extension(filename_ext, url_ext, content_type_ext)

        return content, extension

    def _read_response(self, response: requests.Response) -> bytes:
        chunks = []
        for chunk in response.iter_content(self._chunk_size):
            if chunk:  # filter out keep-alive chunks
                chunks.append(chunk)
        return b"".join(chunks)

    @staticmethod
    def _extension_from_content_type(content_type: str | None) -> str | None:
        if not content_type:
            return None
        mime = content_type.split(";", 1)[0].strip().lower()
        if not mime:
            return None
        extension = mimetypes.guess_extension(mime)
        if extension == ".jpe":
            return ".jpg"
        if extension:
            return extension
        return None

    @staticmethod
    def _extension_from_filename(filename: str | None) -> str | None:
        if not filename:
            return None
        match = re.search(r"\.([A-Za-z0-9]+)$", filename)
        if match:
            return f".{match.group(1)}"
        return None

    @staticmethod
    def _extension_from_url(url: str) -> str | None:
        path = urlparse(url).path
        filename = path.rsplit("/", 1)[-1]
        if "." in filename:
            suffix = filename.rsplit(".", 1)[-1]
            if suffix:
                return f".{suffix}"
        return None

    @classmethod
    def _choose_extension(
        cls,
        filename_ext: str | None,
        url_ext: str | None,
        content_type_ext: str | None,
    ) -> str:
        if filename_ext:
            return filename_ext
        if content_type_ext and content_type_ext not in cls._AMBIGUOUS_EXTENSIONS:
            return content_type_ext
        if url_ext:
            return url_ext
        if content_type_ext:
            return content_type_ext
        return ".bin"

    @staticmethod
    def _determine_filename(
        page: PageSpec,
        index: int,
        total: int,
        extension: str,
        seen_names: MutableSet[str],
    ) -> str:
        if page.filename:
            base_name = ComicBookDownloader._sanitize_filename(page.filename)
            if not ComicBookDownloader._extension_from_filename(base_name):
                base_name = f"{base_name}{extension}"
        else:
            width = max(3, len(str(total)))
            base_name = f"{index:0{width}d}{extension}"

        unique_name = ComicBookDownloader._dedupe_filename(base_name, seen_names)
        seen_names.add(unique_name.lower())
        return unique_name

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        cleaned = re.sub(r"[\\/:*?\"<>|]", "_", name)
        cleaned = cleaned.replace(" ", "_")
        cleaned = re.sub(r"_+", "_", cleaned)
        cleaned = cleaned.strip("._")
        return cleaned or "page"

    @staticmethod
    def _dedupe_filename(name: str, seen_names: MutableSet[str]) -> str:
        candidate = name
        base, dot, ext = candidate.rpartition(".")
        base = base if dot else candidate
        ext = f"{dot}{ext}" if dot else ""

        counter = 1
        lowered = candidate.lower()
        while lowered in seen_names:
            candidate = f"{base}_{counter}{ext}"
            counter += 1
            lowered = candidate.lower()
        return candidate

    @staticmethod
    def _slugify(value: str) -> str:
        text = value.strip().lower()
        text = re.sub(r"[^a-z0-9]+", "_", text)
        text = text.strip("_")
        return text or "issue"
