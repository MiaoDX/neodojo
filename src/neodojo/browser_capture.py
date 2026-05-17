from __future__ import annotations

import json
from dataclasses import dataclass
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from typing import Any
from urllib.parse import quote

from .contracts import PUBLIC_DEMO_SCHEMA, require_schema
from .motion_contract import _relative_path, _write_json, validate_output_dir
from .public_demo import smoke_check_public_demo

BROWSER_CAPTURE_SCHEMA = "neodojo.browser_capture.v1"


@dataclass(frozen=True)
class BrowserCaptureWriteResult:
    manifest_path: Path
    screenshot_path: Path
    public_demo_manifest_path: Path
    url: str


class _QuietStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        return


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _load_playwright() -> Any:
    try:
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError as exc:
        raise ValueError(
            "browser capture requires the optional Playwright dependency; install with "
            "`python -m pip install '.[browser]'` and install Chromium with "
            "`python -m playwright install chromium`"
        ) from exc
    return sync_playwright


def _serve_directory(directory: Path) -> tuple[ThreadingHTTPServer, Thread, str]:
    handler = partial(_QuietStaticHandler, directory=str(directory))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    return server, thread, f"http://{host}:{port}"


def write_public_demo_browser_capture(
    *,
    public_demo: Path,
    out_dir: Path,
    width: int = 1280,
    height: int = 720,
    timeout_ms: int = 10_000,
) -> BrowserCaptureWriteResult:
    if width < 320 or height < 240:
        raise ValueError("browser capture viewport must be at least 320x240")

    validate_output_dir(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    smoke = smoke_check_public_demo(public_demo)
    public_manifest_path = smoke.manifest_path
    public_manifest = _load_json(public_manifest_path)
    require_schema(public_manifest, PUBLIC_DEMO_SCHEMA, "public-demo manifest")
    required_labels = public_manifest.get("visual_smoke_expectations", {}).get("required_labels", [])
    if not isinstance(required_labels, list) or not all(isinstance(label, str) for label in required_labels):
        raise ValueError("public-demo manifest visual_smoke_expectations.required_labels must be strings")

    html_ref = public_manifest.get("html")
    if not isinstance(html_ref, str) or not html_ref:
        raise ValueError("public-demo manifest is missing html")

    screenshot_path = out_dir / "public-demo-browser.png"
    manifest_path = out_dir / "manifest.json"

    sync_playwright = _load_playwright()
    server, thread, base_url = _serve_directory(public_manifest_path.parent.resolve())
    url = f"{base_url}/{quote(html_ref)}"
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            try:
                page = browser.new_page(viewport={"width": width, "height": height})
                page.goto(url, wait_until="networkidle", timeout=timeout_ms)
                page.locator("body").wait_for(state="visible", timeout=timeout_ms)
                body_text = page.locator("body").inner_text(timeout=timeout_ms)
                missing = [label for label in required_labels if label not in body_text]
                if missing:
                    raise ValueError(f"browser-rendered public demo is missing labels: {', '.join(missing)}")
                image_state = page.evaluate(
                    """() => {
                        const img = document.querySelector('.stage img');
                        if (!img) return { ok: false, reason: 'missing stage image' };
                        const box = img.getBoundingClientRect();
                        return {
                            ok: img.complete && img.naturalWidth > 0 && img.naturalHeight > 0 && box.width > 0 && box.height > 0,
                            naturalWidth: img.naturalWidth,
                            naturalHeight: img.naturalHeight,
                            width: box.width,
                            height: box.height,
                        };
                    }"""
                )
                if not isinstance(image_state, dict) or not image_state.get("ok"):
                    raise ValueError(f"browser-rendered public demo screenshot image did not load: {image_state}")
                page.screenshot(path=str(screenshot_path), full_page=True)
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    screenshot_size = screenshot_path.stat().st_size if screenshot_path.exists() else 0
    if screenshot_size < 1024:
        raise ValueError(f"browser screenshot is unexpectedly small or blank: {screenshot_path}")

    manifest = {
        "schema": BROWSER_CAPTURE_SCHEMA,
        "capture_kind": "playwright_chromium_public_demo_screenshot",
        "real_browser_capture": True,
        "fixture_only": bool(public_manifest.get("fixture_only")),
        "public_demo": _relative_path(public_manifest_path, manifest_path.parent),
        "screenshot": _relative_path(screenshot_path, manifest_path.parent),
        "source_url": url,
        "viewport": {"width": width, "height": height},
        "checks": {
            "required_labels": required_labels,
            "browser_body_labels_present": True,
            "stage_image_loaded": True,
            "screenshot_size_bytes": screenshot_size,
        },
        "scoring_source": "smplx",
        "g1_scoring_allowed": False,
        "notes": (
            "Headless Chromium render of the generated public-demo HTML. This is "
            "browser capture evidence, not roboharness or simulator video recording."
        ),
    }
    _write_json(manifest_path, manifest)
    return BrowserCaptureWriteResult(
        manifest_path=manifest_path,
        screenshot_path=screenshot_path,
        public_demo_manifest_path=public_manifest_path,
        url=url,
    )
