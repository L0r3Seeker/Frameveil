from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import time

import numpy as np
from PySide6.QtCore import Qt, QTimer, QSize, QUrl, QThread, Signal
from PySide6.QtGui import QIcon, QImage, QPixmap, QColor, QPainter, QPainterPath, QDesktopServices, QShortcut, QKeySequence
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QListWidget, QListWidgetItem, QComboBox, QDoubleSpinBox,
    QCheckBox, QSlider, QFileDialog, QMessageBox, QDialog, QTextBrowser, QScrollArea,
    QAbstractItemView, QSizePolicy, QColorDialog)

from . import __version__
from .engine import Settings, probe
from .worker import MediaWorker
from .driver import resources, registered_cameras, elevate_helper, install_directory
from .style import STYLE


def data_directory():
    folder = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Frameveil"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def label(text, name=None):
    out = QLabel(text)
    if name:
        out.setObjectName(name)
    return out


def button(text, callback, name=None):
    out = QPushButton(text)
    if name:
        out.setObjectName(name)
    out.setCursor(Qt.CursorShape.PointingHandCursor)
    out.clicked.connect(callback)
    return out


def panel():
    p = QFrame()
    p.setObjectName("panel")
    layout = QVBoxLayout(p)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(13)
    return p, layout


def rgb_pixmap(rgb):
    rgb = np.ascontiguousarray(rgb)
    h, w = rgb.shape[:2]
    return QPixmap.fromImage(QImage(rgb.data, w, h, rgb.strides[0], QImage.Format.Format_RGB888).copy())


def stamp(seconds):
    seconds = max(0, int(seconds))
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


class Preview(QWidget):
    def __init__(self):
        super().__init__()
        self.pixmap = None
        self.setMinimumSize(390, 230)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#0b0c11"))
        if self.pixmap:
            size = self.pixmap.size().scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio)
            x, y = (self.width() - size.width()) // 2, (self.height() - size.height()) // 2
            clip = QPainterPath()
            clip.addRoundedRect(self.rect().toRectF(), 12, 12)
            painter.setClipPath(clip)
            painter.drawPixmap(x, y, self.pixmap.scaled(size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            painter.setPen(QColor("#8e94a8"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "将图片或视频拖入窗口\n在这里预览你的画面")
        painter.end()


class Installer(QThread):
    done = Signal(bool, str)

    def __init__(self, uninstall=False, backend="unitycapture"):
        super().__init__()
        self.uninstall = uninstall
        self.backend = backend

    def run(self):
        try:
            elevate_helper(self.uninstall, self.backend)
            self.done.emit(True, "已卸载摄像头组件" if self.uninstall else "摄像头组件已就绪，请重新打开会议软件以刷新设备列表")
        except Exception as exc:
            logging.exception("Component helper failed")
            self.done.emit(False, str(exc))


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"帧幕 Frameveil  ·  {__version__}")
        self.setWindowIcon(QIcon(str(resources() / "assets" / "frameveil.ico")))
        screen = QApplication.primaryScreen()
        available = screen.availableGeometry() if screen else None
        self.compact = bool(available and (available.width() < 1350 or available.height() < 850))
        self.resize(min(1440, available.width() - 40) if available else 1440,
                    min(900, available.height() - 60) if available else 900)
        self.setMinimumSize(900, 520)
        self.setAcceptDrops(True)
        self.settings = Settings()
        self.entries = []
        self.output_active = False
        self.output_pending = False
        self.paused = False
        self.black = False
        self.current_index = -1
        self.last_serial = 0
        self.started_at = None
        self.installer = None
        self.receiver_check = None
        self.output_device = ''
        self.loading = True
        self.restored = self.load_state()
        self.build_ui()
        self.load_controls()
        self.worker = MediaWorker()
        self.worker.output_changed.connect(self.output_changed)
        self.worker.error.connect(self.show_error)
        self.worker.start()
        self.loading = False
        self.apply_settings()
        self.restore_media()
        self.refresh_device()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_preview)
        self.timer.start(66)
        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.timeout.connect(self.save_state)
        QShortcut(QKeySequence("Ctrl+O"), self, self.import_media)
        QShortcut(QKeySequence("Ctrl+Shift+B"), self, self.toggle_black)
        QShortcut(QKeySequence("Ctrl+Shift+S"), self, self.toggle_output)

    def build_ui(self):
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(16, 12, 16, 12) if self.compact else layout.setContentsMargins(28, 18, 28, 16)
        layout.setSpacing(20)

        header = QFrame()
        header.setObjectName("header")
        row = QHBoxLayout(header)
        row.setContentsMargins(0, 0, 0, 18)
        logo = QLabel()
        logo.setPixmap(QIcon(str(resources() / "assets" / "logo.svg")).pixmap(46, 46))
        row.addWidget(logo)
        brand = QVBoxLayout()
        brand.setSpacing(1)
        brand.addWidget(label("帧幕  FRAMEVEIL", "brand"))
        brand.addWidget(label("让每一帧，由你掌控。", "muted"))
        row.addLayout(brand)
        row.addSpacing(15)
        row.addWidget(label("STUDIO  /  0.2", "badge"))
        row.addStretch()
        self.top_status = label("●  仅本地预览", "status")
        row.addWidget(self.top_status)
        row.addSpacing(8)
        row.addWidget(button("使用指南", self.show_guide, "quiet"))
        layout.addWidget(header)

        columns = QHBoxLayout()
        columns.setSpacing(18)
        left, ll = panel()
        left.setFixedWidth(210 if self.compact else 254)
        ll.addWidget(label("MEDIA LIBRARY", "section"))
        count_row = QHBoxLayout()
        count_row.addWidget(label("素材库", "title"))
        count_row.addStretch()
        self.count_label = label("00", "muted")
        count_row.addWidget(self.count_label)
        ll.addLayout(count_row)
        ll.addWidget(button("＋  导入图片 / 视频", self.import_media))
        ll.addWidget(label("也可以直接拖入文件 · Ctrl+O", "muted"))
        self.list = QListWidget()
        self.list.setIconSize(QSize(72, 46))
        self.list.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list.currentRowChanged.connect(self.select_media)
        ll.addWidget(self.list, 1)
        reorder = QHBoxLayout()
        reorder.setSpacing(6)
        reorder.addWidget(button("↑", lambda: self.reorder(-1), "quiet"))
        reorder.addWidget(button("↓", lambda: self.reorder(1), "quiet"))
        reorder.addWidget(button("移除", self.remove_media, "quiet"))
        ll.addLayout(reorder)
        ll.addWidget(button("载入演示素材", self.load_demo, "quiet"))
        hint = label("素材在本机处理\n视频仅输出画面，不输出声音", "muted")
        hint.setWordWrap(True)
        ll.addWidget(hint)
        columns.addWidget(left)

        middle_container = QWidget()
        middle = QVBoxLayout(middle_container)
        middle.setContentsMargins(0, 0, 0, 0)
        middle.setSpacing(16)
        monitor, ml = panel()
        title_row = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(7)
        titles.addWidget(label("YOUR CANVAS", "section"))
        titles.addWidget(label("画面工作台", "title"))
        title_row.addLayout(titles)
        title_row.addStretch()
        self.preview_badge = label("●  PREVIEW", "badge")
        title_row.addWidget(self.preview_badge)
        ml.addLayout(title_row)
        self.preview = Preview()
        if self.compact:
            self.preview.setMinimumSize(240, 120)
        ml.addWidget(self.preview, 1)
        detail = QHBoxLayout()
        self.media_title = label("等待导入素材")
        detail.addWidget(self.media_title, 1)
        self.format_label = label("1280 × 720  /  30 FPS", "muted")
        detail.addWidget(self.format_label)
        ml.addLayout(detail)
        progress_row = QHBoxLayout()
        self.elapsed_label = label("00:00", "muted")
        self.duration_label = label("00:08", "muted")
        self.seek = QSlider(Qt.Orientation.Horizontal)
        self.seek.setRange(0, 1000)
        self.seek.sliderReleased.connect(lambda: self.worker.post("seek", self.seek.value() / 1000))
        progress_row.addWidget(self.elapsed_label)
        progress_row.addWidget(self.seek, 1)
        progress_row.addWidget(self.duration_label)
        ml.addLayout(progress_row)
        transport = QHBoxLayout()
        transport.setSpacing(8)
        transport.addWidget(button("上一项", lambda: self.worker.post("next", -1), "quiet"))
        self.pause_button = button("Ⅱ  暂停", self.toggle_pause)
        transport.addWidget(self.pause_button)
        transport.addWidget(button("下一项", lambda: self.worker.post("next", 1), "quiet"))
        transport.addStretch()
        self.position_label = label("— / —", "muted")
        transport.addWidget(self.position_label)
        ml.addLayout(transport)
        middle.addWidget(monitor, 1)

        output, ol = panel()
        output_row = QHBoxLayout()
        output_titles = QVBoxLayout()
        output_titles.setSpacing(6)
        output_titles.addWidget(label("VIRTUAL CAMERA", "section"))
        self.output_title = label("准备好，就开始输出", "title")
        output_titles.addWidget(self.output_title)
        output_row.addLayout(output_titles)
        output_row.addStretch()
        self.output_time = label("00:00:00", "muted")
        output_row.addWidget(self.output_time)
        ol.addLayout(output_row)
        self.output_hint = label("开启后，在会议软件中选择对应的虚拟摄像头。", "muted")
        self.output_hint.setWordWrap(True)
        ol.addWidget(self.output_hint)
        actions = QHBoxLayout()
        self.output_button = button("◉  开启虚拟摄像头", self.toggle_output, "primary")
        self.output_button.setMinimumWidth(210)
        actions.addWidget(self.output_button, 1)
        self.black_button = button("黑屏待机", self.toggle_black, "quiet")
        self.black_button.setCheckable(True)
        self.black_button.setToolTip("持续发送黑色画面。快捷键 Ctrl+Shift+B（应用内）")
        actions.addWidget(self.black_button)
        ol.addLayout(actions)
        middle.addWidget(output)
        center_scroll = QScrollArea()
        center_scroll.setWidgetResizable(True)
        center_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        center_scroll.setWidget(middle_container)
        columns.addWidget(center_scroll, 1)

        right, rl = panel()
        right.setFixedWidth(240 if self.compact else 282)
        rl.addWidget(label("FINE TUNE", "section"))
        rl.addWidget(label("播放与输出", "title"))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        controls = QWidget()
        form = QVBoxLayout(controls)
        form.setContentsMargins(0, 0, 6, 0)
        form.setSpacing(10)
        form.addWidget(label("输出格式", "muted"))
        self.resolution = QComboBox()
        self.resolution.addItems(["1280 × 720 · HD", "1920 × 1080 · FHD", "640 × 480 · 4:3"])
        form.addWidget(self.resolution)
        self.fps = QComboBox()
        self.fps.addItems(["30 FPS", "24 FPS", "15 FPS", "60 FPS", "25 FPS"])
        form.addWidget(self.fps)
        form.addSpacing(5)
        form.addWidget(label("画面适配", "muted"))
        self.fit = QComboBox()
        self.fit.addItems(["完整显示 · 保留比例", "铺满画面 · 居中裁剪", "拉伸至画布"])
        form.addWidget(self.fit)
        self.mirror = QCheckBox("水平镜像（同时作用于输出）")
        form.addWidget(self.mirror)
        self.color_button = button("留边颜色  " + self.settings.background, self.choose_color, "quiet")
        form.addWidget(self.color_button)
        form.addSpacing(5)
        form.addWidget(label("图片轮播", "muted"))
        self.interval = QDoubleSpinBox()
        self.interval.setRange(0.5, 3600)
        self.interval.setDecimals(1)
        self.interval.setSuffix(" 秒 / 张")
        self.interval.setSingleStep(0.5)
        form.addWidget(self.interval)
        self.transition = QComboBox()
        self.transition.addItems(["直接切换", "柔和淡入淡出 · 0.3 秒", "柔和淡入淡出 · 0.6 秒", "柔和淡入淡出 · 1 秒"])
        form.addWidget(self.transition)
        self.loop = QCheckBox("循环播放整个列表")
        self.shuffle = QCheckBox("随机播放（不连续重复）")
        form.addWidget(self.loop)
        form.addWidget(self.shuffle)
        form.addWidget(label("视频速度", "muted"))
        self.speed = QComboBox()
        self.speed.addItems(["0.5×", "0.75×", "1.0×", "1.25×", "1.5×", "2.0×"])
        form.addWidget(self.speed)
        form.addSpacing(5)
        form.addWidget(label("摄像头后端", "muted"))
        self.backend = QComboBox()
        self.backend.addItems(["自动选择", "Unity Capture · DirectShow", "OBS · DirectShow", "Windows 原生 · 推荐 Win11"])
        form.addWidget(button("应用会议兼容预设", self.compatibility_preset, "quiet"))
        form.addWidget(self.backend)
        self.device_label = label("正在检测…", "muted")
        self.device_label.setWordWrap(True)
        rl.addWidget(scroll, 1)
        rl.addWidget(self.device_label)
        self.install_button = button("安装摄像头组件", self.install_driver, "quiet")
        rl.addWidget(self.install_button)
        device_actions = QHBoxLayout()
        device_actions.setSpacing(6)
        device_actions.addWidget(button("重新检测", self.refresh_device, "quiet"))
        device_actions.addWidget(button("诊断 / 日志", self.show_diagnostics, "quiet"))
        rl.addLayout(device_actions)
        self.check_button = button("接收自检", self.run_receiver_check, "quiet")
        rl.addWidget(self.check_button)
        form.addStretch()
        scroll.setWidget(controls)
        columns.addWidget(right)
        layout.addLayout(columns, 1)

        footer = QHBoxLayout()
        footer.addWidget(label("●  LOCAL FIRST    /    本地素材 · 实时合成", "muted"))
        footer.addStretch()
        footer.addWidget(label(f"帧幕 {__version__}  ·  Windows x64", "muted"))
        layout.addLayout(footer)
        for control in (self.resolution, self.fps, self.fit, self.transition, self.speed, self.backend):
            control.currentIndexChanged.connect(self.apply_settings)
        for control in (self.loop, self.shuffle, self.mirror):
            control.toggled.connect(self.apply_settings)
        self.interval.valueChanged.connect(self.apply_settings)

    def load_controls(self):
        s = self.settings
        self.resolution.setCurrentIndex([(1280, 720), (1920, 1080), (640, 480)].index((s.width, s.height)))
        self.fps.setCurrentIndex([30, 24, 15, 60, 25].index(s.fps))
        self.fit.setCurrentIndex(["contain", "cover", "stretch"].index(s.fit))
        self.transition.setCurrentIndex([0, 0.3, 0.6, 1.0].index(s.transition))
        self.speed.setCurrentIndex([0.5, 0.75, 1, 1.25, 1.5, 2].index(s.speed))
        self.backend.setCurrentIndex(["auto", "unitycapture", "obs", "native"].index(s.backend))
        self.interval.setValue(s.interval)
        self.mirror.setChecked(s.mirror)
        self.loop.setChecked(s.loop)
        self.shuffle.setChecked(s.shuffle)

    def apply_settings(self, *_):
        if self.loading:
            return
        self.settings.width, self.settings.height = [(1280, 720), (1920, 1080), (640, 480)][self.resolution.currentIndex()]
        self.settings.fps = [30, 24, 15, 60, 25][self.fps.currentIndex()]
        self.settings.fit = ["contain", "cover", "stretch"][self.fit.currentIndex()]
        self.settings.transition = [0, 0.3, 0.6, 1.0][self.transition.currentIndex()]
        self.settings.speed = [0.5, 0.75, 1, 1.25, 1.5, 2][self.speed.currentIndex()]
        self.settings.backend = ["auto", "unitycapture", "obs", "native"][self.backend.currentIndex()]
        self.settings.interval = self.interval.value()
        self.settings.loop, self.settings.shuffle, self.settings.mirror = self.loop.isChecked(), self.shuffle.isChecked(), self.mirror.isChecked()
        self.worker.post("settings", self.settings.dict())
        self.format_label.setText(f"{self.settings.width} × {self.settings.height}  /  {self.settings.fps} FPS")
        if hasattr(self, "save_timer"):
            self.save_timer.start(500)

    def choose_color(self):
        color = QColorDialog.getColor(QColor(self.settings.background), self, "选择留边颜色")
        if color.isValid():
            self.settings.background = color.name()
            self.color_button.setText("留边颜色  " + color.name())
            self.apply_settings()

    def compatibility_preset(self):
        if self.output_active or self.output_pending:
            self.show_error("请先停止输出，再切换兼容预设")
            return
        from .native_camera import supported
        self.resolution.setCurrentIndex(0 if supported() else 2)
        self.fps.setCurrentIndex(0)
        self.backend.setCurrentIndex(3 if supported() else 1)
        self.apply_settings()

    def import_media(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "导入图片或视频", "",
            "图片与视频 (*.png *.jpg *.jpeg *.bmp *.webp *.tif *.tiff *.mp4 *.mov *.mkv *.avi *.wmv *.m4v *.webm);;所有文件 (*)")
        self.add_media(paths)

    def add_media(self, paths, reset=False):
        entries = []
        errors = []
        existing = set() if reset else {entry["path"] for entry in self.entries}
        for path in paths[:200]:
            normalized = str(Path(path).resolve())
            if normalized in existing:
                continue
            try:
                entry = probe(normalized)
                entry["icon"] = QIcon(rgb_pixmap(entry.pop("thumbnail")).scaled(144, 90,
                    Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                entries.append(entry)
                existing.add(normalized)
            except Exception as exc:
                logging.warning("Import failed: %s: %s", path, exc)
                errors.append(Path(path).name + "：" + str(exc))
        if reset:
            self.entries = entries
        else:
            self.entries.extend(entries)
        if entries or reset:
            self.rebuild_list(0 if reset else max(0, self.current_index))
        if errors:
            self.show_error("以下素材未导入：\n" + "\n".join(errors[:8]))

    def rebuild_list(self, index=0):
        self.list.blockSignals(True)
        self.list.clear()
        for e in self.entries:
            kind = "图片" if e["kind"] == "image" else f"视频 · {stamp(e['duration'])}"
            name = Path(e["path"]).stem
            if len(name) > 13:
                name = name[:12] + "…"
            item = QListWidgetItem(e["icon"], f"{name}\n{kind}  ·  {e['width']}×{e['height']}")
            item.setSizeHint(QSize(190, 72))
            item.setToolTip(e["path"])
            self.list.addItem(item)
        self.list.setCurrentRow(min(index, len(self.entries) - 1))
        self.list.blockSignals(False)
        self.count_label.setText(f"{len(self.entries):02d}")
        self.current_index = self.list.currentRow()
        self.worker.post("playlist", ([e["path"] for e in self.entries], max(0, self.current_index)))
        self.save_state()

    def select_media(self, index):
        if index >= 0:
            self.current_index = index
            self.worker.post("select", index)

    def remove_media(self):
        index = self.list.currentRow()
        if index >= 0:
            self.entries.pop(index)
            self.rebuild_list(min(index, len(self.entries) - 1))

    def reorder(self, direction):
        index = self.list.currentRow()
        other = index + direction
        if index >= 0 and 0 <= other < len(self.entries):
            self.entries[index], self.entries[other] = self.entries[other], self.entries[index]
            self.rebuild_list(other)

    def load_demo(self):
        self.add_media([str(p) for p in sorted((resources() / "assets" / "demo").glob("*.png"))], reset=True)

    def restore_media(self):
        if "paths" in self.restored:
            paths = []
            for p in self.restored["paths"]:
                if p.startswith("demo:"):
                    p = str(resources() / "assets" / "demo" / Path(p[5:]).name)
                paths.append(p)
            self.add_media(paths)
        else:
            self.load_demo()

    def toggle_pause(self):
        self.paused = not self.paused
        self.worker.post("pause", self.paused)
        self.pause_button.setText("▶  继续" if self.paused else "Ⅱ  暂停")

    def toggle_black(self):
        self.black = not self.black
        self.black_button.setChecked(self.black)
        self.black_button.setText("恢复画面" if self.black else "黑屏待机")
        self.worker.post("black", self.black)
        self.preview_badge.setText("●  BLACKOUT" if self.black else "●  PREVIEW")

    def toggle_output(self):
        if self.output_pending:
            return
        if not self.output_active and not self.entries:
            self.show_error("请先导入素材")
            return
        self.output_pending = True
        self.output_button.setEnabled(False)
        for control in (self.resolution, self.fps, self.backend):
            control.setEnabled(False)
        self.output_button.setText("正在连接…" if not self.output_active else "正在停止…")
        self.worker.post("output", not self.output_active)

    def output_changed(self, active, device):
        self.output_active = active
        self.output_device = device
        self.output_pending = False
        self.output_button.setEnabled(True)
        self.output_button.setText("■  停止虚拟摄像头" if active else "◉  开启虚拟摄像头")
        self.output_button.setObjectName("danger" if active else "primary")
        self.output_button.style().unpolish(self.output_button)
        self.output_button.style().polish(self.output_button)
        for control in (self.resolution, self.fps, self.backend):
            control.setEnabled(not active)
        self.started_at = time.monotonic() if active else None
        self.top_status.setText("●  正在发送画面" if active else "●  仅本地预览")
        self.top_status.setStyleSheet("color:#a5f3cf;" if active else "")
        self.output_title.setText("虚拟摄像头已开启" if active else "准备好，就开始输出")
        self.output_hint.setText(f"会议软件中选择「{device}」。接收端是否已连接需在会议软件中确认。" if active
            else "开启后，在会议软件中选择对应的虚拟摄像头。")

    def refresh_preview(self):
        snapshot = self.worker.snapshot()
        if not snapshot or snapshot[0] == self.last_serial:
            return
        serial, rgb, index, elapsed, duration, fps, sent, finished = snapshot
        self.last_serial = serial
        self.preview.pixmap = rgb_pixmap(rgb)
        self.preview.update()
        self.current_index = index
        if self.list.currentRow() != index:
            self.list.blockSignals(True)
            self.list.setCurrentRow(index)
            self.list.blockSignals(False)
        self.elapsed_label.setText(stamp(elapsed))
        self.duration_label.setText(stamp(duration))
        if not self.seek.isSliderDown():
            self.seek.setValue(round(1000 * elapsed / duration) if duration > 0 else 0)
        if 0 <= index < len(self.entries):
            name = Path(self.entries[index]["path"]).name
            if len(name) > 32:
                name = name[:29] + "…"
            self.media_title.setText(name + ("  ·  已播完" if finished else ""))
            self.position_label.setText(f"{index + 1:02d} / {len(self.entries):02d}")
        else:
            self.media_title.setText("等待导入素材")
            self.position_label.setText("— / —")
        self.format_label.setText(f"{self.settings.width} × {self.settings.height}  /  {fps:.0f} FPS")
        if self.started_at is not None:
            seconds = int(time.monotonic() - self.started_at)
            self.output_time.setText(f"{seconds // 3600:02d}:{seconds // 60 % 60:02d}:{seconds % 60:02d}")
        else:
            self.output_time.setText("00:00:00")

    def refresh_device(self):
        from .native_camera import registered
        cameras = registered_cameras()
        compatible = [name for name in cameras if "Unity" in name or "OBS Virtual" in name]
        if registered():
            compatible.insert(0, "Frameveil Camera · Windows 原生")
        self.device_label.setText("已检测到：\n" + "\n".join(compatible) if compatible else "尚未检测到虚拟摄像头\n预览可用；输出前请安装组件")
        self.install_button.setText("摄像头组件管理" if compatible else "安装摄像头组件")
        return cameras

    def install_driver(self):
        if self.installer and self.installer.isRunning():
            return
        if self.output_active:
            self.show_error("请先停止虚拟摄像头输出")
            return
        from .native_camera import supported, registered
        if supported():
            choice = QMessageBox(self)
            choice.setWindowTitle("选择摄像头组件")
            choice.setText("Windows 11 推荐原生摄像头，用于现代摄像头接口。")
            choice.setInformativeText("原生组件使用独立设备名 Frameveil Camera，不需要 OBS。首次安装需管理员授权。Windows 10 可继续使用 Unity Capture。")
            native = choice.addButton("安装 / 修复 Windows 原生组件", QMessageBox.ButtonRole.AcceptRole)
            legacy = choice.addButton("Unity Capture 组件管理", QMessageBox.ButtonRole.ActionRole)
            remove = choice.addButton("卸载原生组件", QMessageBox.ButtonRole.DestructiveRole) if registered() else None
            choice.addButton("取消", QMessageBox.ButtonRole.RejectRole)
            choice.exec()
            selected = choice.clickedButton()
            if selected is native or (remove is not None and selected is remove):
                self.installer = Installer(selected is remove, "native")
                self.installer.done.connect(self.installer_done)
                self.install_button.setEnabled(False)
                self.installer.start()
                return
            if selected is not legacy:
                return
        cameras = self.refresh_device()
        owned = (install_directory() / "frameveil-owned.json").exists()
        if "Unity Video Capture" in cameras and not owned:
            QMessageBox.information(self, "组件已就绪", "已检测到现有的 Unity Video Capture，帧幕会直接复用。")
            return
        dialog = QMessageBox(self)
        dialog.setWindowTitle("摄像头组件管理")
        dialog.setText("安装 Unity Capture 虚拟摄像头")
        dialog.setInformativeText("仅需首次安装。将注册 32 位与 64 位摄像头组件，设备名为 Unity Video Capture。\n\n来源：github.com/schellingb/UnityCapture（MIT）\n安装位置：" + str(install_directory()) + "\n\n会弹出 Windows 管理员授权；无需安装 Python 或 OBS。")
        install = dialog.addButton("安装组件", QMessageBox.ButtonRole.AcceptRole)
        uninstall = dialog.addButton("卸载帧幕安装的组件", QMessageBox.ButtonRole.DestructiveRole) if owned else None
        dialog.addButton("取消", QMessageBox.ButtonRole.RejectRole)
        dialog.exec()
        chosen = dialog.clickedButton()
        if chosen is not install and (uninstall is None or chosen is not uninstall):
            return
        self.installer = Installer(uninstall is not None and chosen is uninstall)
        self.installer.done.connect(self.installer_done)
        self.install_button.setEnabled(False)
        self.installer.start()

    def installer_done(self, success, message):
        self.install_button.setEnabled(True)
        self.refresh_device()
        if success:
            QMessageBox.information(self, "摄像头组件", message)
        else:
            self.show_error(message)

    def show_error(self, text):
        QMessageBox.warning(self, "帧幕 · 提示", text)

    def run_receiver_check(self):
        if not self.output_active:
            self.show_error("请先开启输出，再测试系统接收链路")
            return
        if self.receiver_check and self.receiver_check.isRunning():
            return
        from .diagnostics import ReceiverCheck
        self.receiver_check = ReceiverCheck(self.output_device)
        self.receiver_check.done.connect(self.receiver_check_done)
        self.check_button.setEnabled(False)
        self.check_button.setText("正在接收测试…")
        self.receiver_check.start()

    def receiver_check_done(self, success, message):
        self.check_button.setEnabled(True)
        self.check_button.setText("接收自检")
        if success:
            QMessageBox.information(self, "接收验证通过", message)
        else:
            self.show_error(message)

    def text_dialog(self, title, html, diagnostics=False):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.resize(650, 610)
        layout = QVBoxLayout(dialog)
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setStyleSheet("QTextBrowser { background:#181a22; border:1px solid #303543; border-radius:12px; padding:18px; } a { color:#b9adff; }")
        browser.setHtml(html)
        layout.addWidget(browser)
        if diagnostics:
            layout.addWidget(button("打开日志文件夹", lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(data_directory())))))
        layout.addWidget(button("关闭", dialog.accept))
        dialog.exec()

    def show_guide(self):
        self.text_dialog("帧幕 · 使用指南", """<h2>从素材到摄像头，三步开始</h2>
<p>1. 导入图片或视频，在工作台检查画面。多张图片会按间隔依次轮播；单个视频可循环。</p>
<p>2. Windows 11 在右侧组件管理安装 Windows 原生组件；Windows 10 安装 Unity Capture。首次完成 Windows 管理员授权。</p>
<p>3. 点击「应用会议兼容预设」，再开启输出。Windows 11 在会议端选择 <b>Frameveil Camera (Windows Virtual Camera)</b>；Unity 后端选择 Unity Video Capture；OBS 后端选择 OBS Virtual Camera。必须与下方正在输出的设备名一致。</p>
<p>原生设备在输出开启后出现，应先开启帧幕，再打开会议设备列表。若客户端缓存旧列表，请重启客户端。原生模式可通过「接收自检」验证系统接收链路。</p>
<h3>日常控制</h3><p>暂停：冻结播放，仍持续发送画面。<br>黑屏待机：持续发送黑色画面；再次点击恢复。<br>停止：释放虚拟摄像头；会议软件可能保留末帧或显示设备离线。<br>上/下一项：立即切换素材；进度条可定位视频或图片时间轴。</p>
<h3>一轮测试</h3><p>先用演示素材验证轮播，再导入自己的两张图片和一个短 MP4。尝试 2 秒轮播、镜像、暂停、黑屏、停止与重启输出。在会议预览和另一台设备接收端分别确认画面。</p>
<p>钉钉、微信不同版本的设备选择方式与虚拟摄像头支持可能不同。客户端没有摄像头选择入口、看不到设备或拒绝虚拟设备时，当前版本可能无法使用。</p>
<p>视频只输出画面，没有音频；不会读取真实摄像头或麦克风。退出不会自动切换到真实摄像头。请在会议端再次确认摄像头状态。</p>
<p>快捷键（应用内）：Ctrl+O 导入；Ctrl+Shift+B 黑屏；Ctrl+Shift+S 开关输出。</p>
<p>设置和素材路径保存在本机；下次启动恢复预览，摄像头输出始终需手动开启。</p>""")

    def show_diagnostics(self):
        import html
        cameras = self.refresh_device()
        snapshot = self.worker.snapshot()
        from .native_camera import supported, registered
        from .diagnostics import native_device_list
        info = {"version": __version__, "cameras_64bit": cameras, "output_active": self.output_active,
                "selected_output_device": self.output_device,
                "native_supported": supported(), "native_registered": registered(),
                "media_foundation_devices": native_device_list(),
                "settings": self.settings.dict(), "frames_sent": snapshot[6] if snapshot else 0,
                "render_fps": round(snapshot[5], 2) if snapshot else 0, "logs": str(data_directory())}
        self.text_dialog("帧幕 · 本地诊断", "<h2>运行状态</h2><pre>" + html.escape(json.dumps(info, ensure_ascii=False, indent=2)) + "</pre><p>发送帧数只证明帧幕已向组件发送数据。接收端画面需要在会议软件中检查。</p>", True)

    def load_state(self):
        try:
            state = json.loads((data_directory() / "settings.json").read_text(encoding="utf-8"))
            raw = state.get("settings", {})
            allowed = Settings().dict()
            self.settings = Settings(**{k: v for k, v in raw.items() if k in allowed})
            s = self.settings
            assert (s.width, s.height) in [(1280, 720), (1920, 1080), (640, 480)]
            assert s.fps in [15, 24, 25, 30, 60] and s.fit in ["contain", "cover", "stretch"]
            assert s.transition in [0, 0.3, 0.6, 1] and s.speed in [0.5, 0.75, 1, 1.25, 1.5, 2]
            assert s.backend in ["auto", "obs", "unitycapture", "native"] and 0.5 <= s.interval <= 3600
            assert isinstance(s.background, str) and len(s.background) == 7 and s.background.startswith("#")
            int(s.background[1:], 16)
            assert isinstance(state.get("paths", []), list) and all(isinstance(p, str) for p in state.get("paths", []))
            return state
        except Exception:
            self.settings = Settings()
            return {}

    def save_state(self):
        paths = []
        demo_folder = resources() / "assets" / "demo"
        for entry in self.entries:
            path = Path(entry["path"])
            paths.append("demo:" + path.name if path.parent == demo_folder else str(path))
        try:
            destination = data_directory() / "settings.json"
            temporary = destination.with_suffix(".tmp")
            temporary.write_text(json.dumps({"settings": self.settings.dict(), "paths": paths}, ensure_ascii=False, indent=2), encoding="utf-8")
            temporary.replace(destination)
        except OSError:
            logging.exception("Cannot save settings")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        self.add_media([u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()])
        event.acceptProposedAction()

    def closeEvent(self, event):
        if self.receiver_check and self.receiver_check.isRunning():
            self.show_error("接收自检正在进行，请等待完成后再关闭")
            event.ignore()
            return
        if self.installer and self.installer.isRunning():
            self.show_error("摄像头组件操作仍在进行，请完成后再关闭")
            event.ignore()
            return
        self.save_state()
        self.worker.post("quit")
        # Do not terminate a thread holding a decoder/virtual-camera handle.
        if not self.worker.wait(8000):
            self.show_error("正在释放媒体设备，请稍后再关闭")
            event.ignore()
            return
        event.accept()


def run(screenshot=None):
    app = QApplication.instance() or QApplication([])
    app.setApplicationName("Frameveil")
    app.setOrganizationName("Frameveil")
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE.replace("CHECK_PATH", (resources() / "assets" / "check.svg").as_posix()))
    window = Window()
    window.show()
    if screenshot:
        def capture():
            Path(screenshot).parent.mkdir(parents=True, exist_ok=True)
            window.grab().save(str(screenshot))
        QTimer.singleShot(1800, capture)
    return app.exec()
