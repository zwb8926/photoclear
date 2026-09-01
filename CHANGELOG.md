# PhotoClear v0.0.2 更新日志

**发布日期**: 2026-09-01  
**版本号**: v0.0.2  
**协议**: AGPL-3.0 (从 CC BY-NC 4.0 迁移)

---

## 新功能

### 自适应智能分析

新增 `auto_params()` 函数，自动分析图片并推荐最佳参数：

| 分析维度 | 计算方式 | 影响参数 |
|---------|---------|---------|
| 平均亮度 | LAB 色彩空间 L 通道均值 | brightness（暗图自动提亮） |
| 对比度 | L 通道标准差 | dehaze（低对比自动去雾） |
| 动态范围 | 灰度直方图 5%~95% 分位差 | dehaze（窄范围加强去雾） |
| 饱和度 | HSV 色彩空间 S 通道均值 | saturation（低饱和自动增色） |
| 清晰度 | Laplacian 算子方差 | clarity（模糊图适度增强） |
| 整体调整量 | 各参数加权求和 | intensity（调整幅度决定强度） |

选择"自动"预设后，每次加载新图片会重新分析并更新参数，状态栏实时显示分析结果。

### 预设扩展（4 → 10 个）

参考 Adobe Lightroom 专业预设的参数范围，新增 6 个场景预设：

| 预设 | 适用场景 | 参数特点 |
|------|---------|---------|
| 自动 | 通用 | AI 自适应分析 |
| 自然通透 | 日常照片 | 轻度调整，保持原片风格 |
| 清新明亮 | 风景/旅行 | 提亮+增饱和，清新感 |
| 浓郁鲜艳 | 美食/花卉 | 强饱和，色彩浓郁 |
| 强力去雾 | 雾天/逆光 | 强去雾，恢复细节 |
| 人像美肤 | 人物照片 | 低清晰度避免皮肤瑕疵放大 |
| 风景锐利 | 风景/建筑 | 高清晰度，边缘锐利 |
| 阴天提亮 | 阴天/暗光 | 强提亮+去雾 |
| 夜景降噪 | 夜晚拍摄 | 适度去雾+提亮，保护暗部 |
| 电影质感 | 艺术创作 | 低饱和低亮度，电影调色风格 |

### 预览图放大查看

点击任意预览图弹出全屏查看窗口：

- 默认适应窗口，完整查看全图
- 滚轮缩放（5% ~ 800%）
- 按住左键拖动平移图片
- 工具栏：放大/缩小/适应窗口/原始大小

### Toast 通知

处理完成后不再弹出模态对话框，改为顶部滑入式 Toast 通知（深色卡片 + 绿色勾 + 3 秒自动消失），不打断操作流程。

### 拖拽高亮

拖拽图片到窗口时，预览区显示蓝色虚线边框 + "松开以加载图片"提示，松开后自动加载。

### 菜单栏

新增「文件」和「帮助」菜单：

- 文件：打开图片 (Ctrl+O)、打开文件夹 (Ctrl+Shift+O)、开始处理 (Ctrl+Enter)
- 帮助：关于 PhotoClear、查看日志、GitHub 项目

### 键盘快捷键

| 快捷键 | 功能 |
|--------|------|
| Ctrl+O | 打开图片 |
| Ctrl+Shift+O | 打开文件夹 |
| Ctrl+Enter | 开始处理 |
| ESC | 关闭放大窗口 |

### 关于对话框

菜单 → 帮助 → 关于 PhotoClear，显示版本号、作者、开源协议、GitHub 地址。

### 使用情况追踪

新增 `usage_tracker.py` 模块，匿名记录使用数据：

- 安装 ID（随机 UUID，匿名）
- 启动次数
- 累计处理图片数
- 批次处理次数
- 首次/最近启动时间

数据本地存储在 `%LOCALAPPDATA%\PhotoClear\usage.json`，支持配置远程追踪 URL。

---

## 改进

### 算法参数优化

参考 Lightroom 专业调色范围 [$TRAE_REF](https://presetpedia.com/lightroom-preset-settings/) [$TRAE_REF](https://theeditingstudio.co/blog/how-to-stop-overediting-your-photos) 调整所有预设的参数值：

| 参数 | 旧范围 | 新范围 | 参考 |
|------|--------|--------|------|
| clarity (清晰度) | 0.1 ~ 0.4 | 0.08 ~ 0.32 | Lightroom Clarity +6~+18 |
| saturation (饱和度) | 1.0 ~ 1.5 | 1.05 ~ 1.35 | Lightroom Vibrance +10~+25 |
| dehaze (去雾) | 0.2 ~ 0.6 | 0.22 ~ 0.55 | Lightroom Dehaze +3~+10 |
| brightness (亮度) | 0.0 ~ 0.2 | 0.04 ~ 0.18 | Lightroom Exposure ±0.1~0.2 |

### 界面视觉打磨

- 窗口启动自动居中屏幕
- 标题栏：24px 图标 + "PhotoClear" + 版本号
- 预设栏背景层次：#ffffff → #fafafa
- 预设按钮：圆角 18→16，padding 收紧
- 滑块手柄：16px→14px
- 预览卡片阴影更轻柔（blur 30→24）
- 空状态：半透明图标 + 格式说明
- 滚动条样式统一极简

### 代码重构

- `_build_preview` 修复 QStackedLayout 布局冲突
- `save_image_unicode` 改用 `open(path, 'wb')` 替代 `buf.tofile()`
- ProcessingThread 加 `try/finally` 确保 finished_ok 信号一定发出
- 新增 `_updating_from_preset` 标志位，预设选中状态不再被滑块联动覆盖

---

## 开源协议变更

| | v0.0.1 | v0.0.2 |
|---|---|---|
| 协议 | CC BY-NC 4.0 | **AGPL-3.0** |
| 商业使用 | 禁止 | 允许 |
| 修改分发 | 允许 | 允许 |
| 衍生作品 | 相同协议 | 必须用 AGPL-3.0 |
| 网络服务 | 不涉及 | 必须提供源代码 |

---

## 下载

- **Windows**: [PhotoClear.exe](https://github.com/zwb8926/photoclear/releases/tag/v0.0.2) (54.4 MB，Nuitka 编译，无需安装 Python)
- **源码**: https://github.com/zwb8926/photoclear/tree/v0.0.2

## 运行要求

- Windows 10/11（exe 版本无其他依赖）
- 或 Python 3.9+ + PyQt6 + OpenCV（源码运行）
