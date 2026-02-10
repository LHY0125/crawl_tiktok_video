import tkinter as tk
from src.ui.app import DouyinDownloaderApp

# 运行脚本 (使用 my_env 环境):
# D:\ProgramData\anaconda3\envs\my_env\python.exe video_downloader.py
#
# 打包成 exe (使用 my_env 环境):
# D:\ProgramData\anaconda3\envs\my_env\python.exe -m nuitka --standalone ^
# --mingw64 --show-memory --show-progress --output-dir=build_nuitka ^
# --enable-plugin=tk-inter --include-data-dir=ico=ico ^
# --windows-icon-from-ico=ico\video_downloader.ico --main=video_downloader.py

# 主函数入口
if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = DouyinDownloaderApp(root)
        root.mainloop()
    except Exception:
        import traceback

        with open("error_log.txt", "w") as f:
            f.write(traceback.format_exc())
