import sys
import os
import logging
import traceback

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSlider, QFileDialog, QProgressBar,
    QGroupBox, QCheckBox, QMessageBox, QFrame, QScrollArea, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage, QIcon, QFont, QDragEnterEvent, QDropEvent

import cv2
import numpy as np

from enhancer import make_clear

__version__ = "0.0.1"

SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp'}

LOG_PATH = os.path.join(os.path.expanduser("~"), "photoclear.log")


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
    logging.info("照片通透工具启动")
    logging.info(f"Python: {sys.version}")
    logging.info(f"日志文件: {LOG_PATH}")
    logging.info(f"EXE: {sys.executable}")
    logging.info(f"Frozen: {getattr(sys, 'frozen', False)}")

STYLESHEET = """
QMainWindow {
    background-color: #ffffff;
}
QWidget {
    color: #1d1d1f;
    font-size: 13px;
}
QLabel {
    color: #1d1d1f;
    font-size: 13px;
}
QLabel#title {
    font-size: 20px;
    font-weight: 600;
    color: #1d1d1f;
    padding: 10px 0;
}
QLabel#section {
    font-size: 13px;
    font-weight: 600;
    color: #86868b;
    padding: 2px 0;
}
QLabel#hint {
    color: #86868b;
    font-size: 12px;
}
QPushButton {
    background-color: #f5f5f7;
    color: #1d1d1f;
    border: 1px solid #d2d2d7;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #e8e8ed;
}
QPushButton:pressed {
    background-color: #d2d2d7;
}
QPushButton#primary {
    background-color: #007aff;
    color: #ffffff;
    font-weight: 600;
    border: none;
    border-radius: 8px;
}
QPushButton#primary:hover {
    background-color: #0066d6;
}
QPushButton#primary:pressed {
    background-color: #0055b3;
}
QPushButton#primary:disabled {
    background-color: #b0b0b5;
    color: #ffffff;
}
QGroupBox {
    color: #1d1d1f;
    border: 1px solid #e8e8ed;
    border-radius: 12px;
    margin-top: 14px;
    padding-top: 14px;
    background-color: #fbfbfd;
    font-size: 13px;
    font-weight: 500;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 6px;
    color: #1d1d1f;
}
QSlider::groove:horizontal {
    height: 4px;
    background: #e8e8ed;
    border-radius: 2px;
}
QSlider::sub-page:horizontal {
    background: #007aff;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #ffffff;
    width: 18px;
    height: 18px;
    margin: -8px 0;
    border-radius: 9px;
    border: 2px solid #007aff;
}
QSlider::handle:horizontal:hover {
    border-color: #0066d6;
}
QProgressBar {
    border: none;
    border-radius: 4px;
    text-align: center;
    color: #1d1d1f;
    background-color: #e8e8ed;
    height: 6px;
    font-size: 11px;
}
QProgressBar::chunk {
    background-color: #007aff;
    border-radius: 3px;
}
QScrollArea {
    border: 1px solid #e8e8ed;
    border-radius: 12px;
    background-color: #fbfbfd;
}
QCheckBox {
    color: #1d1d1f;
    font-size: 13px;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #d2d2d7;
    border-radius: 5px;
    background-color: #ffffff;
}
QCheckBox::indicator:checked {
    background-color: #007aff;
    border-color: #007aff;
}
QSplitter::handle {
    background-color: #e8e8ed;
    width: 2px;
}
QFrame#leftPanel {
    background-color: #fbfbfd;
    border-right: 1px solid #e8e8ed;
}
QFrame#rightPanel {
    background-color: #ffffff;
}
QDialog {
    background-color: #ffffff;
}
QDialog QLabel {
    color: #1d1d1f;
}
QMessageBox {
    background-color: #ffffff;
}
QMessageBox QLabel {
    color: #1d1d1f;
}
QMessageBox QPushButton {
    min-width: 64px;
}
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    border: none;
}
QScrollBar::handle:vertical {
    background: #d2d2d7;
    min-height: 30px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #b0b0b5;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background: transparent;
    height: 8px;
    border: none;
}
QScrollBar::handle:horizontal {
    background: #d2d2d7;
    min-width: 30px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal:hover {
    background: #b0b0b5;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}
QToolTip {
    background-color: #1d1d1f;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 4px 8px;
}
"""


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
        logging.info(f"线程启动: {total} 张图片, 输出目录: {self.output_dir}")
        logging.info(f"参数: {self.params}")
        try:
            for i, path in enumerate(self.input_paths):
                if self._stop:
                    logging.info("用户取消处理")
                    break
                try:
                    logging.info(f"[{i+1}/{total}] 开始加载: {path}")
                    self.progress.emit(i, total, f"加载: {os.path.basename(path)}")
                    img = load_image_unicode(path)
                    if img is None:
                        msg = f"无法读取: {os.path.basename(path)}"
                        logging.error(msg)
                        self.errors.append(msg)
                        self.error_occurred.emit(msg)
                        self.progress.emit(i + 1, total, os.path.basename(path))
                        continue
                    logging.info(f"[{i+1}/{total}] 加载成功, 尺寸: {img.shape}")
                    self.progress.emit(i, total, f"处理: {os.path.basename(path)}")
                    result = make_clear(img, **self.params)
                    logging.info(f"[{i+1}/{total}] 处理完成")
                    out_name = make_copy_filename(os.path.basename(path))
                    out_path = os.path.normpath(os.path.join(self.output_dir, out_name))
                    logging.info(f"[{i+1}/{total}] 保存到: {out_path}")
                    self.progress.emit(i, total, f"保存: {out_name}")
                    save_image_unicode(result, out_path)
                    success_count += 1
                    logging.info(f"[{i+1}/{total}] 保存成功")
                    self.progress.emit(i + 1, total, out_name)
                except Exception as e:
                    tb = traceback.format_exc()
                    logging.error(f"[{i+1}/{total}] 异常: {e}\n{tb}")
                    msg = f"{os.path.basename(path)}: {e}"
                    self.errors.append(msg)
                    self.error_occurred.emit(msg)
                    self.progress.emit(i + 1, total, os.path.basename(path))
        except Exception as e:
            tb = traceback.format_exc()
            logging.error(f"线程异常: {e}\n{tb}")
            self.errors.append(f"线程异常: {e}")
            self.error_occurred.emit(f"线程异常: {e}")
        finally:
            logging.info(f"线程结束: 成功 {success_count}, 失败 {len(self.errors)}")
            self.finished_ok.emit(success_count, self.errors)


class PhotoClearApp(QMainWindow):
    PLACEHOLDER = "拖拽图片或文件夹到此处\n或点击左侧「选择图片」"

    def __init__(self):
        super().__init__()
        self.preview_image = None
        self.input_paths = []
        self.output_dir = ""
        self.thread = None
        self.init_ui()
        self.setAcceptDrops(True)

    def init_ui(self):
        self.setWindowTitle(f"照片通透工具 v{__version__}")
        self.setWindowIcon(QIcon(resource_path("icon.ico")))
        self.setMinimumSize(1000, 660)
        self.resize(1200, 760)

        central = QWidget()
        self.setCentralWidget(central)
        outer = QHBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        left = self._build_left_panel()
        outer.addWidget(left, 0)

        right = self._build_right_panel()
        outer.addWidget(right, 1)

    def _build_left_panel(self):
        panel = QFrame()
        panel.setObjectName("leftPanel")
        panel.setFixedWidth(320)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        title = QLabel("照片通透工具")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        layout.addWidget(self._build_input_group())
        layout.addWidget(self._build_output_group())
        layout.addWidget(self._build_param_group())

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        reset_btn = QPushButton("恢复默认")
        reset_btn.clicked.connect(self._reset_defaults)
        btn_row.addWidget(reset_btn)

        self.process_btn = QPushButton("开始处理")
        self.process_btn.setObjectName("primary")
        self.process_btn.clicked.connect(self._start_processing)
        btn_row.addWidget(self.process_btn)
        layout.addLayout(btn_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("就绪")
        self.status_label.setObjectName("hint")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        log_btn = QPushButton("查看日志")
        log_btn.clicked.connect(self._open_log)
        layout.addWidget(log_btn)

        layout.addStretch()
        return panel

    def _build_input_group(self):
        group = QGroupBox("输入")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        img_btn = QPushButton("选择图片")
        img_btn.clicked.connect(self._select_image)
        btn_row.addWidget(img_btn)

        folder_btn = QPushButton("选择文件夹")
        folder_btn.clicked.connect(self._select_folder)
        btn_row.addWidget(folder_btn)
        layout.addLayout(btn_row)

        self.input_label = QLabel("未选择")
        self.input_label.setObjectName("hint")
        self.input_label.setWordWrap(True)
        layout.addWidget(self.input_label)

        return group

    def _build_output_group(self):
        group = QGroupBox("输出")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)

        out_btn = QPushButton("选择输出目录")
        out_btn.clicked.connect(self._select_output)
        layout.addWidget(out_btn)

        self.output_label = QLabel("未选择")
        self.output_label.setObjectName("hint")
        self.output_label.setWordWrap(True)
        layout.addWidget(self.output_label)

        return group

    def _build_param_group(self):
        group = QGroupBox("参数调整")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)

        self.sliders = {}
        defaults = {
            "通透强度": (0, 100, 60),
            "去雾强度": (0, 100, 40),
            "清晰度": (0, 100, 30),
            "饱和度": (100, 200, 125),
            "亮度": (-50, 50, 10),
        }

        for name, (mn, mx, val) in defaults.items():
            row = QHBoxLayout()
            label = QLabel(name)
            label.setFixedWidth(70)
            row.addWidget(label)

            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(mn, mx)
            slider.setValue(val)
            slider.valueChanged.connect(self._on_slider_changed)
            row.addWidget(slider, 1)

            val_label = QLabel(str(val))
            val_label.setObjectName("hint")
            val_label.setFixedWidth(40)
            val_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            slider.valueChanged.connect(lambda v, l=val_label: l.setText(str(v)))
            row.addWidget(val_label)

            self.sliders[name] = (slider, val_label)
            layout.addLayout(row)

        self.compare_cb = QCheckBox("显示原图对比")
        self.compare_cb.setChecked(True)
        self.compare_cb.toggled.connect(self._toggle_compare)
        layout.addWidget(self.compare_cb)

        return group

    def _build_right_panel(self):
        panel = QFrame()
        panel.setObjectName("rightPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        header_row = QHBoxLayout()
        self.orig_header = QLabel("原图")
        self.orig_header.setObjectName("section")
        self.orig_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_row.addWidget(self.orig_header)

        result_header = QLabel("效果预览")
        result_header.setObjectName("section")
        result_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_row.addWidget(result_header)
        layout.addLayout(header_row)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        self.preview_original = QLabel(self.PLACEHOLDER)
        self.preview_original.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_original.setStyleSheet("font-size: 14px; color: #86868b;")
        self.preview_original.setMinimumSize(300, 400)

        scroll_orig = QScrollArea()
        scroll_orig.setWidgetResizable(True)
        scroll_orig.setWidget(self.preview_original)
        self.scroll_orig = scroll_orig
        self.splitter.addWidget(scroll_orig)

        self.preview_result = QLabel(self.PLACEHOLDER)
        self.preview_result.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_result.setStyleSheet("font-size: 14px; color: #86868b;")
        self.preview_result.setMinimumSize(300, 400)

        scroll_result = QScrollArea()
        scroll_result.setWidgetResizable(True)
        scroll_result.setWidget(self.preview_result)
        self.splitter.addWidget(scroll_result)

        self.splitter.setSizes([500, 500])
        layout.addWidget(self.splitter, 1)

        return panel

    def _select_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "",
            "图片文件 (*.jpg *.jpeg *.png *.bmp *.tiff *.tif *.webp)"
        )
        if not path:
            return
        self.input_paths = [path]
        self.input_label.setText(path)
        self.output_dir = os.path.dirname(path)
        self.output_label.setText(self.output_dir)
        self._load_preview(path)

    def _select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if not folder:
            return
        paths = []
        for f in os.listdir(folder):
            if os.path.splitext(f)[1].lower() in SUPPORTED_FORMATS:
                paths.append(os.path.join(folder, f))
        if not paths:
            QMessageBox.information(self, "提示", "该文件夹下没有支持的图片文件")
            return
        self.input_paths = sorted(paths)
        self.input_label.setText(f"{folder}\n（{len(paths)} 张图片）")
        self.output_dir = folder
        self.output_label.setText(folder)
        self._load_preview(self.input_paths[0])
        self.status_label.setText(f"已选择 {len(paths)} 张图片")

    def _select_output(self):
        folder = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if not folder:
            return
        self.output_dir = folder
        self.output_label.setText(folder)

    def _load_preview(self, path):
        img = load_image_unicode(path)
        if img is None:
            self.status_label.setText("无法读取该图片")
            return
        self.preview_image = img
        self._update_preview()

    def _update_preview(self):
        if self.preview_image is None:
            return
        img = self.preview_image
        compare = self.compare_cb.isChecked()
        if compare:
            max_w, max_h = 360, 500
        else:
            max_w, max_h = 760, 520
        h, w = img.shape[:2]
        scale = min(max_w / w, max_h / h, 1.0)
        if scale < 1.0:
            small = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
        else:
            small = img

        if compare:
            orig_pixmap = cv2_to_qpixmap(small)
            self.preview_original.setPixmap(orig_pixmap)

        params = self._get_params()
        processed = make_clear(small, **params)
        result_pixmap = cv2_to_qpixmap(processed)
        self.preview_result.setPixmap(result_pixmap)

    def _on_slider_changed(self):
        self._update_preview()

    def _toggle_compare(self, checked):
        self.scroll_orig.setVisible(checked)
        self.orig_header.setVisible(checked)
        self._update_preview()

    def _get_params(self):
        return {
            "intensity": self.sliders["通透强度"][0].value() / 100.0,
            "dehaze": self.sliders["去雾强度"][0].value() / 100.0,
            "clarity": self.sliders["清晰度"][0].value() / 100.0,
            "saturation": self.sliders["饱和度"][0].value() / 100.0,
            "brightness": self.sliders["亮度"][0].value() / 100.0,
        }

    def _reset_defaults(self):
        defaults = {"通透强度": 60, "去雾强度": 40, "清晰度": 30, "饱和度": 125, "亮度": 10}
        for name, val in defaults.items():
            self.sliders[name][0].setValue(val)
        self._update_preview()

    def _start_processing(self):
        if not self.input_paths:
            QMessageBox.warning(self, "提示", "请先选择图片或文件夹")
            return
        if not self.output_dir:
            QMessageBox.warning(self, "提示", "请先选择输出目录")
            return

        params = self._get_params()
        logging.info(f"开始处理: {len(self.input_paths)} 张图片")
        logging.info(f"输入: {self.input_paths[:3]}")
        logging.info(f"输出目录: {self.output_dir}")
        logging.info(f"参数: {params}")
        self._processing_done = False
        self.process_btn.setEnabled(False)
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
        self.status_label.setText(f"处理中 ({current}/{total}): {filename}")

    def _on_error(self, msg):
        self.status_label.setText(f"错误: {msg}")

    def _on_finished(self, count, errors):
        self._processing_done = True
        self.process_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        if errors:
            error_text = "\n".join(errors[:10])
            if len(errors) > 10:
                error_text += f"\n...还有 {len(errors) - 10} 个错误"
            self.status_label.setText(f"完成：成功 {count} 张，失败 {len(errors)} 张")
            QMessageBox.warning(self, "处理完成（有错误）",
                f"成功处理 {count} 张图片\n失败 {len(errors)} 张\n\n错误详情:\n{error_text}\n\n详细日志: {LOG_PATH}")
        else:
            self.status_label.setText(f"完成！共处理 {count} 张图片")
            QMessageBox.information(self, "完成",
                f"共处理 {count} 张图片\n输出目录: {self.output_dir}")

    def _on_thread_finished(self):
        if not getattr(self, '_processing_done', False):
            self.process_btn.setEnabled(True)
            self.progress_bar.setVisible(False)
            self.status_label.setText("处理异常终止")

    def _open_log(self):
        os.startfile(LOG_PATH)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if not urls:
            return
        path = urls[0].toLocalFile()
        if not path:
            return
        if os.path.isdir(path):
            paths = []
            for f in os.listdir(path):
                if os.path.splitext(f)[1].lower() in SUPPORTED_FORMATS:
                    paths.append(os.path.join(path, f))
            if not paths:
                QMessageBox.information(self, "提示", "该文件夹下没有支持的图片文件")
                return
            self.input_paths = sorted(paths)
            self.input_label.setText(f"{path}\n（{len(paths)} 张图片）")
            self.output_dir = path
            self.output_label.setText(path)
            self._load_preview(self.input_paths[0])
            self.status_label.setText(f"已选择 {len(paths)} 张图片")
        elif os.path.splitext(path)[1].lower() in SUPPORTED_FORMATS:
            self.input_paths = [path]
            self.input_label.setText(path)
            self.output_dir = os.path.dirname(path)
            self.output_label.setText(self.output_dir)
            self._load_preview(path)
        else:
            QMessageBox.information(self, "提示", "请拖入图片文件或文件夹")


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
