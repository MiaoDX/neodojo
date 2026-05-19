from __future__ import annotations

import base64
import io
import json
import subprocess
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


def _gif_frame_duration_ms(*, total_frames: int, fps: float, sample_count: int, requested_ms: int | None) -> int:
    if requested_ms is not None and requested_ms > 0:
        if requested_ms < 20:
            raise ValueError("GIF frame duration must be at least 20ms")
        return requested_ms
    if fps <= 0:
        raise ValueError("public-demo scene fps must be positive")
    return max(20, round((total_frames / fps) * 1000 / sample_count))


def _resize_frame(image: Any, *, image_module: Any, scale_width: int | None) -> Any:
    if scale_width is None or scale_width <= 0 or image.width == scale_width:
        return image
    height = round(image.height * scale_width / image.width)
    resampling = getattr(getattr(image_module, "Resampling", None), "LANCZOS", None)
    if resampling is None:
        resampling = 1
    return image.resize((scale_width, height), resampling)


def _reference_video_path(scene: dict[str, Any], public_demo_dir: Path) -> Path | None:
    reference_video = scene.get("reference_video")
    if not isinstance(reference_video, dict) or reference_video.get("available") is not True:
        return None
    reference = reference_video.get("path")
    if not isinstance(reference, str) or not reference:
        return None
    path = Path(reference)
    if not path.is_absolute():
        path = public_demo_dir / path
    if not path.exists() or not path.is_file():
        return None
    return path


def _reference_video_offset_seconds(scene: dict[str, Any]) -> float:
    reference_video = scene.get("reference_video")
    if not isinstance(reference_video, dict):
        return 0.0
    try:
        return float(reference_video.get("playback_offset_seconds") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _decode_reference_video_png_data_uri(video_path: Path, seconds: float) -> str:
    command = [
        "ffmpeg",
        "-v",
        "error",
        "-ss",
        f"{max(0.0, seconds):.3f}",
        "-i",
        str(video_path),
        "-frames:v",
        "1",
        "-f",
        "image2pipe",
        "-vcodec",
        "png",
        "-",
    ]
    try:
        result = subprocess.run(command, check=False, capture_output=True)
    except FileNotFoundError as exc:
        raise ValueError("GIF rendering with a reference-video panel requires ffmpeg on PATH") from exc
    if result.returncode != 0 or not result.stdout:
        error = result.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(f"failed to decode reference video frame at {seconds:.3f}s: {error}")
    encoded = base64.b64encode(result.stdout).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _seek_public_demo_frame(
    page: Any,
    frame_index: int,
    *,
    seconds: float,
    source_frame_data_uri: str | None = None,
) -> None:
    page.evaluate(
        """async ({frameIndex, seconds, sourceFrameDataUri}) => {
            const playButton = document.getElementById("playButton");
            if (playButton && playButton.textContent.trim() === "Pause") {
                playButton.click();
            }
            const timeline = document.getElementById("timeline");
            if (!timeline) throw new Error("public demo timeline is missing");
            timeline.value = String(frameIndex);
            timeline.dispatchEvent(new Event("input", {bubbles: true}));
            await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
            if (sourceFrameDataUri) {
                const video = document.getElementById("referenceVideo");
                if (!video) return;
                let still = document.getElementById("referenceVideoStill");
                if (!still) {
                    still = document.createElement("img");
                    still.id = "referenceVideoStill";
                    still.className = video.className;
                    still.alt = video.getAttribute("aria-label") || "Original source video";
                    video.insertAdjacentElement("afterend", still);
                }
                video.style.display = "none";
                await new Promise((resolve) => {
                    still.onload = () => requestAnimationFrame(() => requestAnimationFrame(resolve));
                    still.src = sourceFrameDataUri;
                });
                return;
            }
            const video = document.getElementById("referenceVideo");
            if (!video) return;
            video.pause();
            if (video.readyState < 1) {
                await new Promise((resolve) => {
                    video.addEventListener("loadedmetadata", resolve, {once: true});
                });
            }
            const target = Math.max(0, Math.min(seconds, Math.max(0, video.duration - 0.04)));
            await new Promise((resolve) => {
                let settled = false;
                const done = () => {
                    if (settled) return;
                    settled = true;
                    clearTimeout(timer);
                    video.removeEventListener("seeked", done);
                    requestAnimationFrame(() => requestAnimationFrame(resolve));
                };
                const timer = setTimeout(done, 1200);
                if (Math.abs(video.currentTime - target) > 0.015) {
                    video.addEventListener("seeked", done, {once: true});
                    video.currentTime = target;
                } else {
                    done();
                }
            });
            const sourcePanel = document.querySelector('[data-panel="source"]');
            if (!sourcePanel || !video.videoWidth || !video.videoHeight) return;
            const scratch = document.createElement("canvas");
            scratch.width = video.videoWidth;
            scratch.height = video.videoHeight;
            const ctx = scratch.getContext("2d");
            ctx.drawImage(video, 0, 0, scratch.width, scratch.height);
            let still = document.getElementById("referenceVideoStill");
            if (!still) {
                still = document.createElement("img");
                still.id = "referenceVideoStill";
                still.className = video.className;
                still.alt = video.getAttribute("aria-label") || "Original source video";
                video.insertAdjacentElement("afterend", still);
                video.style.display = "none";
            }
            await new Promise((resolve) => {
                still.onload = () => requestAnimationFrame(() => requestAnimationFrame(resolve));
                still.src = scratch.toDataURL("image/png");
            });
        }""",
        {"frameIndex": frame_index, "seconds": seconds, "sourceFrameDataUri": source_frame_data_uri},
    )


def write_public_demo_gif(
    *,
    public_demo: Path,
    out: Path,
    width: int = 1280,
    height: int = 720,
    frames: int = 24,
    duration_ms: int | None = None,
    scale_width: int | None = 960,
    timeout_ms: int = 10_000,
) -> PublicDemoGifWriteResult:
    if width < 320 or height < 240:
        raise ValueError("GIF browser viewport must be at least 320x240")
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
    try:
        fps = float(timing.get("fps") or scene.get("track_metadata", {}).get("smplx", {}).get("fps") or 25.0)
    except (TypeError, ValueError):
        fps = 25.0
    gif_duration_ms = _gif_frame_duration_ms(
        total_frames=total_frames,
        fps=fps,
        sample_count=len(frame_indices),
        requested_ms=duration_ms,
    )

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
                reference_video_path = _reference_video_path(scene, public_manifest_path.parent)
                reference_offset_seconds = _reference_video_offset_seconds(scene)
                for frame_index in frame_indices:
                    seconds = reference_offset_seconds + frame_index / fps
                    source_frame_data_uri = None
                    if reference_video_path is not None:
                        source_frame_data_uri = _decode_reference_video_png_data_uri(
                            reference_video_path,
                            seconds,
                        )
                    _seek_public_demo_frame(
                        page,
                        frame_index,
                        seconds=seconds,
                        source_frame_data_uri=source_frame_data_uri,
                    )
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
        duration=gif_duration_ms,
        loop=0,
        optimize=True,
    )
    return PublicDemoGifWriteResult(
        gif_path=out,
        frame_count=len(captured_frames),
        source_public_demo=public_manifest_path,
    )
