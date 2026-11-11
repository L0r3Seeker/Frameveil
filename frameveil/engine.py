"""Media timeline and RGB composition, independent of the GUI."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import random

import cv2
import numpy as np
from PIL import Image, ImageOps

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".wmv", ".m4v", ".webm"}


@dataclass
class Settings:
    width: int = 1280
    height: int = 720
    fps: int = 30
    interval: float = 8.0
    transition: float = 0.6
    fit: str = "contain"
    mirror: bool = False
    loop: bool = True
    shuffle: bool = False
    speed: float = 1.0
    background: str = "#101117"
    backend: str = "auto"

    def dict(self):
        return asdict(self)


def read_image(path: str) -> np.ndarray:
    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im)
        im.thumbnail((4096, 4096))
        # Composite transparency instead of silently turning it black.
        rgba = im.convert("RGBA")
        base = Image.new("RGBA", rgba.size, "#101117")
        return np.array(Image.alpha_composite(base, rgba).convert("RGB"))


def compose(rgb: np.ndarray, settings: Settings) -> np.ndarray:
    w, h = settings.width, settings.height
    ih, iw = rgb.shape[:2]
    if settings.fit == "stretch":
        result = cv2.resize(rgb, (w, h), interpolation=cv2.INTER_AREA)
    else:
        ratio = (max if settings.fit == "cover" else min)(w / iw, h / ih)
        nw, nh = max(1, round(iw * ratio)), max(1, round(ih * ratio))
        sized = cv2.resize(rgb, (nw, nh), interpolation=cv2.INTER_AREA)
        if settings.fit == "cover":
            x, y = (nw - w) // 2, (nh - h) // 2
            result = sized[y:y + h, x:x + w].copy()
        else:
            color = tuple(int(settings.background.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
            result = np.full((h, w, 3), color, dtype=np.uint8)
            x, y = (w - nw) // 2, (h - nh) // 2
            result[y:y + nh, x:x + nw] = sized
    return np.ascontiguousarray(result[:, ::-1] if settings.mirror else result)


def probe(path: str) -> dict:
    ext = Path(path).suffix.lower()
    if ext in IMAGE_EXTS:
        with Image.open(path) as im:
            if getattr(im, "n_frames", 1) > 1:
                raise ValueError("暂不支持动画图片，请转换为 MP4")
        rgb = read_image(path)
        return {"path": str(Path(path).resolve()), "kind": "image", "width": rgb.shape[1],
                "height": rgb.shape[0], "duration": 0, "thumbnail": rgb}
    if ext not in VIDEO_EXTS:
        raise ValueError("不支持的格式；请使用 PNG / JPG / MP4 等静态图片或视频")
    cap = cv2.VideoCapture(path)
    try:
        ok, bgr = cap.read()
        fps = cap.get(cv2.CAP_PROP_FPS)
        count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        if not ok or fps <= 0 or count <= 0:
            raise ValueError("视频无法解码或没有有效时间轴，请转换为 H.264 MP4")
        return {"path": str(Path(path).resolve()), "kind": "video", "width": bgr.shape[1],
                "height": bgr.shape[0], "duration": count / fps,
                "thumbnail": cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)}
    finally:
        cap.release()


class Timeline:
    def __init__(self, settings=None):
        self.settings = settings or Settings()
        self.paths = []
        self.index = -1
        self.elapsed = 0.0
        self.duration = 0.0
        self.paused = False
        self.black = False
        self.finished = False
        self.cap = None
        self.image = None
        self.video_rgb = None
        self.video_index = -1
        self.source_fps = 30.0
        self.previous = None
        self.last = None
        self.fade_elapsed = 0.0
        self.scaled_image = None
        self.visited = set()

    def close(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def configure(self, settings):
        if settings.shuffle != self.settings.shuffle:
            self.visited = {self.index} if self.index >= 0 else set()
        self.settings = settings
        self.scaled_image = None
        self.previous = None

    def playlist(self, paths, index=0):
        self.paths = list(paths)
        self.select(index)

    def select(self, index, fade=True, reset_order=True):
        self.previous = self.last.copy() if fade and not self.paused and self.last is not None else None
        self.close()
        self.index = min(max(0, index), len(self.paths) - 1) if self.paths else -1
        if reset_order:
            self.visited = {self.index} if self.index >= 0 else set()
        self.elapsed = self.fade_elapsed = 0.0
        self.finished = False
        self.image = self.video_rgb = self.scaled_image = None
        self.video_index = -1
        if self.index < 0:
            self.duration = 0
            return
        path = self.paths[self.index]
        if Path(path).suffix.lower() in IMAGE_EXTS:
            self.image = read_image(path)
            self.duration = self.settings.interval
        else:
            self.cap = cv2.VideoCapture(path)
            self.source_fps = self.cap.get(cv2.CAP_PROP_FPS)
            count = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
            if not self.cap.isOpened() or self.source_fps <= 0 or count <= 0:
                self.close()
                raise ValueError(f"无法解码视频：{Path(path).name}")
            self.duration = count / self.source_fps

    def next(self, step=1, automatic=False):
        if not self.paths:
            return
        target = self.index + step
        if automatic and self.settings.shuffle:
            remaining = [i for i in range(len(self.paths)) if i not in self.visited]
            if not remaining:
                if not self.settings.loop:
                    self.finished = True
                    self.elapsed = self.duration
                    return
                self.visited = {self.index}
                remaining = [i for i in range(len(self.paths)) if i != self.index] or [self.index]
            target = random.choice(remaining)
        elif automatic and target >= len(self.paths) and not self.settings.loop:
            self.finished = True
            self.elapsed = self.duration
            return
        self.select(target % len(self.paths), reset_order=not automatic)
        self.visited.add(self.index)

    def seek(self, fraction):
        self.elapsed = min(1, max(0, fraction)) * self.duration
        self.finished = False
        self.previous = None

    def frame(self, dt):
        s = self.settings
        if self.image is not None:
            self.duration = s.interval
        if not self.paused and not self.finished and self.index >= 0:
            self.elapsed += max(0, dt) * (s.speed if self.cap is not None else 1)
            self.fade_elapsed += max(0, dt)
            if self.elapsed >= self.duration:
                self.next(automatic=True)
        if self.image is not None:
            if self.scaled_image is None:
                self.scaled_image = compose(self.image, s)
            out = self.scaled_image.copy()
        elif self.cap is not None:
            target = min(int(self.elapsed * self.source_fps), max(0, int(self.duration * self.source_fps) - 1))
            if target < self.video_index or target - self.video_index > 5:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, target)
                self.video_index = target - 1
            while self.video_index < target:
                ok, bgr = self.cap.read()
                if not ok:
                    if self.video_rgb is None:
                        raise ValueError("视频解码失败，请尝试 H.264 MP4")
                    break
                self.video_rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
                self.video_index += 1
            out = compose(self.video_rgb, s) if self.video_rgb is not None else np.zeros((s.height, s.width, 3), np.uint8)
        else:
            out = np.zeros((s.height, s.width, 3), np.uint8)
        if self.previous is not None and self.previous.shape == out.shape and s.transition > 0:
            alpha = min(1, self.fade_elapsed / s.transition)
            out = cv2.addWeighted(self.previous, 1 - alpha, out, alpha, 0)
            if alpha >= 1:
                self.previous = None
        self.last = out
        return np.zeros_like(out) if self.black else out
