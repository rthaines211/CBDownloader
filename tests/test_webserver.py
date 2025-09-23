from __future__ import annotations

import json

import pytest

from cbdownloader.downloader import DownloadError, PageSpec
from cbdownloader.webserver import create_app


class DummyDownloader:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[tuple[str, list[PageSpec], str]] = []

    def download_cbz(self, title: str, pages: list[PageSpec], output_dir: str):
        if self.fail:
            raise DownloadError("boom")
        self.calls.append((title, pages, output_dir))
        return f"{output_dir}/result.cbz"


@pytest.fixture()
def client(tmp_path):
    downloader = DummyDownloader()
    app = create_app(downloader, default_output_dir=str(tmp_path))
    with app.test_client() as client:
        client.downloader = downloader  # type: ignore[attr-defined]
        client.tmp_path = tmp_path  # type: ignore[attr-defined]
        yield client


def post_json(client, url: str, payload: dict[str, object]):
    return client.post(url, data=json.dumps(payload), content_type="application/json")


def test_download_success(client):
    response = post_json(
        client,
        "/download",
        {
            "title": "Amazing Adventures #1",
            "pages": [
                {"url": "https://example.com/1.jpg"},
                {"url": "https://example.com/2.jpg", "filename": "hero.jpg"},
            ],
        },
    )

    assert response.status_code == 201
    assert response.get_json() == {
        "archive_path": f"{client.tmp_path}/result.cbz"
    }
    assert client.downloader.calls == [
        (
            "Amazing Adventures #1",
            [
                PageSpec(url="https://example.com/1.jpg", filename=None, headers=None),
                PageSpec(url="https://example.com/2.jpg", filename="hero.jpg", headers=None),
            ],
            str(client.tmp_path),
        )
    ]


def test_download_allows_override_output_dir(client):
    response = post_json(
        client,
        "/download",
        {
            "title": "Amazing Adventures #2",
            "output_dir": "./custom",
            "pages": [{"url": "https://example.com/1.jpg"}],
        },
    )

    assert response.status_code == 201
    assert client.downloader.calls[0][2] == "./custom"


def test_index_serves_ui(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.content_type
    body = response.get_data(as_text=True)
    assert "CBDownloader" in body
    assert "Create a CBZ archive" in body


def test_get_config_returns_default(client):
    response = client.get("/config")

    assert response.status_code == 200
    assert response.get_json() == {"default_output_dir": str(client.tmp_path)}


def test_update_default_output_dir(client):
    response = client.post("/config/output-dir", json={"output_dir": "./changed"})

    assert response.status_code == 200
    assert response.get_json() == {"default_output_dir": "./changed"}

    response = post_json(
        client,
        "/download",
        {
            "title": "Amazing Adventures #4",
            "pages": [{"url": "https://example.com/1.jpg"}],
        },
    )

    assert response.status_code == 201
    assert client.downloader.calls[-1][2] == "./changed"


def test_download_validation_errors(client):
    response = post_json(client, "/download", {})

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_download_handles_downloader_errors(tmp_path):
    downloader = DummyDownloader(fail=True)
    app = create_app(downloader, default_output_dir=str(tmp_path))

    with app.test_client() as client:
        response = post_json(
            client,
            "/download",
            {
                "title": "Amazing Adventures #3",
                "pages": [{"url": "https://example.com/1.jpg"}],
            },
        )

    assert response.status_code == 502
    assert response.get_json() == {"error": "boom"}
