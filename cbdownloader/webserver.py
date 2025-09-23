"""Minimal web server exposing the comic book downloader as an HTTP API."""

from __future__ import annotations

import argparse
from typing import Any, Dict, Iterable

from flask import Flask, jsonify, render_template_string, request

from .downloader import ComicBookDownloader, DownloadError, PageSpec
from .features import get_feature_catalog

__all__ = ["create_app", "main"]


INDEX_TEMPLATE = """<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\">
    <title>CBDownloader</title>
    <style>
      :root {
        color-scheme: light dark;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif;
        background: #f7f7f9;
      }

      body {
        margin: 0 auto;
        max-width: 900px;
        padding: 2rem 1.5rem 4rem;
        line-height: 1.5;
        color: #222;
        background: inherit;
      }

      h1,
      h2 {
        font-weight: 600;
      }

      form,
      .card {
        margin-bottom: 2.5rem;
        background: #fff;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 12px 40px rgba(15, 23, 42, 0.12);
      }

      label {
        font-weight: 600;
      }

      input[type=\"text\"],
      textarea {
        width: 100%;
        padding: 0.6rem 0.75rem;
        margin-top: 0.25rem;
        border-radius: 8px;
        border: 1px solid rgba(15, 23, 42, 0.15);
        background: rgba(255, 255, 255, 0.9);
        font-family: inherit;
        font-size: 1rem;
        box-sizing: border-box;
      }

      textarea {
        min-height: 4rem;
      }

      button {
        padding: 0.6rem 1.1rem;
        border: none;
        border-radius: 999px;
        background: linear-gradient(135deg, #2563eb, #7c3aed);
        color: #fff;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        box-shadow: 0 12px 30px rgba(59, 130, 246, 0.35);
        transition: transform 120ms ease, box-shadow 120ms ease;
      }

      button:hover {
        transform: translateY(-1px);
        box-shadow: 0 16px 40px rgba(59, 130, 246, 0.3);
      }

      button.secondary {
        background: transparent;
        color: #2563eb;
        border: 1px solid rgba(37, 99, 235, 0.35);
        box-shadow: none;
        margin-left: 0.75rem;
      }

      button.secondary:hover {
        transform: none;
        background: rgba(37, 99, 235, 0.08);
      }

      .feature-list {
        margin: 0.5rem 0 1.5rem;
        padding-left: 1.25rem;
      }

      .feature-list li {
        margin-bottom: 0.35rem;
      }

      #feature-catalog h3 {
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
        font-size: 1.05rem;
      }

      #feature-catalog h3:first-of-type {
        margin-top: 1rem;
      }

      .page {
        padding: 1rem;
        border: 1px solid rgba(15, 23, 42, 0.08);
        border-radius: 10px;
        margin-top: 1rem;
        background: rgba(241, 245, 249, 0.5);
      }

      .page h3 {
        margin-top: 0;
        font-size: 1rem;
      }

      .status {
        padding: 1rem;
        border-radius: 10px;
        margin-top: 1rem;
        white-space: pre-wrap;
        word-break: break-word;
        background: rgba(14, 165, 233, 0.12);
        border: 1px solid rgba(14, 165, 233, 0.2);
      }

      .status.error {
        background: rgba(239, 68, 68, 0.1);
        border-color: rgba(239, 68, 68, 0.2);
      }

      .actions {
        margin-top: 1rem;
      }

      .pages-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        flex-wrap: wrap;
      }

      .pages-header button {
        margin: 0;
      }

      .small {
        color: rgba(15, 23, 42, 0.6);
        font-size: 0.9rem;
      }
    </style>
  </head>
  <body>
    <h1>CBDownloader</h1>
    <p class=\"small\">Use the form below to configure your default output folder, describe the comic book you want to download and trigger a build of the CBZ archive. The web API stays fully functional for automation.</p>

    <form id=\"config-form\" autocomplete=\"off\">
      <h2>Default output folder</h2>
      <label for=\"config-output\">Folder path</label>
      <input id=\"config-output\" name=\"config-output\" type=\"text\" required>
      <div class=\"actions\">
        <button type=\"submit\">Update default folder</button>
      </div>
      <div id=\"config-status\" class=\"status\" hidden></div>
    </form>

    <section id=\"feature-catalog\" class=\"card\">
      <h2>Feature roadmap</h2>
      <p class=\"small\">See what CBDownloader already supports today and which improvements are planned for the near future.</p>
      <h3>Current capabilities</h3>
      <ul id=\"current-features\" class=\"feature-list\"></ul>
      <h3>Planned additions</h3>
      <ul id=\"future-features\" class=\"feature-list\"></ul>
      <div id=\"feature-status\" class=\"status\" hidden></div>
    </section>

    <form id=\"download-form\" autocomplete=\"off\">
      <h2>Create a CBZ archive</h2>
      <label for=\"title\">Issue title</label>
      <input id=\"title\" name=\"title\" type=\"text\" placeholder=\"Amazing Adventures #1\" required>

      <label for=\"output-dir\">Output folder</label>
      <input id=\"output-dir\" name=\"output-dir\" type=\"text\" required>

      <label for=\"source-url\">Issue page URL <span class=\"small\">(optional)</span></label>
      <input id=\"source-url\" name=\"source-url\" type=\"text\" placeholder=\"https://getcomics.org/...\">
      <p class=\"small\">Provide a GetComics issue page link to automatically follow the <strong>Direct Download</strong> button. Leave this blank to describe the comic page-by-page below.</p>

      <label for=\"direct-filename\">Archive filename <span class=\"small\">(optional)</span></label>
      <input id=\"direct-filename\" name=\"direct-filename\" type=\"text\" placeholder=\"My Comic.cbz\">

      <div class=\"pages-header\">
        <h2>Pages</h2>
        <button id=\"add-page\" class=\"secondary\" type=\"button\">Add page</button>
      </div>
      <p class=\"small\">Provide at least one page. Each page must have a URL and can optionally include a filename override. Headers are an advanced option and accept JSON (e.g. <code>{\"Authorization\": \"Bearer ...\"}</code>).</p>
      <div id=\"pages\"></div>

      <div class=\"actions\">
        <button type=\"submit\">Download comic</button>
      </div>
      <div id=\"result\" class=\"status\" hidden></div>
    </form>

    <template id=\"page-template\">
      <div class=\"page\">
        <h3>Page <span class=\"page-index\"></span></h3>
        <label>Image URL</label>
        <input type=\"text\" name=\"url\" required placeholder=\"https://...\">
        <label>Filename override <span class=\"small\">(optional)</span></label>
        <input type=\"text\" name=\"filename\" placeholder=\"cover.jpg\">
        <label>Headers <span class=\"small\">(optional, JSON object)</span></label>
        <textarea name=\"headers\" placeholder=\"{\"Referer\": \"https://example.com\"}\"></textarea>
        <div class=\"actions\">
          <button class=\"secondary remove-page\" type=\"button\">Remove page</button>
        </div>
      </div>
    </template>

    <script>
      const defaultOutputDir = {{ default_output_dir | tojson }};

      const configInput = document.getElementById('config-output');
      const configStatus = document.getElementById('config-status');
      const outputDirInput = document.getElementById('output-dir');
      const sourceUrlInput = document.getElementById('source-url');
      const directFilenameInput = document.getElementById('direct-filename');
      const result = document.getElementById('result');
      const featureStatus = document.getElementById('feature-status');
      const currentFeaturesList = document.getElementById('current-features');
      const futureFeaturesList = document.getElementById('future-features');
      const pagesContainer = document.getElementById('pages');
      const template = document.getElementById('page-template');

      function setStatus(el, message, isError = false) {
        if (!message) {
          el.hidden = true;
          el.textContent = '';
          el.classList.remove('error');
          return;
        }
        el.hidden = false;
        el.textContent = message;
        el.classList.toggle('error', isError);
      }

      function renderFeatureList(target, items) {
        if (!target) {
          return;
        }
        target.innerHTML = '';
        items.forEach((item) => {
          const li = document.createElement('li');
          li.textContent = item;
          target.appendChild(li);
        });
      }

      function pageElements() {
        return Array.from(pagesContainer.querySelectorAll('.page'));
      }

      function renumberPages() {
        pageElements().forEach((el, idx) => {
          el.querySelector('.page-index').textContent = String(idx + 1);
        });
      }

      function addPage(initial = {}) {
        const clone = template.content.cloneNode(true);
        const wrapper = clone.querySelector('.page');
        const [urlInput, filenameInput, headersInput] = wrapper.querySelectorAll('input, textarea');
        urlInput.value = initial.url || '';
        filenameInput.value = initial.filename || '';
        headersInput.value = initial.headers || '';
        wrapper.querySelector('.remove-page').addEventListener('click', () => {
          wrapper.remove();
          renumberPages();
        });
        pagesContainer.appendChild(wrapper);
        renumberPages();
      }

      document.getElementById('add-page').addEventListener('click', () => addPage());

      async function fetchConfig() {
        try {
          const response = await fetch('/config');
          if (!response.ok) {
            throw new Error('Failed to fetch configuration');
          }
          const data = await response.json();
          const folder = data.default_output_dir || '';
          configInput.value = folder;
          if (!outputDirInput.value) {
            outputDirInput.value = folder;
          }
        } catch (err) {
          setStatus(configStatus, err.message, true);
        }
      }

      async function fetchFeatures() {
        try {
          const response = await fetch('/features');
          if (!response.ok) {
            throw new Error('Failed to fetch feature catalogue');
          }
          const data = await response.json();
          const current = Array.isArray(data.current) ? data.current : [];
          const future = Array.isArray(data.future) ? data.future : [];
          renderFeatureList(currentFeaturesList, current);
          renderFeatureList(futureFeaturesList, future);
          if (featureStatus) {
            if (!current.length && !future.length) {
              setStatus(featureStatus, 'No features available yet.', true);
            } else {
              setStatus(featureStatus, '');
            }
          }
        } catch (err) {
          renderFeatureList(currentFeaturesList, []);
          renderFeatureList(futureFeaturesList, []);
          if (featureStatus) {
            setStatus(featureStatus, err.message, true);
          }
        }
      }

      document.getElementById('config-form').addEventListener('submit', async (event) => {
        event.preventDefault();
        const folder = configInput.value.trim();
        if (!folder) {
          setStatus(configStatus, 'Please provide a folder path.', true);
          return;
        }
        try {
          const response = await fetch('/config/output-dir', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({output_dir: folder}),
          });
          const data = await response.json();
          if (!response.ok) {
            throw new Error(data.error || 'Failed to update folder');
          }
          setStatus(configStatus, `Default folder set to ${data.default_output_dir}`);
          if (!outputDirInput.value.trim()) {
            outputDirInput.value = data.default_output_dir;
          }
        } catch (err) {
          setStatus(configStatus, err.message, true);
        }
      });

      document.getElementById('download-form').addEventListener('submit', async (event) => {
        event.preventDefault();
        setStatus(result, '');

        const title = document.getElementById('title').value.trim();
        const outputDir = outputDirInput.value.trim();
        const sourceUrl = sourceUrlInput.value.trim();
        const directFilename = directFilenameInput.value.trim();
        const pages = [];
        let error = null;

        const payload = {title, output_dir: outputDir};

        if (sourceUrl) {
          payload.source_url = sourceUrl;
          if (directFilename) {
            payload.filename = directFilename;
          }
        } else {
          pageElements().forEach((el, idx) => {
            if (error) return;
            const url = el.querySelector('input[name="url"]').value.trim();
            const filename = el.querySelector('input[name="filename"]').value.trim();
            const headersRaw = el.querySelector('textarea[name="headers"]').value.trim();
            if (!url) {
              error = `Page ${idx + 1} is missing a URL.`;
              return;
            }
            const page = {url};
            if (filename) {
              page.filename = filename;
            }
            if (headersRaw) {
              try {
                const parsed = JSON.parse(headersRaw);
                page.headers = parsed;
              } catch (err) {
                error = `Page ${idx + 1} has invalid headers JSON.`;
                return;
              }
            }
            pages.push(page);
          });

          if (error) {
            setStatus(result, error, true);
            return;
          }

          if (!pages.length) {
            setStatus(result, 'Please add at least one page.', true);
            return;
          }

          payload.pages = pages;
        }

        try {
          const response = await fetch('/download', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload),
          });
          const data = await response.json();
          if (!response.ok) {
            throw new Error(data.error || 'Download failed');
          }
          setStatus(result, `✅ Archive created at ${data.archive_path}`);
        } catch (err) {
          setStatus(result, err.message, true);
        }
      });

      addPage();
      if (defaultOutputDir) {
        configInput.value = defaultOutputDir;
        outputDirInput.value = defaultOutputDir;
      }
      fetchFeatures();
      fetchConfig();
    </script>
  </body>
</html>
"""


def create_app(
    downloader: ComicBookDownloader | None = None,
    *,
    default_output_dir: str | None = None,
) -> Flask:
    """Create a Flask application exposing the downloader as an API."""

    app = Flask(__name__)
    app.config["DEFAULT_OUTPUT_DIR"] = default_output_dir
    worker = downloader or ComicBookDownloader()

    @app.get("/")
    def index() -> Any:  # pragma: no cover - template rendering is trivial
        return render_template_string(
            INDEX_TEMPLATE,
            default_output_dir=app.config.get("DEFAULT_OUTPUT_DIR", ""),
        )

    @app.get("/health")
    def health() -> Any:  # pragma: no cover - trivial
        return jsonify({"status": "ok"})

    @app.get("/features")
    def feature_catalog() -> Any:
        catalog = get_feature_catalog()
        return jsonify(catalog.to_dict())

    @app.get("/config")
    def get_config() -> Any:
        return jsonify({"default_output_dir": app.config.get("DEFAULT_OUTPUT_DIR")})

    @app.post("/config/output-dir")
    def update_default_output_dir() -> Any:
        payload = request.get_json(silent=True) or {}
        output_dir = payload.get("output_dir")
        if not isinstance(output_dir, str) or not output_dir.strip():
            return jsonify({"error": "output_dir must be provided as a non-empty string"}), 400

        app.config["DEFAULT_OUTPUT_DIR"] = output_dir
        return jsonify({"default_output_dir": output_dir})

    def _build_pages(raw_pages: Any) -> Iterable[PageSpec]:
        if not isinstance(raw_pages, list) or not raw_pages:
            raise ValueError("pages must be a non-empty list")

        specs: list[PageSpec] = []
        for index, raw in enumerate(raw_pages):
            if not isinstance(raw, dict):
                raise ValueError(f"pages[{index}] must be an object")

            url = raw.get("url")
            if not isinstance(url, str) or not url:
                raise ValueError(f"pages[{index}].url must be a non-empty string")

            spec_kwargs: Dict[str, Any] = {"url": url}

            if "filename" in raw:
                filename = raw["filename"]
                if filename is not None and (not isinstance(filename, str) or not filename):
                    raise ValueError(
                        f"pages[{index}].filename must be a non-empty string when provided"
                    )
                spec_kwargs["filename"] = filename

            if "headers" in raw:
                headers = raw["headers"]
                if not isinstance(headers, dict):
                    raise ValueError(
                        f"pages[{index}].headers must be an object mapping strings to strings"
                    )
                converted: Dict[str, str] = {}
                for key, value in headers.items():
                    if not isinstance(key, str) or not isinstance(value, str):
                        raise ValueError(
                            f"pages[{index}].headers must only contain string keys and values"
                        )
                    converted[key] = value
                spec_kwargs["headers"] = converted

            specs.append(PageSpec(**spec_kwargs))

        return specs

    @app.post("/download")
    def download() -> Any:
        payload = request.get_json(silent=True) or {}

        title = payload.get("title")
        if not isinstance(title, str) or not title.strip():
            return jsonify({"error": "title must be a non-empty string"}), 400

        output_dir = payload.get("output_dir", app.config.get("DEFAULT_OUTPUT_DIR"))
        if not isinstance(output_dir, str) or not output_dir.strip():
            return jsonify({"error": "output_dir must be provided as a non-empty string"}), 400

        output_dir = output_dir.strip()

        source_url = payload.get("source_url")
        if source_url is not None:
            if not isinstance(source_url, str) or not source_url.strip():
                return jsonify({"error": "source_url must be a non-empty string"}), 400

            filename = payload.get("filename")
            if filename is not None:
                if not isinstance(filename, str) or not filename.strip():
                    return jsonify({"error": "filename must be a non-empty string when provided"}), 400
                filename_value = filename.strip()
            else:
                filename_value = None

            try:
                archive_path = worker.download_direct_archive(
                    source_url.strip(),
                    output_dir,
                    filename=filename_value,
                )
            except DownloadError as exc:
                return jsonify({"error": str(exc)}), 502

            return jsonify({"archive_path": str(archive_path)}), 201

        try:
            pages = list(_build_pages(payload.get("pages")))
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        try:
            archive_path = worker.download_cbz(title, pages, output_dir)
        except DownloadError as exc:
            return jsonify({"error": str(exc)}), 502

        return jsonify({"archive_path": str(archive_path)}), 201

    return app


def main() -> None:
    """Entry point for running the development server."""

    parser = argparse.ArgumentParser(description="Run the CBDownloader web server")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument(
        "--output-dir",
        default="./downloads",
        help="Default directory where generated CBZ archives are written",
    )
    args = parser.parse_args()

    app = create_app(default_output_dir=args.output_dir)
    app.run(host=args.host, port=args.port)


if __name__ == "__main__":  # pragma: no cover - manual invocation
    main()
