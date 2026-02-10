import os
import time
import re
import json
import requests
import concurrent.futures
from datetime import datetime
from DrissionPage import ChromiumPage, ChromiumOptions
from src.downloader import download_file


def run_bilibili_task(
    target_url,
    target_count,
    save_root,
    browser_path,
    log_callback,
    finish_callback=None,
):
    """
    [Control Layer] B站核心业务流程
    1. 启动浏览器
    2. 监听数据包获取作品列表
    3. 调度线程池并行下载
    """
    dp = None
    try:
        log_callback(f"正在启动 Edge 浏览器 ({browser_path})...")
        co = ChromiumOptions()
        co.set_paths(browser_path=browser_path)
        dp = ChromiumPage(addr_or_opts=co)

        # 监听 B站 用户视频列表接口
        dp.listen.start("space/wbi/arc/search")

        log_callback(f"正在访问: {target_url}")
        dp.get(target_url)

        # 尝试自动跳转到 /video 页面
        if "space.bilibili.com" in target_url and "/video" not in dp.url:
            video_url = target_url.rstrip("/") + "/video"
            log_callback(f"尝试跳转到视频页: {video_url}")
            dp.get(video_url)

        collected_works = []
        log_callback("正在扫描作品列表 (请不要关闭弹出的浏览器)...")

        no_new_data_count = 0

        while len(collected_works) < target_count:
            dp.scroll.to_bottom()

            res = dp.listen.wait(timeout=2)
            found_new = False

            if res:
                try:
                    data = res.response.body
                    # 解析 B站 响应: data['data']['list']['vlist']
                    if (
                        data
                        and isinstance(data, dict)
                        and "data" in data
                        and "list" in data["data"]
                    ):
                        vlist = data["data"]["list"]["vlist"]
                        if vlist:
                            for video in vlist:
                                if not any(
                                    w["bvid"] == video["bvid"] for w in collected_works
                                ):
                                    collected_works.append(video)
                                    found_new = True
                except Exception:
                    pass

            log_callback(f"已获取作品信息: {len(collected_works)}/{target_count}")

            if len(collected_works) >= target_count:
                break

            if not found_new:
                no_new_data_count += 1
                time.sleep(1)
                # 尝试点击下一页
                try:
                    next_btn = dp.ele("text:下一页", timeout=1)
                    if next_btn:
                        next_btn.click()
                        no_new_data_count = 0
                        time.sleep(2)
                except Exception:
                    pass
            else:
                no_new_data_count = 0

            if no_new_data_count > 10:
                log_callback("未检测到新数据，可能已到底部。")
                break

        log_callback(f"扫描完成，共获取 {len(collected_works)} 个作品。")
        dp.close()
        dp = None

        # 处理数据
        works_to_process = collected_works[:target_count]

        log_callback("开始下载 (多线程并行)...")

        download_tasks = []
        for index, work in enumerate(works_to_process):
            ts = work.get("created", time.time())
            date_str = datetime.fromtimestamp(ts).strftime("%Y_%m_%d")
            title = work.get("title", "无标题")
            title = re.sub(r'[\\/:*?"<>|]', "_", title)
            file_name_base = f"{date_str}_{title}"

            download_tasks.append(
                {
                    "work": work,
                    "index": index,
                    "file_name_base": file_name_base,
                }
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            for task in download_tasks:
                futures.append(
                    executor.submit(
                        process_bilibili_work,
                        task["work"],
                        task["index"],
                        len(works_to_process),
                        save_root,
                        task["file_name_base"],
                        log_callback,
                    )
                )
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
        # 这里需要一种机制通知UI线程结束，或者由UI层处理
        # 简化处理：finish_callback可以包含清理UI状态的逻辑，但这里主要是弹窗
        # 实际UI状态恢复最好由调用方通过回调处理
        pass


def process_bilibili_work(
    work, index, total_count, save_root, file_name_base, log_callback
):
    """
    [Data Layer] B站单个视频处理
    """
    try:
        bvid = work["bvid"]
        log_callback(f"[{index + 1}/{total_count}] {file_name_base} | 分析中...")

        video_url, audio_url = get_bilibili_play_url(bvid)

        if not video_url:
            log_callback(
                f"[{index + 1}/{total_count}] {file_name_base} -> 无法获取下载地址"
            )
            return

        video_path = os.path.join(save_root, f"{file_name_base}.mp4")

        # 下载视频 (带 Referer)
        if download_file(
            video_url,
            video_path,
            referer="https://www.bilibili.com/",
            log_callback=log_callback,
        ):
            log_callback(
                f"[{index + 1}/{total_count}] {file_name_base} -> 视频下载完成"
            )
        else:
            log_callback(
                f"[{index + 1}/{total_count}] {file_name_base} -> 视频下载失败"
            )

        # 尝试下载音频 (如果有)
        if audio_url:
            audio_path = os.path.join(save_root, f"{file_name_base}_audio.m4a")
            if not os.path.exists(audio_path):
                if download_file(
                    audio_url,
                    audio_path,
                    referer="https://www.bilibili.com/",
                    log_callback=log_callback,
                ):
                    log_callback(
                        f"[{index + 1}/{total_count}] {file_name_base} -> 音频下载完成"
                    )
            else:
                log_callback(
                    f"[{index + 1}/{total_count}] {file_name_base} -> 音频已存在"
                )

    except Exception as e:
        log_callback(f"[{index + 1}/{total_count}] {file_name_base} -> 处理出错: {e}")


def get_bilibili_play_url(bvid):
    """
    获取 B站 视频播放地址
    """
    url = f"https://www.bilibili.com/video/{bvid}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": "https://www.bilibili.com/",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            match = re.search(r"window\.__playinfo__=(.*?)</script>", resp.text)
            if match:
                info = json.loads(match.group(1))
                data = info.get("data", {})

                if "durl" in data and data["durl"]:
                    return data["durl"][0]["url"], None

                if "dash" in data:
                    video_url = None
                    audio_url = None
                    if "video" in data["dash"] and data["dash"]["video"]:
                        video_url = data["dash"]["video"][0]["baseUrl"]
                    if "audio" in data["dash"] and data["dash"]["audio"]:
                        audio_url = data["dash"]["audio"][0]["baseUrl"]
                    return video_url, audio_url
    except Exception:
        pass
    return None, None
