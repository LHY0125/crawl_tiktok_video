import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import threading
import os
from src.utils import find_edge_path
from src.tasks.bilibili import run_bilibili_task
from src.tasks.douyin import run_douyin_task


class DouyinDownloaderApp:
    def __init__(self, root):
        """
        [UI Layer] 初始化界面
        负责创建主窗口、设置图标、初始化变量和加载布局
        """
        self.root = root
        self.root.title("抖音/B站批量下载工具 (GUI版)")
        self.root.geometry("600x650")

        # 设置窗口图标
        try:
            # 尝试多种路径查找图标，兼容源码运行和打包后的情况
            # 注意：这里的路径逻辑可能需要根据新的目录结构微调，
            # 但如果从根目录运行，os.path.dirname(__file__) 将是 src/ui
            # 所以我们需要往上找两层，或者依赖入口文件传进来的路径
            # 为了兼容性，我们假设入口文件在根目录，ico文件夹也在根目录
            base_dir = os.getcwd()
            # 或者使用相对路径尝试
            icon_candidates = [
                os.path.join(base_dir, "ico", "video_downloader.ico"),
                os.path.join(base_dir, "video_downloader.ico"),
                # 如果是从 src/ui/app.py 视角
                os.path.abspath(
                    os.path.join(
                        os.path.dirname(__file__),
                        "..",
                        "..",
                        "ico",
                        "video_downloader.ico",
                    )
                ),
            ]
            for icon_path in icon_candidates:
                if os.path.exists(icon_path):
                    self.root.iconbitmap(icon_path)
                    break
        except Exception:
            pass

        # 界面布局变量
        self.url_var = tk.StringVar()
        self.count_var = tk.StringVar(value="10")
        self.save_path_var = tk.StringVar()

        # 浏览器路径初始化
        default_browser = find_edge_path()
        if not default_browser:
            default_browser = (
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
            )
        self.browser_path_var = tk.StringVar(value=default_browser)

        # 平台选择变量
        self.platform_var = tk.StringVar(value="douyin")

        self.is_running = False

        self.create_widgets()

    def create_widgets(self):
        """
        [UI Layer] 构建界面组件
        使用 Pack 布局管理器按顺序排列各个输入框和按钮
        """
        # 1. 主页链接
        tk.Label(self.root, text="1. 作者主页链接:").pack(
            anchor="w", padx=10, pady=(10, 0)
        )
        entry_url = tk.Entry(self.root, textvariable=self.url_var, width=60)
        entry_url.pack(padx=10, pady=5, fill="x")

        # 2. 爬取数量
        tk.Label(self.root, text="2. 爬取视频个数:").pack(
            anchor="w", padx=10, pady=(10, 0)
        )
        entry_count = tk.Entry(self.root, textvariable=self.count_var, width=60)
        entry_count.pack(padx=10, pady=5, fill="x")

        # 3. 保存路径
        tk.Label(self.root, text="3. 保存路径:").pack(anchor="w", padx=10, pady=(10, 0))
        frame_path = tk.Frame(self.root)
        frame_path.pack(padx=10, pady=5, fill="x")

        # === 修正点：readOnly=True 改为 state='readonly' ===
        entry_path = tk.Entry(
            frame_path, textvariable=self.save_path_var, state="readonly"
        )
        entry_path.pack(side="left", fill="x", expand=True)

        btn_browse = tk.Button(
            frame_path, text="选择文件夹", command=self.select_folder
        )
        btn_browse.pack(side="right", padx=(5, 0))

        # 4. 浏览器路径
        tk.Label(self.root, text="4. 浏览器路径 (Edge):").pack(
            anchor="w", padx=10, pady=(10, 0)
        )
        frame_browser = tk.Frame(self.root)
        frame_browser.pack(padx=10, pady=5, fill="x")

        entry_browser = tk.Entry(frame_browser, textvariable=self.browser_path_var)
        entry_browser.pack(side="left", fill="x", expand=True)

        btn_browse_browser = tk.Button(
            frame_browser, text="选择文件", command=self.select_browser
        )
        btn_browse_browser.pack(side="right", padx=(5, 0))

        # 5. 平台选择
        tk.Label(self.root, text="5. 下载平台:").pack(anchor="w", padx=10, pady=(10, 0))
        frame_platform = tk.Frame(self.root)
        frame_platform.pack(padx=10, pady=5, fill="x")

        rb_douyin = tk.Radiobutton(
            frame_platform, text="抖音", variable=self.platform_var, value="douyin"
        )
        rb_douyin.pack(side="left", padx=10)

        rb_bilibili = tk.Radiobutton(
            frame_platform, text="B站", variable=self.platform_var, value="bilibili"
        )
        rb_bilibili.pack(side="left", padx=10)

        # 6. 开始按钮
        self.btn_start = tk.Button(
            self.root,
            text="开始下载",
            command=self.start_thread,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 12, "bold"),
        )
        self.btn_start.pack(pady=15, fill="x", padx=50)

        # 6. 日志输出窗口
        tk.Label(self.root, text="运行日志:").pack(anchor="w", padx=10)
        self.log_text = scrolledtext.ScrolledText(
            self.root, height=15, state="disabled"
        )
        self.log_text.pack(padx=10, pady=5, fill="both", expand=True)

    def log(self, message):
        """
        [UI Layer] 线程安全的日志输出
        子线程不能直接更新UI，必须通过 root.after 调度到主线程执行
        """
        self.root.after(0, self._log_impl, message)

    def _log_impl(self, message):
        """实际执行日志写入的方法"""
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)  # 滚动到底部
        self.log_text.config(state="disabled")

    def select_folder(self):
        """选择文件夹对话框"""
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.save_path_var.set(folder_selected)

    def select_browser(self):
        """选择浏览器文件对话框"""
        file_selected = filedialog.askopenfilename(
            title="选择 Edge 浏览器可执行文件",
            filetypes=[("Executable Files", "*.exe"), ("All Files", "*.*")],
        )
        if file_selected:
            self.browser_path_var.set(file_selected)

    def start_thread(self):
        """
        [Control Layer] 线程调度
        校验参数并开启独立线程运行核心任务，防止界面卡死
        """
        if self.is_running:
            messagebox.showwarning("提示", "任务正在进行中，请稍候...")
            return

        # 验证输入
        url = self.url_var.get().strip()
        count_str = self.count_var.get().strip()
        save_path = self.save_path_var.get().strip()
        browser_path = self.browser_path_var.get().strip()
        platform = self.platform_var.get()

        if not url:
            messagebox.showerror("错误", "请输入主页链接")
            return
        if not count_str.isdigit() or int(count_str) <= 0:
            messagebox.showerror("错误", "请输入正确的数量")
            return
        if not save_path:
            messagebox.showerror("错误", "请选择保存路径")
            return

        # 检查浏览器路径是否存在
        if not browser_path or not os.path.exists(browser_path):
            messagebox.showerror(
                "错误",
                f"指定的浏览器路径不存在：\n{browser_path}\n请手动选择正确的 msedge.exe 路径。",
            )
            return

        self.is_running = True
        self.btn_start.config(state="disabled", text="正在运行...")
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)  # 清空日志
        self.log_text.config(state="disabled")

        # 开启线程
        thread = threading.Thread(
            target=self.run_task,
            args=(url, int(count_str), save_path, browser_path, platform),
        )
        thread.daemon = True
        thread.start()

    def run_task(self, target_url, target_count, save_root, browser_path, platform):
        """
        [Control Layer] 任务分发
        """
        try:
            if platform == "bilibili":
                run_bilibili_task(
                    target_url,
                    target_count,
                    save_root,
                    browser_path,
                    log_callback=self.log,
                    finish_callback=self.finish_task,
                )
            else:
                run_douyin_task(
                    target_url,
                    target_count,
                    save_root,
                    browser_path,
                    log_callback=self.log,
                    finish_callback=self.finish_task,
                )
        finally:
            self.is_running = False
            self.root.after(
                0, lambda: self.btn_start.config(state="normal", text="开始下载")
            )

    def finish_task(self, title, message):
        self.root.after(0, lambda: messagebox.showinfo(title, message))