# 照片通透工具 (PhotoClear)

一键让照片更通透、更清晰。基于 OpenCV 的智能图像增强，去雾、提亮、锐化、加饱和度，自动输出通透感十足的照片。

## 功能特点

- **去雾增强** — CLAHE 自适应对比度，去除灰雾感
- **清晰度提升** — Unsharp Mask 细节锐化
- **饱和度增强** — 色彩更鲜艳
- **亮度调节** — Gamma 校正提亮
- **S 曲线对比度** — 增加画面层次
- **批量处理** — 选择文件夹自动处理所有图片
- **实时预览** — 拖动滑块即时查看效果，原图对比
- **拖拽支持** — 直接拖拽图片或文件夹到窗口
- **单文件运行** — 无需安装 Python 或任何依赖

## 下载使用

1. 前往 [Releases](https://github.com/zwb8926/photoclear/releases) 下载 `PhotoClear.exe`
2. 双击运行即可，无需安装

### 支持的图片格式

JPG / JPEG / PNG / BMP / TIFF / WEBP

### 可调参数

| 参数 | 范围 | 默认值 | 说明 |
|------|------|--------|------|
| 通透强度 | 0-100 | 60 | 整体效果混合比例 |
| 去雾强度 | 0-100 | 40 | CLAHE 自适应对比度去灰雾 |
| 清晰度 | 0-100 | 30 | Unsharp Mask 细节锐化 |
| 饱和度 | 100-200 | 125 | 色彩鲜艳度倍数 |
| 亮度 | -50~50 | 10 | Gamma 校正提亮/压暗 |

## 开发环境

- Python 3.9+
- OpenCV (opencv-python)
- NumPy
- PyQt6
- Nuitka (编译打包)

## 从源码构建

```bash
# 安装依赖
pip install opencv-python numpy PyQt6 Nuitka

# 直接运行
python main.py

# Nuitka 编译为单文件 exe
python -m nuitka --onefile --windows-console-mode=disable \
  --enable-plugin=pyqt6 --windows-icon-from-ico=icon.ico \
  --include-data-file="icon.ico=icon.ico" \
  --output-filename=PhotoClear.exe --output-dir=dist \
  --remove-output --assume-yes-for-download main.py
```

## 开源协议

本项目采用 [AGPL-3.0](./LICENSE) (GNU Affero General Public License v3.0) 协议。

- 允许商业使用、修改和分发
- 衍生作品必须以 AGPL-3.0 协议开源
- 网络服务使用也必须提供源代码
- 必须保留原作者版权声明 (zwb8926)

## 作者

- GitHub: [github.com/zwb8926/photoclear](https://github.com/zwb8926/photoclear)

## 隐私说明

本软件会匿名收集使用统计数据（启动次数、处理图片数量），不收集任何个人信息或图片内容。统计数据仅用于了解软件使用情况，不会上传图片或任何用户数据。
