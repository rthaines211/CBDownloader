from __future__ import annotations

import zipfile
from pathlib import Path

import pytest
import responses

from cbdownloader import ComicBookDownloader, DownloadError, PageSpec


@responses.activate
def test_download_cbz_creates_archive(tmp_path: Path) -> None:
    downloader = ComicBookDownloader()

    responses.add(
        responses.GET,
        "https://example.com/issue1/page1.jpg",
        body=b"image-one",
        status=200,
        content_type="image/jpeg",
    )
    responses.add(
        responses.GET,
        "https://example.com/issue1/page2.jpg",
        body=b"image-two",
        status=200,
        content_type="image/jpeg",
    )
    responses.add(
        responses.GET,
        "https://example.com/issue1/page3",
        body=b"image-three",
        status=200,
        content_type="image/png",
    )

    archive = downloader.download_cbz(
        "Issue #1: Dawn of Testing",
        [
            PageSpec(url="https://example.com/issue1/page1.jpg"),
            PageSpec(url="https://example.com/issue1/page2.jpg", filename="page 2"),
            PageSpec(url="https://example.com/issue1/page3", filename="custom-name.png"),
        ],
        tmp_path,
    )

    assert archive.exists()
    assert archive.name == "issue_1_dawn_of_testing.cbz"

    with zipfile.ZipFile(archive) as zf:
        assert zf.namelist() == ["001.jpg", "page_2.jpg", "custom-name.png"]
        assert zf.read("001.jpg") == b"image-one"
        assert zf.read("page_2.jpg") == b"image-two"
        assert zf.read("custom-name.png") == b"image-three"


@responses.activate
def test_download_cbz_raises_on_http_error(tmp_path: Path) -> None:
    downloader = ComicBookDownloader()

    responses.add(
        responses.GET,
        "https://example.com/failure",
        status=500,
    )

    with pytest.raises(DownloadError):
        downloader.download_cbz(
            "Issue",
            [PageSpec(url="https://example.com/failure")],
            tmp_path,
        )


@responses.activate
def test_duplicate_filenames_are_deduped(tmp_path: Path) -> None:
    downloader = ComicBookDownloader()

    responses.add(
        responses.GET,
        "https://example.com/page1",
        body=b"a",
        status=200,
        content_type="image/jpeg",
    )
    responses.add(
        responses.GET,
        "https://example.com/page2",
        body=b"b",
        status=200,
        content_type="image/jpeg",
    )

    archive = downloader.download_cbz(
        "Issue",
        [
            PageSpec(url="https://example.com/page1", filename="Same.png"),
            PageSpec(url="https://example.com/page2", filename="Same.png"),
        ],
        tmp_path,
    )

    with zipfile.ZipFile(archive) as zf:
        assert zf.namelist() == ["Same.png", "Same_1.png"]
        assert zf.read("Same.png") == b"a"
        assert zf.read("Same_1.png") == b"b"


@responses.activate
def test_extension_falls_back_to_url(tmp_path: Path) -> None:
    downloader = ComicBookDownloader()

    responses.add(
        responses.GET,
        "https://cdn.example.com/book/page1.webp",
        body=b"data",
        status=200,
    )

    archive = downloader.download_cbz(
        "Issue",
        [PageSpec(url="https://cdn.example.com/book/page1.webp")],
        tmp_path,
    )

    with zipfile.ZipFile(archive) as zf:
        assert zf.namelist() == ["001.webp"]


def test_download_cbz_validates_input(tmp_path: Path) -> None:
    downloader = ComicBookDownloader()

    with pytest.raises(ValueError):
        downloader.download_cbz("", [PageSpec(url="https://example.com")], tmp_path)

    with pytest.raises(ValueError):
        downloader.download_cbz("Issue", [], tmp_path)


@responses.activate
def test_download_direct_archive_success(tmp_path: Path) -> None:
    downloader = ComicBookDownloader()

    responses.add(
        responses.GET,
        "https://getcomics.org/book/issue",
        body="""
        <html>
            <body>
                <a href="https://cdn.getcomics.org/files/issue.cbz">
                    <span>Direct Download</span>
                </a>
            </body>
        </html>
        """,
        status=200,
        content_type="text/html",
    )

    responses.add(
        responses.GET,
        "https://cdn.getcomics.org/files/issue.cbz",
        body=b"binary-data",
        status=200,
        headers={"Content-Disposition": 'attachment; filename="Deadpool.cbz"'},
        content_type="application/octet-stream",
    )

    archive = downloader.download_direct_archive(
        "https://getcomics.org/book/issue",
        tmp_path,
    )

    assert archive.exists()
    assert archive.read_bytes() == b"binary-data"
    assert archive.name == "Deadpool.cbz"


@responses.activate
def test_download_direct_archive_errors_without_link(tmp_path: Path) -> None:
    downloader = ComicBookDownloader()

    responses.add(
        responses.GET,
        "https://getcomics.org/book/issue",
        body="<html><body><p>No direct link here</p></body></html>",
        status=200,
        content_type="text/html",
    )

    with pytest.raises(DownloadError):
        downloader.download_direct_archive(
            "https://getcomics.org/book/issue",
            tmp_path,
        )


@responses.activate
def test_download_direct_archive_uses_custom_filename(tmp_path: Path) -> None:
    downloader = ComicBookDownloader()

    responses.add(
        responses.GET,
        "https://getcomics.org/book/issue",
        body='<a href="/files/direct">Direct Download</a>',
        status=200,
        content_type="text/html",
    )

    responses.add(
        responses.GET,
        "https://getcomics.org/files/direct",
        body=b"content",
        status=200,
        content_type="application/octet-stream",
    )

    archive = downloader.download_direct_archive(
        "https://getcomics.org/book/issue",
        tmp_path,
        filename="My Comic.cbz",
    )

    assert archive.name == "My_Comic.cbz"
    assert archive.read_bytes() == b"content"
