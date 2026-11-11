"""Native receiver runs in a separate process and opens only Frameveil Camera."""
from pathlib import Path
import os
import subprocess
import tempfile

from PySide6.QtCore import QThread, Signal
from .driver import resources


class ReceiverCheck(QThread):
    done = Signal(bool, str)

    def __init__(self, device):
        super().__init__()
        self.device = device

    def run(self):
        if not self.device.startswith('Frameveil Camera'):
            self.done.emit(False, '当前为 DirectShow 输出。请在目标客户端选择「' + self.device +
                '」测试；Windows 原生后端可在这里执行跨进程接收自检。')
            return
        try:
            with tempfile.TemporaryDirectory(prefix='Frameveil-check-') as temp:
                frame = Path(temp) / 'received.nv12'
                result = subprocess.run([str(resources() / 'vendor/native/FrameveilCameraProbe.exe'), str(frame), '1280'],
                    capture_output=True, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW)
                detail = result.stdout.decode(errors='replace') + result.stderr.decode(errors='replace')
                if result.returncode or not frame.exists() or frame.stat().st_size != 1280 * 720 * 3 // 2:
                    raise RuntimeError('接收失败；这表明仅注册/发送尚不足以完成接收。\n' + detail)
                self.done.emit(True, '独立 Media Foundation 接收进程已成功读取 1280×720 画面。\n'
                    '这证明本机系统接收链路可用，仍需在钉钉/微信及远端确认。\n\n' + detail)
        except Exception as exc:
            self.done.emit(False, str(exc))


def native_device_list():
    try:
        result = subprocess.run([str(resources() / 'vendor/native/FrameveilCameraProbe.exe')],
            capture_output=True, timeout=5, creationflags=subprocess.CREATE_NO_WINDOW)
        return result.stdout.decode(errors='replace').strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return '无法读取原生设备列表：' + str(exc)
