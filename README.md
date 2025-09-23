# CBDownloader

CBDownloader is a small toolkit for assembling comic books from remote image
assets. The package downloads the requested pages and bundles them into a CBZ
archive using sensible defaults for file naming and ordering.

## Features

* Page downloads backed by `requests` with optional per-page headers.
* Automatic filename generation with collision handling.
* Smart extension detection based on content type, custom filenames or source
  URLs.


```python
from cbdownloader import ComicBookDownloader, PageSpec

downloader = ComicBookDownloader()
archive_path = downloader.download_cbz(
    "Amazing Adventures #1",
    [
        PageSpec(url="https://example.com/pages/1.jpg"),
        PageSpec(url="https://example.com/pages/2.jpg", filename="hero.jpg"),
    ],

)
print(f"Created archive at {archive_path}")
```

\pytest
```
