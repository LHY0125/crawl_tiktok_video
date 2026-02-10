import os
import time
import concurrent.futures
from datetime import datetime
from DrissionPage import ChromiumPage, ChromiumOptions
from src.downloader import download_file


def run_douyin_task(
    target_url,
    target_count,
    save_root,
    browser_path,
    log_callback,
    finish_callback,
):
    """
    [Control Layer] 抖音核心业务流程
    1. 启动浏览器
    2. 监听数据包获取作品列表
    3. 调度线程池并行下载
    """
    dp = None
    try:
        log_callback(f"正在启动 Edge 浏览器 ({browser_path})...")

        co = ChromiumOptions()
        co.set_paths(browser_path=browser_path)

        # 尝试启动浏览器
        dp = ChromiumPage(addr_or_opts=co)

        # 开始监听
        dp.listen.start("aweme/v1/web/aweme/post")

        log_callback(f"正在访问: {target_url}")
        dp.get(target_url)

        collected_works = []
        log_callback("正在扫描作品列表 (请不要关闭弹出的浏览器)...")

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
                except Exception:
                    pass

            log_callback(f"已获取作品信息: {len(collected_works)}/{target_count}")

            if len(collected_works) >= target_count:
                break

            if not found_new:
                no_new_data_count += 1
                time.sleep(1)
            else:
                no_new_data_count = 0

            if no_new_data_count > 8:
                log_callback("未检测到新数据，可能已到底部。")
                break

        log_callback(f"扫描完成，共获取 {len(collected_works)} 个作品。")
        dp.close()  # 关闭浏览器
        dp = None  # 置空，避免 finally 重复关闭

        # 处理数据
        works_to_process = collected_works[:target_count]
        # 按时间正序
        works_to_process.sort(key=lambda x: x["create_time"])

        log_callback("开始下载 (多线程并行)...")
        date_counter = {}

        # 准备下载任务列表
        download_tasks = []

        for index, work in enumerate(works_to_process):
            ts = work["create_time"]
            date_str = datetime.fromtimestamp(ts).strftime("%Y_%m_%d")

            if date_str not in date_counter:
                date_counter[date_str] = 1
                file_name_base = date_str
            else:
                date_counter[date_str] += 1
                count_idx = date_counter[date_str]
                file_name_base = f"{date_str}({count_idx})"

            download_tasks.append(
                {
                    "work": work,
                    "index": index,
                    "file_name_base": file_name_base,
                }
            )

        # 使用线程池执行下载
        # max_workers=5 表示同时下载5个
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for task in download_tasks:
                futures.append(
                    executor.submit(
                        process_douyin_work,
                        task["work"],
                        task["index"],
                        len(works_to_process),
                        save_root,
                        task["file_name_base"],
                        log_callback,
                    )
                )

            # 等待所有任务完成
            concurrent.futures.wait(futures)

        log_callback("=" * 30)
        log_callback("全部任务结束！")

        if finish_callback:
            finish_callback("完成", "全部下载任务已结束！")

    except Exception as e:
        log_callback(f"发生严重错误: {e}")
        if dp:
            try:
                dp.close()
            except Exception:
                pass
    finally:
        pass


def process_douyin_work(
    work, index, total_count, save_root, file_name_base, log_callback
):
    """
    [Data Layer] 单个任务处理逻辑 (Worker)
    判断作品类型(视频/图文)，生成路径并调用下载器
    """
    try:
        is_video = True
        if "images" in work and work["images"]:
            is_video = False

        msg = (
            f"[{index + 1}/{total_count}] {file_name_base} | "
            f"{'视频' if is_video else '图文'} | 下载中..."
        )
        log_callback(msg)

        if is_video:
            video_url = work["video"]["play_addr"]["url_list"][0]
            file_path = os.path.join(save_root, f"{file_name_base}.mp4")
            if not os.path.exists(file_path):
                if download_file(video_url, file_path, log_callback=log_callback):
                    log_callback(
                        f"[{index + 1}/{total_count}] {file_name_base} " "-> 下载完成"
                    )
                else:
                    log_callback(
                        f"[{index + 1}/{total_count}] {file_name_base} -> 下载失败"
                    )
            else:
                log_callback(
                    f"[{index + 1}/{total_count}] {file_name_base} "
                    "-> 文件已存在，跳过"
                )
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
                    download_file(img_url, img_path, log_callback=log_callback)
            log_callback(
                f"[{index + 1}/{total_count}] {file_name_base} -> 图文下载完成"
            )

    except Exception as e:
        log_callback(f"[{index + 1}/{total_count}] {file_name_base} -> 处理出错: {e}")
