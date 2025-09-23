# CBDownloader

CBDownloader is a small toolkit for assembling comic books from remote image
assets. The package downloads the requested pages and bundles them into a CBZ
archive using sensible defaults for file naming and ordering.

## Current features

* Download remote comic pages and assemble them into CBZ archives with automatic naming and extension detection.
* Follow GetComics Direct Download links to fetch ready-made archives with optional filename overrides.
* Provide per-page configuration including custom filenames and HTTP headers for advanced sources.
* Expose a browser UI and JSON API for configuring downloads, folders, and viewing status updates.
* Run the service inside a Docker container so it can be deployed without a local Python environment.

## Planned features

* Queue multiple comics and process them sequentially with progress tracking in the UI.
* Import metadata from comic databases to pre-fill titles, cover images, and series information.
* Integrate additional content sources such as shared drives or authenticated cloud buckets.
* Support alternative archive formats like PDF and CBR alongside CBZ output.
* Offer optional authentication and API tokens for shared or hosted deployments.

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

### Direct downloads from GetComics

Some distributors such as [GetComics](https://getcomics.org) host complete CBZ
archives behind a "Direct Download" button. CBDownloader can follow that flow
for you:

```python
from cbdownloader import ComicBookDownloader

downloader = ComicBookDownloader()
archive_path = downloader.download_direct_archive(
    "https://getcomics.org/marvel/marvel-dc-deadpool-batman-1-2025/",
    "./downloads",
)
print(f"Fetched archive from GetComics to {archive_path}")
```

Pass a `filename="My Comic.cbz"` argument if you want to override the
automatically detected name.

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
* Provide a GetComics issue page URL so the server can follow the Direct
  Download link automatically.
* Describe each page to fetch through a friendly form and trigger a CBZ build
  directly from the browser when you want full control.
* Inspect success or failure messages without having to drop down to curl.

`output_dir` defaults to the value supplied via `--output-dir` but can be
overridden per request by including an `"output_dir"` field in the JSON body or
by updating the default via the UI (or a `POST /config/output-dir` call).

When calling the API programmatically you can also submit a JSON payload with a
`"source_url"` key instead of a `"pages"` list. The service will treat the value
as a GetComics issue page and download the resulting archive on your behalf.

### Feature catalog

The home page now highlights the feature roadmap so you can quickly see what is
available today and which improvements are coming next. The same information is
also exposed through the JSON API:

```shell
curl http://127.0.0.1:8000/features
```

The endpoint returns a structure containing the `current` and `future`
feature lists, matching the bullets above.

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
