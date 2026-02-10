# 抖音/B站批量下载工具 (Video Downloader)

这是一个基于 Python 的抖音/B站视频批量下载工具，采用模块化设计，提供图形用户界面 (GUI)。它利用 `DrissionPage` 自动化控制 Edge 浏览器获取数据，支持多线程并发下载视频和图文内容。

> **项目介绍视频**：[点击观看](https://www.douyin.com/user/self?modal_id=7602291788182721777&showTab=record)

## ✨ 功能特点

- **多平台支持**：支持 **抖音** 和 **B站 (Bilibili)** 视频/图文下载。
- **图形化界面**：基于 Tkinter 的简洁 GUI，操作直观。
- **批量处理**：支持指定数量批量爬取。
- **自动归档**：按发布日期 `YYYY_MM_DD` 自动命名文件，同一天发布的作品自动添加序号。
- **高性能**：多线程并发下载，大幅提升速度。
- **智能配置**：自动检测 Edge 浏览器路径，支持手动指定。
- **标准安装包**：支持生成标准的 Windows 安装程序 (Inno Setup)。

## 📂 项目结构

项目已进行重构，采用模块化架构，源码位于 `src` 目录下：

```text
Video Downloader/
├── video_downloader.py    # 程序入口 (Entry Point)
├── src/
│   ├── ui/                # 界面模块 (App类, 负责GUI逻辑)
│   ├── tasks/             # 平台任务模块 (包含Bilibili和Douyin的具体爬虫逻辑)
│   ├── downloader.py      # 通用下载器 (封装Requests, 支持流式下载和重试)
│   └── utils.py           # 工具函数 (如Edge路径查找)
├── ico/                   # 图标资源文件夹
├── setup_nuitka.iss       # Inno Setup 打包脚本
└── README.md              # 项目说明文档
```

## 🚀 快速开始

### 方式一：直接运行源码

**环境要求**：
- Windows 10/11
- Python 3.8+
- Microsoft Edge 浏览器 (必需)

**安装依赖**：
```bash
pip install requests DrissionPage
```

**运行程序**：
```bash
python video_downloader.py
```

### 方式二：使用安装包

如果你是普通用户，可以直接运行 `Output` 目录下的安装程序（如果已打包），或者联系开发者获取。

## 📦 打包指南 (开发者)

本项目采用 **Nuitka** 编译核心程序，并结合 **Inno Setup** 制作最终的 Windows 安装包。

### 1. Nuitka 编译

使用以下命令将 Python 脚本编译为独立的可执行文件（文件夹模式）：

```bash
# 确保使用正确的 Python 环境 (如 Anaconda env)
# 注意替换 --windows-icon-from-ico 的路径为你实际的图标路径
python -m nuitka --standalone --mingw64 --show-progress --show-memory --enable-plugin=tk-inter --output-dir=build_nuitka --windows-disable-console --windows-icon-from-ico="ico\video_downloader.ico" video_downloader.py
```

### 2. 依赖补全 (关键步骤)

Nuitka 自动分析有时可能遗漏部分 DLL，导致程序无法运行或报错 `ImportError` / `ctypes` 错误。
**编译完成后，请务必手动检查并复制以下文件到 `build_nuitka/video_downloader.dist` 目录：**

1. **Tcl/Tk 库**：`tcl86t.dll`, `tk86t.dll`
2. **基础依赖库**：`Library/bin` 目录下的所有 DLL 文件 (如 `zlib.dll`, `libcrypto-*.dll`, `sqlite3.dll` 等)

### 3. Inno Setup 制作安装包

1. 下载并安装 **Inno Setup 6**。
2. 打开项目根目录下的 `setup_nuitka.iss` 文件。
3. 检查脚本中的路径配置是否正确（如 `Source` 路径指向你的 `build_nuitka\video_downloader.dist`）。
4. 点击工具栏的 **Compile** 按钮。
5. 编译成功后，生成的安装包将位于 `Output` 文件夹中。

## 🛠️ 架构说明

- **UI 层 (`src/ui`)**：使用 `tkinter` 构建，负责接收用户输入、显示日志和进度。采用 `root.after` 机制确保线程安全地更新 UI。
- **控制层 (`src/tasks`)**：
  - `bilibili.py` / `douyin.py`：封装了针对特定平台的业务逻辑。
  - 使用 `DrissionPage` 监听浏览器网络流量，解析视频/音频地址。
  - 使用 `concurrent.futures.ThreadPoolExecutor` 管理下载线程池。
- **数据层 (`src/downloader.py`)**：纯粹的下载执行器，封装了 `requests`，支持 Referer 防盗链处理、流式写入和错误重试。

## ⚠️ 注意事项

- **浏览器窗口**：程序运行时会启动 Edge 浏览器窗口进行数据采集，**请勿手动关闭该窗口**，否则任务会中断。
- **网络环境**：爬取过程中请保持网络畅通。
- **合规性**：本工具仅供学习交流使用，请勿用于非法用途。请尊重版权，不要传播未授权的内容。
