"""Windows-only camera adapter. The media timeline is platform-independent."""
from __future__ import annotations
import ctypes
import logging
import mmap
import msvcrt
import os
from pathlib import Path
import struct
import subprocess
import sys
import threading
import queue
import winreg

import cv2
from .driver import resources

NATIVE_CLSID = "{184FBC72-6B4D-41FB-9421-5976DAB0C222}"
MAGIC = 0x32564D46
CAPACITY = 1920 * 1080 * 4
HEADER_SIZE = 64


def supported():
    return sys.platform == "win32" and sys.getwindowsversion().build >= 22000


def registered():
    if not supported():
        return False
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, rf"SOFTWARE\Classes\CLSID\{NATIVE_CLSID}\InprocServer32", 0,
                            winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
            return Path(winreg.QueryValueEx(key, "")[0]).is_file()
    except OSError:
        return False


def transport_path():
    return Path(os.environ.get("ProgramData", r"C:\ProgramData")) / "Frameveil" / "Transport" / "current.frame"


class FrameTransport:
    def __init__(self, path=None):
        self.path = Path(path) if path is not None else transport_path()
        self.file = self.path.open("r+b")
        if self.path.stat().st_size != HEADER_SIZE + CAPACITY:
            self.file.close()
            raise RuntimeError("原生摄像头传输文件无效，请修复组件")
        try:
            self.file.seek(63)
            msvcrt.locking(self.file.fileno(), msvcrt.LK_NBLCK, 1)
            self.mapping = mmap.mmap(self.file.fileno(), HEADER_SIZE + CAPACITY, access=mmap.ACCESS_WRITE)
        except Exception:
            self.file.close()
            raise RuntimeError("原生传输缓冲不可写或已被另一个发送实例占用")
        self.sequence = 0
        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self.kernel.GetTickCount64.restype = ctypes.c_uint64

    def write(self, rgb):
        h, w = rgb.shape[:2]
        if w > 1920 or h > 1080 or rgb.shape[2] != 3:
            raise ValueError("原生输出支持最高 1920×1080 RGB 画面")
        bgra = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGRA)
        self.sequence = (self.sequence + 2) & 0xFFFFFFFE
        struct.pack_into("<I", self.mapping, 32, self.sequence | 1)
        struct.pack_into("<6IQ", self.mapping, 0, MAGIC, 1, w, h, w * 4, bgra.nbytes, self.kernel.GetTickCount64())
        self.mapping[HEADER_SIZE:HEADER_SIZE + bgra.nbytes] = bgra.tobytes()
        struct.pack_into("<I", self.mapping, 32, self.sequence)

    def close(self):
        if getattr(self, "mapping", None) is not None:
            struct.pack_into("<Q", self.mapping, 24, 0)  # immediately invalidate retained content
            self.mapping[HEADER_SIZE:] = b"\0" * CAPACITY
            self.mapping.close()
            self.mapping = None
            self.file.close()


class NativeCamera:
    device = "Frameveil Camera (Windows Virtual Camera)"
    backend = "native"

    def __init__(self, width, height, fps):
        if not supported():
            raise RuntimeError("Windows 原生摄像头需要 Windows 11 build 22000 或更新；Windows 10 请使用 DirectShow")
        if not registered():
            raise RuntimeError("尚未安装 Windows 原生摄像头组件，请点击「摄像头组件管理」安装")
        if fps != 30:
            raise RuntimeError("原生兼容模式使用 30 FPS，请选择 30 FPS 后重试")
        self.width, self.height, self.fps = width, height, fps
        self.process = None
        self.transport = None
        try:
            self.transport = FrameTransport()
            self.process = subprocess.Popen([str(resources() / "vendor/native/FrameveilCameraHost.exe")],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW)
            ready = queue.Queue()
            process = self.process
            def read_ready():
                try:
                    ready.put(process.stdout.readline().decode("utf-8", errors="replace").strip())
                except (OSError, ValueError):
                    ready.put("")
            threading.Thread(target=read_ready, daemon=True).start()
            try:
                line = ready.get(timeout=12)
            except queue.Empty:
                raise RuntimeError("Windows 摄像头服务启动超时，请查看系统摄像头权限或诊断报告")
            if not line.startswith("READY"):
                raise RuntimeError("Windows 原生摄像头启动失败：" + (line or "服务未返回就绪状态"))
            logging.info("Native camera ready: %s %sx%s@%s", line, width, height, fps)
        except Exception:
            self.close()
            raise

    def send(self, rgb):
        if self.process.poll() is not None:
            raise RuntimeError("Windows 原生摄像头宿主已退出，请重新开启输出")
        self.transport.write(rgb)

    def close(self):
        if self.transport is not None:
            self.transport.close()
            self.transport = None
        if self.process is not None:
            try:
                try:
                    self.process.stdin.write(b"\n")
                    self.process.stdin.flush()
                    self.process.stdin.close()
                except (OSError, ValueError):
                    pass
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.terminate()
                self.process.wait(timeout=3)
            self.process.stdout.close()
            self.process = None
