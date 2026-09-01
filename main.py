import sys
import os
import logging
import traceback

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QProgressBar,
    QMessageBox, QFrame, QScrollArea, QSplitter, QSizePolicy,
    QGraphicsDropShadowEffect, QDialog, QSlider, QGraphicsOpacityEffect,
    QMenuBar, QMenu
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QEasingCurve, QPropertyAnimation,
    QPoint, QPropertyAnimation, QEvent
)
from PyQt6.QtGui import QPixmap, QImage, QIcon, QFont, QDragEnterEvent, QDropEvent, QColor, QAction

import cv2
import numpy as np

from enhancer import make_clear, auto_params
from usage_tracker import UsageTracker

__version__ = "0.0.2"
AUTHOR = "zwb8926"
PROJECT_URL = "https://github.com/zwb8926/photoclear"

SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp'}

LOG_PATH = os.path.join(os.path.expanduser("~"), "photoclear.log")

PRESETS = [
    {"name": "自动", "params": None},
    {"name": "自然通透", "params": {"intensity": 0.5, "dehaze": 0.28, "clarity": 0.15, "saturation": 1.12, "brightness": 0.06}},
    {"name": "清新明亮", "params": {"intensity": 0.6, "dehaze": 0.35, "clarity": 0.2, "saturation": 1.2, "brightness": 0.1}},
    {"name": "浓郁鲜艳", "params": {"intensity": 0.68, "dehaze": 0.3, "clarity": 0.18, "saturation": 1.35, "brightness": 0.08}},
    {"name": "强力去雾", "params": {"intensity": 0.75, "dehaze": 0.55, "clarity": 0.25, "saturation": 1.18, "brightness": 0.12}},
    {"name": "人像美肤", "params": {"intensity": 0.55, "dehaze": 0.22, "clarity": 0.1, "saturation": 1.08, "brightness": 0.12}},
    {"name": "风景锐利", "params": {"intensity": 0.7, "dehaze": 0.4, "clarity": 0.32, "saturation": 1.25, "brightness": 0.05}},
    {"name": "阴天提亮", "params": {"intensity": 0.65, "dehaze": 0.5, "clarity": 0.15, "saturation": 1.18, "brightness": 0.18}},
    {"name": "夜景降噪", "params": {"intensity": 0.58, "dehaze": 0.42, "clarity": 0.08, "saturation": 1.25, "brightness": 0.15}},
    {"name": "电影质感", "params": {"intensity": 0.62, "dehaze": 0.38, "clarity": 0.12, "saturation": 1.05, "brightness": 0.04}},
]

DEFAULT_PRESET = 0


def resource_path(relative):
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative)


def setup_logging():
    global LOG_PATH
    try:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[logging.FileHandler(LOG_PATH, encoding='utf-8')],
        )
    except Exception:
        LOG_PATH = os.path.join(os.environ.get('TEMP', os.getcwd()), 'photoclear.log')
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[logging.FileHandler(LOG_PATH, encoding='utf-8')],
        )
    logging.info("=" * 50)
    logging.info("PhotoClear 启动")


STYLESHEET = """
* {
    font-family: "Microsoft YaHei UI", "PingFang SC", "Segoe UI", sans-serif;
}
QMainWindow {
    background-color: #f5f5f7;
}
QWidget {
    color: #1d1d1f;
    font-size: 14px;
}

/* ===== 标题栏 ===== */
QFrame#headerBar {
    background-color: #ffffff;
    border-bottom: 1px solid #e5e5e7;
}
QLabel#appTitle {
    font-size: 17px;
    font-weight: 600;
    color: #1d1d1f;
}
QLabel#appSubtitle {
    font-size: 12px;
    color: #86868b;
}

/* ===== 预设栏 ===== */
QFrame#presetBar {
    background-color: #fafafa;
    border-bottom: 1px solid #e5e5e7;
}
QLabel#presetLabel {
    font-size: 12px;
    color: #86868b;
    font-weight: 600;
}
QPushButton#presetBtn {
    background-color: #ffffff;
    color: #3a3a3c;
    border: 1px solid #d1d1d6;
    border-radius: 16px;
    padding: 5px 16px;
    font-size: 12px;
    font-weight: 500;
}
QPushButton#presetBtn:hover {
    background-color: #f0f0f5;
    border-color: #aeaeb2;
}
QPushButton#presetBtn:checked {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #007aff, stop:1 #34c759);
    color: #ffffff;
    border: none;
}

/* ===== 预览区 ===== */
QFrame#previewArea {
    background-color: #f5f5f7;
    border: none;
}
QFrame#previewCard {
    background-color: #ffffff;
    border-radius: 14px;
    border: 1px solid #e5e5e7;
}
QFrame#dragOverlay {
    border: 3px dashed #007aff;
    border-radius: 14px;
    background-color: rgba(0, 122, 255, 15);
}
QLabel#previewBadge {
    font-size: 11px;
    font-weight: 600;
    color: #86868b;
    background-color: #f0f0f5;
    padding: 4px 14px;
    border-radius: 16px;
}
QLabel#resultBadge {
    font-size: 11px;
    font-weight: 600;
    color: #ffffff;
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #34c759, stop:1 #30d158);
    padding: 4px 14px;
    border-radius: 16px;
}
QScrollArea#previewScroll {
    border: none;
    background-color: transparent;
    border-radius: 10px;
}
QLabel#previewLabel {
    color: #86868b;
    font-size: 14px;
    background-color: transparent;
}
QLabel#zoomHint {
    font-size: 11px;
    color: #c7c7cc;
}
QSplitter::handle {
    background-color: transparent;
    width: 6px;
}
QSplitter::handle:hover {
    background-color: #d1d1d6;
    border-radius: 2px;
}

/* ===== 参数面板 ===== */
QFrame#paramPanel {
    background-color: #ffffff;
    border-top: 1px solid #e5e5e7;
}
QLabel#paramName {
    font-size: 11px;
    color: #6e6e73;
    font-weight: 500;
}
QLabel#paramValue {
    font-size: 11px;
    color: #007aff;
    font-weight: 600;
    background-color: #e8f0fe;
    padding: 1px 8px;
    border-radius: 8px;
    min-width: 32px;
    qproperty-alignment: AlignCenter;
}
QSlider::groove:horizontal {
    height: 4px;
    background: #e5e5e7;
    border-radius: 2px;
}
QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #007aff, stop:1 #34c759);
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #ffffff;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
    border: 2px solid #007aff;
}
QSlider::handle:horizontal:hover {
    border-color: #006fe0;
}

/* ===== 主按钮 ===== */
QPushButton#bigBtn {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #007aff, stop:1 #34c759);
    color: #ffffff;
    font-size: 13px;
    font-weight: 600;
    border: none;
    border-radius: 8px;
    padding: 7px 22px;
}
QPushButton#bigBtn:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #006fe0, stop:1 #2bb84e);
}
QPushButton#bigBtn:pressed {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0062c4, stop:1 #25a544);
}
QPushButton#bigBtn:disabled {
    background-color: #d1d1d6;
    color: #ffffff;
}

/* ===== 进度条 ===== */
QProgressBar {
    border: none;
    border-radius: 4px;
    text-align: center;
    color: #ffffff;
    background-color: #e5e5e7;
    max-height: 4px;
    font-size: 10px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #007aff, stop:1 #34c759);
    border-radius: 4px;
}

/* ===== 滚动条 ===== */
QScrollBar:vertical {
    background: transparent;
    width: 4px;
    border: none;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #d1d1d6;
    min-height: 40px;
    border-radius: 2px;
}
QScrollBar::handle:vertical:hover { background: #86868b; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: transparent;
    height: 4px;
    border: none;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: #d1d1d6;
    min-width: 40px;
    border-radius: 2px;
}
QScrollBar::handle:horizontal:hover { background: #86868b; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ===== Toast ===== */
QFrame#toast {
    background-color: #1d1d1f;
    border-radius: 12px;
}
QLabel#toastText {
    color: #ffffff;
    font-size: 13px;
    font-weight: 500;
}
QLabel#toastIcon {
    font-size: 18px;
}

/* ===== 状态栏 ===== */
QFrame#statusBar {
    background-color: #ffffff;
    border-top: 1px solid #e5e5e7;
}
QLabel#statusText {
    font-size: 11px;
    color: #86868b;
}
QLabel#authorText {
    font-size: 11px;
    color: #aeaeb2;
}
QLabel#authorText a {
    color: #007aff;
    text-decoration: none;
}

/* ===== 对话框 ===== */
QDialog, QMessageBox {
    background-color: #ffffff;
}
QMessageBox QLabel {
    color: #1d1d1f;
    font-size: 14px;
}
QMessageBox QPushButton {
    min-width: 70px;
    padding: 8px 20px;
    background-color: #ffffff;
    color: #1d1d1f;
    border: 1px solid #d1d1d6;
    border-radius: 8px;
    font-size: 13px;
}
QMessageBox QPushButton:hover {
    background-color: #f5f5f7;
    border-color: #86868b;
}
QDialog#zoomDialog { background-color: #1d1d1f; }

QToolTip {
    background-color: #1d1d1f;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}

QMenuBar {
    background-color: #ffffff;
    border-bottom: 1px solid #e5e5e7;
    padding: 2px;
}
QMenuBar::item {
    padding: 4px 12px;
    border-radius: 4px;
}
QMenuBar::item:selected {
    background-color: #f0f0f5;
}
QMenu {
    background-color: #ffffff;
    border: 1px solid #e5e5e7;
    border-radius: 8px;
    padding: 4px;
}
QMenu::item {
    padding: 6px 24px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #f0f0f5;
}
"""


def add_shadow(widget, blur=30, offset_y=4, color=QColor(0, 0, 0, 80)):
    effect = QGraphicsDropShadowEffect()
    effect.setBlurRadius(blur)
    effect.setOffset(0, offset_y)
    effect.setColor(color)
    widget.setGraphicsEffect(effect)


def cv2_to_qpixmap(img):
    if img is None:
        return QPixmap()
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    h, w, c = img_rgb.shape
    bytes_per_line = c * w
    q_img = QImage(img_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
    return QPixmap.fromImage(q_img)


def load_image_unicode(path):
    with open(str(path), 'rb') as f:
        data = np.frombuffer(f.read(), dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def save_image_unicode(img, path):
    path = os.path.normpath(str(path))
    ext = os.path.splitext(path)[1]
    success, buf = cv2.imencode(ext, img)
    if not success:
        raise RuntimeError(f"无法编码为 {ext} 格式")
    with open(path, 'wb') as f:
        f.write(buf.tobytes())


def make_copy_filename(filename):
    name, ext = os.path.splitext(filename)
    return f"{name}_副本{ext}"


class Toast(QFrame):
    def __init__(self, text, parent=None, duration=3000, success=True):
        super().__init__(parent)
        self.setObjectName("toast")
        self.setFixedHeight(44)
        add_shadow(self, blur=40, offset_y=4, color=QColor(0, 0, 0, 60))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(10)

        icon = QLabel("✓" if success else "!")
        icon.setObjectName("toastIcon")
        icon.setStyleSheet(f"color: {'#34c759' if success else '#ff3b30'};")
        layout.addWidget(icon)

        label = QLabel(text)
        label.setObjectName("toastText")
        layout.addWidget(label)
        layout.addStretch()

        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

        parent_w = parent.width() if parent else 800
        toast_w = 320
        self.setFixedWidth(toast_w)
        self.move((parent_w - toast_w) // 2, 60)

        self._opacity = QGraphicsOpacityEffect(self)
        self._opacity.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity)

        self._anim_in = QPropertyAnimation(self._opacity, b"opacity")
        self._anim_in.setDuration(250)
        self._anim_in.setStartValue(0.0)
        self._anim_in.setEndValue(1.0)
        self._anim_in.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._anim_out = QPropertyAnimation(self._opacity, b"opacity")
        self._anim_out.setDuration(300)
        self._anim_out.setStartValue(1.0)
        self._anim_out.setEndValue(0.0)
        self._anim_out.setEasingCurve(QEasingCurve.Type.InCubic)
        self._anim_out.finished.connect(self.deleteLater)

        self._anim_in.start()
        QTimer.singleShot(duration, self._dismiss)

    def _dismiss(self):
        self._anim_out.start()


class ZoomScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._dragging = False
        self._drag_start = None
        self._drag_bar_pos = None
        self.setCursor(Qt.CursorShape.OpenHandCursor)

    def wheelEvent(self, event):
        dlg = self.window()
        if isinstance(dlg, ZoomDialog):
            delta = event.angleDelta().y()
            if delta > 0:
                dlg._zoom(0.1)
            else:
                dlg._zoom(-0.1)
            event.accept()
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_start = event.position().toPoint()
            self._drag_bar_pos = (
                self.horizontalScrollBar().value(),
                self.verticalScrollBar().value(),
            )
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging and self._drag_start is not None:
            delta = event.position().toPoint() - self._drag_start
            self.horizontalScrollBar().setValue(self._drag_bar_pos[0] - delta.x())
            self.verticalScrollBar().setValue(self._drag_bar_pos[1] - delta.y())
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._dragging:
            self._dragging = False
            self._drag_start = None
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)


class ZoomDialog(QDialog):
    def __init__(self, pixmap, title="图片查看", parent=None):
        super().__init__(parent)
        self.setObjectName("zoomDialog")
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(1400, 900)
        self._pixmap = pixmap
        self._scale = 1.0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        top_bar = QFrame()
        top_bar.setStyleSheet("QFrame { background-color: #2d2d2f; }")
        top_bar.setFixedHeight(40)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(16, 0, 16, 0)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: 500;")
        top_layout.addWidget(title_lbl)
        top_layout.addStretch()

        zoom_out_btn = QPushButton("−")
        zoom_out_btn.setFixedSize(28, 24)
        zoom_out_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        zoom_out_btn.setStyleSheet(
            "QPushButton { background: #3a3a3c; color: #fff; border: none; border-radius: 5px; font-size: 14px; }"
            "QPushButton:hover { background: #4a4a4c; }"
        )
        zoom_out_btn.clicked.connect(lambda: self._zoom(-0.2))

        self.zoom_label = QLabel("100%")
        self.zoom_label.setStyleSheet("color: #86868b; font-size: 11px; padding: 0 8px;")
        self.zoom_label.setFixedWidth(50)
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        zoom_in_btn = QPushButton("+")
        zoom_in_btn.setFixedSize(28, 24)
        zoom_in_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        zoom_in_btn.setStyleSheet(
            "QPushButton { background: #3a3a3c; color: #fff; border: none; border-radius: 5px; font-size: 14px; }"
            "QPushButton:hover { background: #4a4a4c; }"
        )
        zoom_in_btn.clicked.connect(lambda: self._zoom(0.2))

        fit_btn = QPushButton("适应")
        fit_btn.setFixedHeight(24)
        fit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        fit_btn.setStyleSheet(
            "QPushButton { background: #3a3a3c; color: #fff; border: none; border-radius: 5px; font-size: 11px; padding: 0 10px; }"
            "QPushButton:hover { background: #4a4a4c; }"
        )
        fit_btn.clicked.connect(self._fit_to_window)

        orig_btn = QPushButton("1:1")
        orig_btn.setFixedHeight(24)
        orig_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        orig_btn.setStyleSheet(
            "QPushButton { background: #3a3a3c; color: #fff; border: none; border-radius: 5px; font-size: 11px; padding: 0 10px; }"
            "QPushButton:hover { background: #4a4a4c; }"
        )
        orig_btn.clicked.connect(self._original_size)

        close_btn = QPushButton("关闭")
        close_btn.setFixedHeight(24)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(
            "QPushButton { background: #007aff; color: #fff; border: none; border-radius: 5px; font-size: 11px; padding: 0 14px; }"
            "QPushButton:hover { background: #006fe0; }"
        )
        close_btn.clicked.connect(self.close)

        top_layout.addWidget(zoom_out_btn)
        top_layout.addWidget(self.zoom_label)
        top_layout.addWidget(zoom_in_btn)
        top_layout.addWidget(fit_btn)
        top_layout.addWidget(orig_btn)
        top_layout.addSpacing(12)
        top_layout.addWidget(close_btn)

        layout.addWidget(top_bar, 0)

        self.scroll = ZoomScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(
            "QScrollArea { background-color: #1d1d1f; border: none; }"
            "QScrollBar:vertical { background: #2d2d2f; width: 6px; border-radius: 3px; }"
            "QScrollBar::handle:vertical { background: #6a6a6c; border-radius: 3px; min-height: 30px; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
            "QScrollBar:horizontal { background: #2d2d2f; height: 6px; border-radius: 3px; }"
            "QScrollBar::handle:horizontal { background: #6a6a6c; border-radius: 3px; min-width: 30px; }"
            "QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }"
        )

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("QLabel { background-color: #1d1d1f; }")
        self.scroll.setWidget(self.image_label)

        layout.addWidget(self.scroll, 1)
        QTimer.singleShot(50, self._fit_to_window)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def _zoom(self, factor):
        self._scale = max(0.05, min(8.0, self._scale + factor))
        self._apply_zoom()

    def _apply_zoom(self):
        new_w = int(self._pixmap.width() * self._scale)
        new_h = int(self._pixmap.height() * self._scale)
        scaled = self._pixmap.scaled(
            new_w, new_h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.image_label.setPixmap(scaled)
        self.image_label.setMinimumSize(new_w, new_h)
        self.zoom_label.setText(f"{int(self._scale * 100)}%")

    def _fit_to_window(self):
        vp_w = self.scroll.viewport().width() - 20
        vp_h = self.scroll.viewport().height() - 20
        pw = self._pixmap.width()
        ph = self._pixmap.height()
        if pw <= 0 or ph <= 0:
            return
        self._scale = min(vp_w / pw, vp_h / ph, 1.0)
        if self._scale < 0.05:
            self._scale = 0.05
        self._apply_zoom()

    def _original_size(self):
        self._scale = 1.0
        self._apply_zoom()


class ClickableLabel(QLabel):
    clicked = pyqtSignal()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class ProcessingThread(QThread):
    progress = pyqtSignal(int, int, str)
    finished_ok = pyqtSignal(int, list)
    error_occurred = pyqtSignal(str)

    def __init__(self, input_paths, output_dir, params):
        super().__init__()
        self.input_paths = input_paths
        self.output_dir = output_dir
        self.params = params
        self._stop = False
        self.errors = []

    def stop(self):
        self._stop = True

    def run(self):
        total = len(self.input_paths)
        success_count = 0
        logging.info(f"线程启动: {total} 张图片, 参数: {self.params}")
        try:
            for i, path in enumerate(self.input_paths):
                if self._stop:
                    break
                try:
                    self.progress.emit(i, total, f"加载: {os.path.basename(path)}")
                    img = load_image_unicode(path)
                    if img is None:
                        msg = f"无法读取: {os.path.basename(path)}"
                        self.errors.append(msg)
                        self.error_occurred.emit(msg)
                        self.progress.emit(i + 1, total, os.path.basename(path))
                        continue

                    self.progress.emit(i, total, f"处理: {os.path.basename(path)}")
                    result = make_clear(img, **self.params)

                    out_name = make_copy_filename(os.path.basename(path))
                    out_path = os.path.normpath(os.path.join(self.output_dir, out_name))
                    self.progress.emit(i, total, f"保存: {out_name}")
                    save_image_unicode(result, out_path)
                    success_count += 1
                    self.progress.emit(i + 1, total, out_name)
                except Exception as e:
                    logging.error(f"[{i+1}/{total}] 异常: {e}\n{traceback.format_exc()}")
                    msg = f"{os.path.basename(path)}: {e}"
                    self.errors.append(msg)
                    self.error_occurred.emit(msg)
                    self.progress.emit(i + 1, total, os.path.basename(path))
        except Exception as e:
            logging.error(f"线程异常: {e}\n{traceback.format_exc()}")
            self.errors.append(f"线程异常: {e}")
            self.error_occurred.emit(f"线程异常: {e}")
        finally:
            self.finished_ok.emit(success_count, self.errors)


class PhotoClearApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.preview_image = None
        self.input_paths = []
        self.output_dir = ""
        self.thread = None
        self.current_preset = DEFAULT_PRESET
        self._updating_from_preset = False
        self._drag_overlay = None
        self.tracker = UsageTracker(__version__)
        self.tracker.track_launch()
        self.init_ui()
        self.setAcceptDrops(True)

    def init_ui(self):
        self.setWindowTitle(f"PhotoClear — 让每张照片更通透")
        self.setWindowIcon(QIcon(resource_path("icon.ico")))
        self.setMinimumSize(1040, 700)
        self.resize(1320, 860)
        self._center_window()

        self._build_menubar()

        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        outer.addWidget(self._build_header(), 0)
        outer.addWidget(self._build_preset_bar(), 0)
        outer.addWidget(self._build_preview(), 1)
        outer.addWidget(self._build_param_panel(), 0)
        outer.addWidget(self._build_statusbar(), 0)

    def _center_window(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def _build_menubar(self):
        mb = self.menuBar()
        mb.setStyleSheet("QMenuBar { background: #ffffff; border-bottom: 1px solid #e5e5e7; }")

        file_menu = mb.addMenu("文件")
        open_act = QAction("打开图片...", self)
        open_act.setShortcut("Ctrl+O")
        open_act.triggered.connect(self._select_files)
        file_menu.addAction(open_act)

        open_folder_act = QAction("打开文件夹...", self)
        open_folder_act.setShortcut("Ctrl+Shift+O")
        open_folder_act.triggered.connect(self._select_folder)
        file_menu.addAction(open_folder_act)

        file_menu.addSeparator()
        process_act = QAction("开始处理", self)
        process_act.setShortcut("Ctrl+Return")
        process_act.triggered.connect(self._start_processing)
        file_menu.addAction(process_act)

        help_menu = mb.addMenu("帮助")
        about_act = QAction("关于 PhotoClear", self)
        about_act.triggered.connect(self._show_about)
        help_menu.addAction(about_act)

        log_act = QAction("查看日志", self)
        log_act.triggered.connect(self._open_log)
        help_menu.addAction(log_act)

        github_act = QAction("GitHub 项目", self)
        github_act.triggered.connect(lambda: os.startfile(PROJECT_URL))
        help_menu.addAction(github_act)

    def _build_header(self):
        bar = QFrame()
        bar.setObjectName("headerBar")
        bar.setFixedHeight(48)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 0, 16, 0)
        layout.setSpacing(10)

        icon_label = QLabel()
        icon_pixmap = QPixmap(resource_path("icon.ico"))
        if not icon_pixmap.isNull():
            icon_label.setPixmap(icon_pixmap.scaled(
                24, 24, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
        layout.addWidget(icon_label)

        title_label = QLabel("PhotoClear")
        title_label.setObjectName("appTitle")
        layout.addWidget(title_label)

        sub_label = QLabel(f"v{__version__}")
        sub_label.setObjectName("appSubtitle")
        layout.addWidget(sub_label)

        layout.addStretch()

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMaximumWidth(160)
        self.progress_bar.setFixedHeight(4)
        layout.addWidget(self.progress_bar)

        self.big_btn = QPushButton("开始")
        self.big_btn.setObjectName("bigBtn")
        self.big_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.big_btn.setEnabled(False)
        self.big_btn.setFixedWidth(80)
        self.big_btn.clicked.connect(self._start_processing)
        layout.addWidget(self.big_btn)

        return bar

    def _build_preset_bar(self):
        bar = QFrame()
        bar.setObjectName("presetBar")
        bar.setFixedHeight(44)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(6)

        hint = QLabel("预设")
        hint.setObjectName("presetLabel")
        layout.addWidget(hint)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFixedHeight(32)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")

        btn_wrap = QWidget()
        btn_layout = QHBoxLayout(btn_wrap)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(6)

        self.preset_buttons = []
        for i, preset in enumerate(PRESETS):
            btn = QPushButton(preset["name"])
            btn.setObjectName("presetBtn")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            if i == DEFAULT_PRESET:
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, idx=i: self._on_preset_clicked(idx))
            btn_layout.addWidget(btn)
            self.preset_buttons.append(btn)

        btn_layout.addStretch()
        scroll.setWidget(btn_wrap)
        layout.addWidget(scroll, 1)
        return bar

    def _build_preview(self):
        container = QFrame()
        container.setObjectName("previewArea")

        preview_wrap = QWidget()
        p_layout = QVBoxLayout(preview_wrap)
        p_layout.setContentsMargins(12, 8, 12, 4)
        p_layout.setSpacing(6)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(6)
        self.splitter.setChildrenCollapsible(False)

        orig_card = QFrame()
        orig_card.setObjectName("previewCard")
        add_shadow(orig_card, blur=24, offset_y=2, color=QColor(0, 0, 0, 25))
        orig_layout = QVBoxLayout(orig_card)
        orig_layout.setContentsMargins(12, 10, 12, 12)
        orig_layout.setSpacing(6)

        orig_top = QHBoxLayout()
        orig_badge = QLabel(" 原图 ")
        orig_badge.setObjectName("previewBadge")
        orig_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        orig_top.addWidget(orig_badge)
        orig_top.addStretch()
        zoom_hint1 = QLabel("点击放大")
        zoom_hint1.setObjectName("zoomHint")
        orig_top.addWidget(zoom_hint1)
        orig_layout.addLayout(orig_top)

        self.preview_original = ClickableLabel()
        self.preview_original.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_original.setMinimumSize(200, 220)
        self.preview_original.setObjectName("previewLabel")
        self.preview_original.setCursor(Qt.CursorShape.PointingHandCursor)
        self.preview_original.clicked.connect(self._on_preview_click)
        self._set_empty_state(self.preview_original)

        scroll_orig = QScrollArea()
        scroll_orig.setObjectName("previewScroll")
        scroll_orig.setWidgetResizable(True)
        scroll_orig.setWidget(self.preview_original)
        orig_layout.addWidget(scroll_orig, 1)
        self.splitter.addWidget(orig_card)

        result_card = QFrame()
        result_card.setObjectName("previewCard")
        add_shadow(result_card, blur=24, offset_y=2, color=QColor(0, 0, 0, 25))
        result_layout = QVBoxLayout(result_card)
        result_layout.setContentsMargins(12, 10, 12, 12)
        result_layout.setSpacing(6)

        result_top = QHBoxLayout()
        result_top.addStretch()
        result_badge = QLabel(" 效果预览 ")
        result_badge.setObjectName("resultBadge")
        result_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        result_top.addWidget(result_badge)
        zoom_hint2 = QLabel("点击放大")
        zoom_hint2.setObjectName("zoomHint")
        result_top.addWidget(zoom_hint2)
        result_layout.addLayout(result_top)

        self.preview_result = ClickableLabel()
        self.preview_result.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_result.setMinimumSize(200, 220)
        self.preview_result.setObjectName("previewLabel")
        self.preview_result.setCursor(Qt.CursorShape.PointingHandCursor)
        self.preview_result.clicked.connect(self._on_preview_click)
        self._set_empty_state(self.preview_result)

        scroll_result = QScrollArea()
        scroll_result.setObjectName("previewScroll")
        scroll_result.setWidgetResizable(True)
        scroll_result.setWidget(self.preview_result)
        result_layout.addWidget(scroll_result, 1)
        self.splitter.addWidget(result_card)

        self.splitter.setSizes([500, 500])
        p_layout.addWidget(self.splitter, 1)

        self._drag_overlay = QFrame()
        self._drag_overlay.setObjectName("dragOverlay")
        self._drag_overlay.setVisible(False)
        drag_layout = QVBoxLayout(self._drag_overlay)
        drag_layout.setContentsMargins(0, 0, 0, 0)
        drag_label = QLabel("松开以加载图片")
        drag_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drag_label.setStyleSheet("font-size: 18px; font-weight: 600; color: #007aff; background: transparent;")
        drag_layout.addWidget(drag_label)

        from PyQt6.QtWidgets import QStackedLayout
        stack = QStackedLayout(container)
        stack.setStackingMode(QStackedLayout.StackingMode.StackAll)
        stack.addWidget(preview_wrap)
        stack.addWidget(self._drag_overlay)

        return container

    def _build_param_panel(self):
        panel = QFrame()
        panel.setObjectName("paramPanel")
        panel.setFixedHeight(58)
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(20, 8, 20, 8)
        layout.setSpacing(16)

        self.sliders = {}
        params = [
            ("通透", 0, 100, 60, "%"),
            ("去雾", 0, 100, 40, "%"),
            ("清晰", 0, 100, 30, "%"),
            ("饱和", 100, 200, 125, ""),
            ("亮度", -50, 50, 10, ""),
        ]

        for name, mn, mx, val, suffix in params:
            col = QVBoxLayout()
            col.setSpacing(3)

            row = QHBoxLayout()
            row.setSpacing(6)
            lbl = QLabel(name)
            lbl.setObjectName("paramName")
            row.addWidget(lbl)
            row.addStretch()
            val_lbl = QLabel(f"{val}{suffix}")
            val_lbl.setObjectName("paramValue")
            row.addWidget(val_lbl)
            col.addLayout(row)

            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(mn, mx)
            slider.setValue(val)
            slider.setCursor(Qt.CursorShape.PointingHandCursor)
            slider.valueChanged.connect(self._on_slider_changed)
            slider.valueChanged.connect(lambda v, l=val_lbl, s=suffix: l.setText(f"{v}{s}"))
            col.addWidget(slider)

            self.sliders[name] = (slider, val_lbl, suffix)
            layout.addLayout(col, 1)

        return panel

    def _set_empty_state(self, label):
        label.setText(
            '<div style="text-align: center; line-height: 2.2;">'
            '<div style="font-size: 36px; margin-bottom: 8px; opacity: 0.4;">&#128247;</div>'
            '<div style="font-size: 14px; color: #aeaeb2; font-weight: 500;">'
            '拖拽图片到此处 或 点击选择</div>'
            '<div style="font-size: 11px; color: #d1d1d6; margin-top: 2px;">'
            'JPG · PNG · BMP · TIFF · WEBP</div>'
            '</div>'
        )

    def _build_statusbar(self):
        bar = QFrame()
        bar.setObjectName("statusBar")
        bar.setFixedHeight(28)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(16)

        self.status_label = QLabel("就绪 · 拖入图片或 Ctrl+O 打开")
        self.status_label.setObjectName("statusText")
        layout.addWidget(self.status_label)

        layout.addStretch()

        author_label = QLabel(
            f'<a href="{PROJECT_URL}" style="color: #aeaeb2; text-decoration: none;">{AUTHOR}</a>'
            '  ·  '
            f'<a href="{PROJECT_URL}" style="color: #aeaeb2; text-decoration: none;">GitHub</a>'
        )
        author_label.setObjectName("authorText")
        author_label.setOpenExternalLinks(True)
        layout.addWidget(author_label)
        return bar

    def _show_about(self):
        QMessageBox.about(self, "关于 PhotoClear",
            f"<div style='text-align: center; font-size: 15px; font-weight: 600;'>PhotoClear v{__version__}</div>"
            f"<br>"
            f"<div style='text-align: center; color: #86868b;'>让每张照片更通透</div>"
            f"<br><br>"
            f"作者: {AUTHOR}<br>"
            f"协议: AGPL-3.0<br>"
            f"GitHub: {PROJECT_URL}"
        )

    def _open_log(self):
        if os.path.exists(LOG_PATH):
            os.startfile(LOG_PATH)
        else:
            QMessageBox.information(self, "日志", "日志文件不存在")

    def _select_files(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "",
            "图片文件 (*.jpg *.jpeg *.png *.bmp *.tiff *.tif *.webp)"
        )
        if path:
            self._load_input([path])

    def _select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            paths = [os.path.join(folder, f) for f in os.listdir(folder)
                     if os.path.splitext(f)[1].lower() in SUPPORTED_FORMATS]
            if paths:
                self._load_input(sorted(paths))
            else:
                QMessageBox.information(self, "提示", "该文件夹下没有支持的图片文件")

    def _load_input(self, paths):
        self.input_paths = paths
        self.output_dir = os.path.dirname(paths[0])
        self.big_btn.setEnabled(True)
        if len(paths) == 1:
            short = os.path.basename(paths[0])
            self.status_label.setText(f"已加载: {short}")
        else:
            self.status_label.setText(f"已加载 {len(paths)} 张图片 · 按开始处理")
        self._load_preview(paths[0])

    def _load_preview(self, path):
        img = load_image_unicode(path)
        if img is None:
            self.status_label.setText("无法读取该图片")
            return
        self.preview_image = img
        if self.current_preset == 0:
            self._on_preset_clicked(0)
        else:
            self._update_preview()

    def _update_preview(self):
        if self.preview_image is None:
            return
        img = self.preview_image
        max_w, max_h = 340, 360
        h, w = img.shape[:2]
        scale = min(max_w / w, max_h / h, 1.0)
        if scale < 1.0:
            small = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
        else:
            small = img

        self.preview_original.setPixmap(cv2_to_qpixmap(small))
        params = self._get_params()
        self.preview_result.setPixmap(cv2_to_qpixmap(make_clear(small, **params)))

    def _on_preset_clicked(self, idx):
        self._updating_from_preset = True
        self.current_preset = idx
        for i, btn in enumerate(self.preset_buttons):
            btn.setChecked(i == idx)
        preset = PRESETS[idx]
        p = preset["params"]
        if p is None:
            if self.preview_image is not None:
                p, info = auto_params(self.preview_image)
                self.status_label.setText(
                    f"自动分析 · 亮度{info['avg_l']:.0f} 对比{info['std_l']:.0f} "
                    f"饱和{info['avg_s']:.0f} 清晰{info['sharpness']:.0f}"
                )
            else:
                p = {"intensity": 0.6, "dehaze": 0.35, "clarity": 0.2, "saturation": 1.2, "brightness": 0.1}
        self.sliders["通透"][0].setValue(int(p["intensity"] * 100))
        self.sliders["去雾"][0].setValue(int(p["dehaze"] * 100))
        self.sliders["清晰"][0].setValue(int(p["clarity"] * 100))
        self.sliders["饱和"][0].setValue(int(p["saturation"] * 100))
        self.sliders["亮度"][0].setValue(int(p["brightness"] * 100))
        self._updating_from_preset = False
        self._update_preview()

    def _get_params(self):
        return {
            "intensity": self.sliders["通透"][0].value() / 100.0,
            "dehaze": self.sliders["去雾"][0].value() / 100.0,
            "clarity": self.sliders["清晰"][0].value() / 100.0,
            "saturation": self.sliders["饱和"][0].value() / 100.0,
            "brightness": self.sliders["亮度"][0].value() / 100.0,
        }

    def _on_slider_changed(self):
        if self._updating_from_preset:
            return
        for btn in self.preset_buttons:
            btn.setChecked(False)
        self._update_preview()

    def _on_preview_click(self):
        if self.preview_image is None:
            self._select_files()
        else:
            sender = self.sender()
            if sender == self.preview_result:
                img = make_clear(self.preview_image, **self._get_params())
                title = "效果预览"
            else:
                img = self.preview_image.copy()
                title = "原图"
            pixmap = cv2_to_qpixmap(img)
            if not pixmap.isNull():
                dlg = ZoomDialog(pixmap, title, self)
                dlg.exec()

    def _start_processing(self):
        if not self.input_paths:
            return
        params = self._get_params()
        logging.info(f"开始处理: {len(self.input_paths)} 张图片, 参数: {params}")
        self.big_btn.setEnabled(False)
        self.big_btn.setText("处理中")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(self.input_paths))
        self.progress_bar.setValue(0)
        self.status_label.setText("正在处理...")

        self.thread = ProcessingThread(self.input_paths, self.output_dir, params)
        self.thread.progress.connect(self._on_progress)
        self.thread.error_occurred.connect(self._on_error)
        self.thread.finished_ok.connect(self._on_finished)
        self.thread.finished.connect(self._on_thread_finished)
        self.thread.start()

    def _on_progress(self, current, total, filename):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_label.setText(f"({current}/{total}) {filename}")

    def _on_error(self, msg):
        self.status_label.setText(f"错误: {msg}")

    def _on_finished(self, count, errors):
        self.tracker.track_process(count)
        if errors:
            error_text = "\n".join(errors[:10])
            if len(errors) > 10:
                error_text += f"\n...还有 {len(errors) - 10} 个错误"
            self.status_label.setText(f"完成 · 成功 {count} 张 · 失败 {len(errors)} 张")
            QMessageBox.warning(self, "处理完成（有错误）",
                f"成功 {count} 张，失败 {len(errors)} 张\n\n{error_text}\n\n日志: {LOG_PATH}")
        else:
            self.status_label.setText(f"完成 · 共处理 {count} 张 · 已保存到原目录")
            Toast(f"处理完成 · {count} 张图片已保存", self, duration=3000, success=True)

    def _on_thread_finished(self):
        self.big_btn.setEnabled(True)
        self.big_btn.setText("开始")
        self.progress_bar.setVisible(False)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            if self._drag_overlay:
                self._drag_overlay.setVisible(True)
                self._drag_overlay.raise_()

    def dragLeaveEvent(self, event):
        if self._drag_overlay:
            self._drag_overlay.setVisible(False)

    def dropEvent(self, event: QDropEvent):
        if self._drag_overlay:
            self._drag_overlay.setVisible(False)
        urls = event.mimeData().urls()
        if not urls:
            return
        path = urls[0].toLocalFile()
        if not path:
            return
        if os.path.isdir(path):
            paths = [os.path.join(path, f) for f in os.listdir(path)
                     if os.path.splitext(f)[1].lower() in SUPPORTED_FORMATS]
            if not paths:
                QMessageBox.information(self, "提示", "该文件夹下没有支持的图片文件")
                return
            self._load_input(sorted(paths))
        elif os.path.splitext(path)[1].lower() in SUPPORTED_FORMATS:
            self._load_input([path])
        else:
            QMessageBox.information(self, "提示", "请拖入图片文件或文件夹")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_O and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self._select_folder()
            else:
                self._select_files()
        elif event.key() == Qt.Key.Key_Return and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self._start_processing()
        else:
            super().keyPressEvent(event)


def main():
    setup_logging()
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    app.setFont(QFont("Microsoft YaHei UI", 10))
    window = PhotoClearApp()
    window.show()
    logging.info("窗口已显示")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
