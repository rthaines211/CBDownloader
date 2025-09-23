# CBDownloader

CBDownloader is a small toolkit for assembling comic books from remote image
assets. The package downloads the requested pages and bundles them into a CBZ
archive using sensible defaults for file naming and ordering.

## Features

* Page downloads backed by `requests` with optional per-page headers.
* Automatic filename generation with collision handling.
* Smart extension detection based on content type, custom filenames or source
  URLs.
* Simple API that returns a ready-to-use CBZ archive or exposes it through a
  lightweight HTTP server.

## Installation

Create a virtual environment and install the package in editable mode:

```shell
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

To install the optional dependencies required for the HTTP server (see below)
use:

```shell
pip install -e ".[web]"
```

For development work you can install everything, including test tooling, with:

```shell
pip install -e ".[dev,web]"
```

## Library usage

The package exposes a small API that accepts a comic title, a list of pages to
download, and an output directory. Each page is described by a `PageSpec`
containing the URL and optional headers or an explicit filename.

```python
from cbdownloader import ComicBookDownloader, PageSpec

downloader = ComicBookDownloader()
archive_path = downloader.download_cbz(
    "Amazing Adventures #1",
    [
        PageSpec(url="https://example.com/pages/1.jpg"),
        PageSpec(url="https://example.com/pages/2.jpg", filename="hero.jpg"),
    ],
    "./downloads",
)
print(f"Created archive at {archive_path}")
```

Each archive is written to the output directory with a filename derived from
the issue name. Existing files are overwritten.

## Running the web server

CBDownloader ships with a small Flask-based web service that wraps the
`ComicBookDownloader`. After installing the optional `web` extra, start the
server with:

```shell
python -m cbdownloader.webserver --output-dir ./downloads
```

The server exposes two endpoints:

* `GET /health` – returns `{"status": "ok"}` when the service is available.
* `POST /download` – accepts a JSON payload describing the comic to download.

Example request using `curl`:

```shell
curl -X POST http://127.0.0.1:8000/download \
    -H "Content-Type: application/json" \
    -d '{
          "title": "Amazing Adventures #1",
          "pages": [
            {"url": "https://example.com/pages/1.jpg"},
            {"url": "https://example.com/pages/2.jpg", "filename": "hero.jpg"}
          ]
        }'
```

Once the server is running you can simply open http://127.0.0.1:8000/ to access
the built-in UI. The interface lets you:

* Change the default download folder that is used when no explicit
  `output_dir` is supplied in requests.
* Describe each page to fetch through a friendly form and trigger a CBZ build
  directly from the browser.
* Inspect success or failure messages without having to drop down to curl.

`output_dir` defaults to the value supplied via `--output-dir` but can be
overridden per request by including an `"output_dir"` field in the JSON body or
by updating the default via the UI (or a `POST /config/output-dir` call).

## Running with Docker

CBDownloader also ships with a container image definition so you can run the
HTTP API without installing Python locally.

Build the image (from the project root) with:

```shell
docker build -t cbdownloader .
```

The container exposes port 8000 and writes generated CBZ archives to `/data`.
Start it with the port published to your host and a volume for downloads:

```shell
docker run --rm -p 8000:8000 -v "$(pwd)/downloads:/data" cbdownloader
```

Once the container is running the API is available at
`http://localhost:8000`. The bound volume will contain the generated CBZ files.
To customise the port or output directory, override the container command, for
example:

```shell
docker run --rm -p 8080:8080 cbdownloader --port 8080 --output-dir /tmp/output
```

## Development

Run the tests after installing the development dependencies:

```shell
pytest
```
