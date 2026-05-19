from __future__ import annotations

import io
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote

from .browser_capture import _load_playwright, _serve_directory
from .contracts import require_schema
from .public_demo import SCENE_TIMELINE_SCHEMA, smoke_check_public_demo


@dataclass(frozen=True)
class PublicDemoGifWriteResult:
    gif_path: Path
    frame_count: int
    source_public_demo: Path


def _load_pillow() -> Any:
    try:
        from PIL import Image
    except ModuleNotFoundError as exc:
        raise ValueError(
            "GIF rendering requires Pillow; install the browser extra with "
            "`python -m pip install '.[browser]'`"
        ) from exc
    return Image


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _sample_frame_indices(total_frames: int, sample_count: int) -> list[int]:
    if total_frames < 1:
        raise ValueError("public-demo scene must contain at least one frame")
    if sample_count < 1:
        raise ValueError("GIF frame count must be at least 1")
    if sample_count >= total_frames:
        return list(range(total_frames))
    if sample_count == 1:
        return [0]
    return [
        round(index * (total_frames - 1) / (sample_count - 1))
        for index in range(sample_count)
    ]


def _resize_frame(image: Any, *, image_module: Any, scale_width: int | None) -> Any:
    if scale_width is None or scale_width <= 0 or image.width == scale_width:
        return image
    height = round(image.height * scale_width / image.width)
    resampling = getattr(getattr(image_module, "Resampling", None), "LANCZOS", None)
    if resampling is None:
        resampling = 1
    return image.resize((scale_width, height), resampling)


def _seek_public_demo_frame(page: Any, frame_index: int) -> None:
    page.evaluate(
        """async (frameIndex) => {
            const playButton = document.getElementById("playButton");
            if (playButton && playButton.textContent.trim() === "Pause") {
                playButton.click();
            }
            const timeline = document.getElementById("timeline");
            if (!timeline) throw new Error("public demo timeline is missing");
            timeline.value = String(frameIndex);
            timeline.dispatchEvent(new Event("input", {bubbles: true}));
            await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
            const video = document.getElementById("referenceVideo");
            if (!video) return;
            await new Promise((resolve) => {
                let settled = false;
                const done = () => {
                    if (settled) return;
                    settled = true;
                    clearTimeout(timer);
                    video.removeEventListener("seeked", done);
                    requestAnimationFrame(() => requestAnimationFrame(resolve));
                };
                const timer = setTimeout(done, 700);
                if (video.seeking) {
                    video.addEventListener("seeked", done, {once: true});
                } else {
                    done();
                }
            });
        }""",
        frame_index,
    )


def write_public_demo_gif(
    *,
    public_demo: Path,
    out: Path,
    width: int = 1280,
    height: int = 720,
    frames: int = 24,
    duration_ms: int = 120,
    scale_width: int | None = 960,
    timeout_ms: int = 10_000,
) -> PublicDemoGifWriteResult:
    if width < 320 or height < 240:
        raise ValueError("GIF browser viewport must be at least 320x240")
    if duration_ms < 20:
        raise ValueError("GIF frame duration must be at least 20ms")

    smoke = smoke_check_public_demo(public_demo)
    public_manifest_path = smoke.manifest_path
    public_manifest = _load_json(public_manifest_path)
    html_ref = public_manifest.get("html")
    scene_ref = public_manifest.get("scene")
    if not isinstance(html_ref, str) or not html_ref:
        raise ValueError("public-demo manifest is missing html")
    if not isinstance(scene_ref, str) or not scene_ref:
        raise ValueError("public-demo manifest is missing scene")

    scene_path = public_manifest_path.parent / scene_ref
    scene = _load_json(scene_path)
    require_schema(scene, SCENE_TIMELINE_SCHEMA, "scene/timeline manifest")
    timing = scene.get("timing") if isinstance(scene.get("timing"), dict) else {}
    total_frames = int(timing.get("frame_count") or len(scene["tracks"]["smplx"]["frames"]))
    frame_indices = _sample_frame_indices(total_frames, frames)

    Image = _load_pillow()
    sync_playwright = _load_playwright()
    server, _thread, base_url = _serve_directory(public_manifest_path.parent.resolve())
    url = f"{base_url}/{quote(html_ref)}"
    captured_frames = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            try:
                page = browser.new_page(viewport={"width": width, "height": height})
                page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                page.locator("body").wait_for(state="visible", timeout=timeout_ms)
                page.wait_for_function(
                    "() => document.querySelectorAll('canvas').length >= 2",
                    timeout=timeout_ms,
                )
                page.wait_for_function(
                    """() => {
                        const video = document.getElementById("referenceVideo");
                        return !video || video.readyState >= 1;
                    }""",
                    timeout=timeout_ms,
                )
                for frame_index in frame_indices:
                    _seek_public_demo_frame(page, frame_index)
                    png = page.screenshot(full_page=False)
                    image = Image.open(io.BytesIO(png)).convert("RGB")
                    captured_frames.append(_resize_frame(image, image_module=Image, scale_width=scale_width))
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()

    if not captured_frames:
        raise ValueError("GIF rendering did not capture any frames")
    out.parent.mkdir(parents=True, exist_ok=True)
    captured_frames[0].save(
        out,
        save_all=True,
        append_images=captured_frames[1:],
        duration=duration_ms,
        loop=0,
        optimize=True,
    )
    return PublicDemoGifWriteResult(
        gif_path=out,
        frame_count=len(captured_frames),
        source_public_demo=public_manifest_path,
    )
