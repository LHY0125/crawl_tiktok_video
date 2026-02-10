import requests
import time

def download_file(url, filepath, referer=None, log_callback=None):
    """
    [Data Layer] 文件下载执行器
    使用 requests 流式下载，包含重试机制
    """
    try:
        # 根据不同平台可能需要调整 Headers
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }

        # 优先使用传入的 referer
        if referer:
            headers["Referer"] = referer
        else:
            # 简单的 Referer 区分 (保留旧逻辑作为后备)
            if (
                "bilibili.com" in url
                or "hdslb.com" in url
                or "bilivideo.com" in url
            ):
                headers["Referer"] = "https://www.bilibili.com/"
            else:
                headers["Referer"] = "https://www.douyin.com/"

        for i in range(3):
            try:
                response = requests.get(
                    url, headers=headers, stream=True, timeout=20
                )
                if response.status_code == 200:
                    with open(filepath, "wb") as f:
                        for chunk in response.iter_content(chunk_size=1024 * 1024):
                            f.write(chunk)
                    return True
                else:
                    # 只有在最后一次尝试失败时记录状态码，或者记录每次警告
                    if i == 2:
                        if log_callback:
                            log_callback(
                                f"下载请求失败: Status {response.status_code} | URL: {url[:30]}..."
                            )
            except requests.exceptions.RequestException as e:
                if i == 2:
                    if log_callback:
                        log_callback(f"网络请求异常: {e}")
                time.sleep(1)
                continue
        return False
    except Exception as e:
        if log_callback:
            log_callback(f"下载出错: {e}")
        return False