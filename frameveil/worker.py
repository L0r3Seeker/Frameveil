"""One owner thread for decoders and virtual-camera resources."""
import logging
import queue
import threading
import time

import cv2
import numpy as np
from PySide6.QtCore import QThread, Signal
from .engine import Timeline, Settings


class MediaWorker(QThread):
    output_changed = Signal(bool, str)
    error = Signal(str)

    def __init__(self):
        super().__init__()
        self.commands = queue.Queue()
        self.lock = threading.Lock()
        self.latest = None
        self.serial = 0
        self.running = True

    def post(self, action, value=None):
        self.commands.put((action, value))

    def snapshot(self):
        with self.lock:
            return self.latest

    def run(self):
        timeline = Timeline()
        camera = None
        last_t = time.perf_counter()
        next_t = last_t
        fps_start, frames, measured = last_t, 0, 0.0
        sent = 0
        pending = None
        try:
            while self.running:
                while not self.commands.empty():
                    action, value = self.commands.get_nowait()
                    try:
                        if action == "quit":
                            self.running = False
                        elif action == "settings":
                            timeline.configure(Settings(**value))
                        elif action == "playlist":
                            timeline.playlist(*value)
                        elif action == "select":
                            timeline.select(value)
                        elif action == "next":
                            timeline.next(value)
                        elif action == "pause":
                            timeline.paused = value
                        elif action == "black":
                            timeline.black = value
                        elif action == "seek":
                            timeline.seek(value)
                        elif action == "output":
                            pending = bool(value)
                    except Exception as exc:
                        logging.exception("Media command failed")
                        timeline.close()
                        timeline.image = None
                        timeline.index = -1
                        self.error.emit(str(exc))
                if not self.running:
                    break
                if pending is not None:
                    if camera is not None:
                        # Send a black frame before releasing. Consumer behavior after close is device-specific.
                        try:
                            camera.send(np.zeros((camera.height, camera.width, 3), np.uint8))
                        finally:
                            camera.close()
                            camera = None
                    if pending:
                        try:
                            if timeline.index < 0:
                                raise RuntimeError("请先导入并选择一个可用素材")
                            from .outputs import open_camera
                            s = timeline.settings
                            camera = open_camera(s)
                            sent = 0
                            self.output_changed.emit(True, camera.device)
                        except Exception as exc:
                            logging.exception("Virtual camera failed")
                            self.output_changed.emit(False, "")
                            self.error.emit("无法启动虚拟摄像头。请安装组件，或退出占用设备的 OBS 等程序后重试。\n\n" + str(exc))
                    else:
                        self.output_changed.emit(False, "")
                    pending = None
                now = time.perf_counter()
                dt = min(now - last_t, 0.25)
                last_t = now
                try:
                    rgb = timeline.frame(dt)
                    if camera is not None:
                        camera.send(rgb)
                        sent += 1
                except Exception as exc:
                    logging.exception("Frame failed")
                    if camera is not None:
                        camera.close()
                        camera = None
                        self.output_changed.emit(False, "")
                    timeline.close()
                    timeline.image = None
                    timeline.index = -1
                    rgb = np.zeros((timeline.settings.height, timeline.settings.width, 3), np.uint8)
                    self.error.emit(str(exc))
                frames += 1
                if now - fps_start >= 1:
                    measured = frames / (now - fps_start)
                    fps_start, frames = now, 0
                # Bounded latest-frame mailbox: preview cannot accumulate queued frames.
                if rgb.shape[1] > 960:
                    rgb = cv2.resize(rgb, (960, round(rgb.shape[0] * 960 / rgb.shape[1])))
                with self.lock:
                    self.serial += 1
                    self.latest = (self.serial, rgb, timeline.index, timeline.elapsed,
                                   timeline.duration, measured, sent, timeline.finished)
                next_t += 1 / timeline.settings.fps
                if next_t < time.perf_counter() - 0.15:
                    next_t = time.perf_counter()
                self.msleep(max(1, int((next_t - time.perf_counter()) * 1000)))
        finally:
            if camera is not None:
                try:
                    camera.send(np.zeros((camera.height, camera.width, 3), np.uint8))
                finally:
                    camera.close()
            timeline.close()
