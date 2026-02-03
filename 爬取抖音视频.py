import os
import time
import requests
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from datetime import datetime
from DrissionPage import ChromiumPage, ChromiumOptions

# python "D:\Code\doing_exercises\programs\crawl_tiktok_video\爬取抖音视频.py"

# ================= 配置区域 =================
# 这里写死了 Edge 的路径
DEFAULT_BROWSER_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"


# ===========================================


class DouyinDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("抖音批量下载工具 (GUI版)")
        self.root.geometry("600x550")

        # 界面布局变量
        self.url_var = tk.StringVar()
        self.count_var = tk.StringVar(value="10")
        self.save_path_var = tk.StringVar()
        self.is_running = False

        self.create_widgets()

    def create_widgets(self):
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

        # 4. 开始按钮
        self.btn_start = tk.Button(
            self.root,
            text="开始下载",
            command=self.start_thread,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 12, "bold"),
        )
        self.btn_start.pack(pady=15, fill="x", padx=50)

        # 5. 日志输出窗口
        tk.Label(self.root, text="运行日志:").pack(anchor="w", padx=10)
        self.log_text = scrolledtext.ScrolledText(
            self.root, height=15, state="disabled"
        )
        self.log_text.pack(padx=10, pady=5, fill="both", expand=True)

    def log(self, message):
        """向日志窗口输出信息"""
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)  # 滚动到底部
        self.log_text.config(state="disabled")

    def select_folder(self):
        """选择文件夹对话框"""
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.save_path_var.set(folder_selected)

    def start_thread(self):
        """在独立线程中运行，防止界面卡死"""
        if self.is_running:
            messagebox.showwarning("提示", "任务正在进行中，请稍候...")
            return

        # 验证输入
        url = self.url_var.get().strip()
        count_str = self.count_var.get().strip()
        save_path = self.save_path_var.get().strip()

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
        if not os.path.exists(DEFAULT_BROWSER_PATH):
            messagebox.showerror(
                "错误",
                f"未找到浏览器文件：\n{DEFAULT_BROWSER_PATH}\n\n请确认已安装Edge或修改代码中的路径配置。",
            )
            return

        self.is_running = True
        self.btn_start.config(state="disabled", text="正在运行...")
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)  # 清空日志
        self.log_text.config(state="disabled")

        # 开启线程
        thread = threading.Thread(
            target=self.run_task, args=(url, int(count_str), save_path)
        )
        thread.daemon = True
        thread.start()

    def download_file(self, url, filepath):
        """下载文件逻辑"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://www.douyin.com/",
            }
            for _ in range(3):
                try:
                    response = requests.get(
                        url, headers=headers, stream=True, timeout=20
                    )
                    if response.status_code == 200:
                        with open(filepath, "wb") as f:
                            for chunk in response.iter_content(chunk_size=1024 * 1024):
                                f.write(chunk)
                        return True
                    break
                except requests.exceptions.RequestException:
                    time.sleep(1)
                    continue
            return False
        except Exception as e:
            self.log(f"下载出错: {e}")
            return False

    def run_task(self, target_url, target_count, save_root):
        """核心业务逻辑"""
        dp = None
        try:
            self.log(f"正在启动 Edge 浏览器 ({DEFAULT_BROWSER_PATH})...")

            co = ChromiumOptions()
            co.set_paths(browser_path=DEFAULT_BROWSER_PATH)

            # 尝试启动浏览器
            dp = ChromiumPage(addr_or_opts=co)

            # 开始监听
            dp.listen.start("aweme/v1/web/aweme/post")

            self.log(f"正在访问: {target_url}")
            dp.get(target_url)

            collected_works = []
            self.log("正在扫描作品列表 (请不要关闭弹出的浏览器)...")

            no_new_data_count = 0

            while len(collected_works) < target_count:
                dp.scroll.to_bottom()

                # 等待数据包
                res = dp.listen.wait(timeout=2)

                found_new = False
                if res:
                    try:
                        data = res.response.body
                        if data and "aweme_list" in data:
                            aweme_list = data["aweme_list"]
                            if aweme_list:
                                for aweme in aweme_list:
                                    if not any(
                                        w["aweme_id"] == aweme["aweme_id"]
                                        for w in collected_works
                                    ):
                                        collected_works.append(aweme)
                                        found_new = True
                    except:
                        pass

                self.log(f"已获取作品信息: {len(collected_works)}/{target_count}")

                if len(collected_works) >= target_count:
                    break

                if not found_new:
                    no_new_data_count += 1
                    time.sleep(1)
                else:
                    no_new_data_count = 0

                if no_new_data_count > 8:
                    self.log("未检测到新数据，可能已到底部。")
                    break

            self.log(f"扫描完成，共获取 {len(collected_works)} 个作品。")
            dp.close()  # 关闭浏览器

            # 处理数据
            works_to_process = collected_works[:target_count]
            # 按时间正序
            works_to_process.sort(key=lambda x: x["create_time"])

            self.log("开始下载...")
            date_counter = {}

            for index, work in enumerate(works_to_process):
                try:
                    ts = work["create_time"]
                    date_str = datetime.fromtimestamp(ts).strftime("%Y_%m_%d")

                    if date_str not in date_counter:
                        date_counter[date_str] = 1
                        file_name_base = date_str
                    else:
                        date_counter[date_str] += 1
                        count_idx = date_counter[date_str]
                        file_name_base = f"{date_str}({count_idx})"

                    is_video = True
                    if "images" in work and work["images"]:
                        is_video = False

                    self.log(
                        f"[{index + 1}/{len(works_to_process)}] {file_name_base} | {'视频' if is_video else '图文'}"
                    )

                    if is_video:
                        video_url = work["video"]["play_addr"]["url_list"][0]
                        file_path = os.path.join(save_root, f"{file_name_base}.mp4")
                        if not os.path.exists(file_path):
                            self.download_file(video_url, file_path)
                        else:
                            self.log("  -> 文件已存在，跳过")
                    else:
                        img_folder = os.path.join(save_root, file_name_base)
                        if not os.path.exists(img_folder):
                            os.makedirs(img_folder)

                        images = work["images"]
                        for idx, img_obj in enumerate(images):
                            img_url = img_obj["url_list"][0]
                            img_name = f"{idx + 1}.png"
                            img_path = os.path.join(img_folder, img_name)
                            if not os.path.exists(img_path):
                                self.download_file(img_url, img_path)
                        self.log("  -> 图文下载完成")

                except Exception as e:
                    self.log(f"  -> 处理出错: {e}")
                    continue

            self.log("=" * 30)
            self.log("全部任务结束！")
            messagebox.showinfo("完成", "全部下载任务已结束！")

        except Exception as e:
            self.log(f"发生严重错误: {e}")
            if dp:
                try:
                    dp.close()
                except:
                    pass
        finally:
            self.is_running = False
            self.btn_start.config(state="normal", text="开始下载")


if __name__ == "__main__":
    root = tk.Tk()
    app = DouyinDownloaderApp(root)
    root.mainloop()
