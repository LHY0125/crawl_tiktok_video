import os


def find_edge_path():
    """
    [Utils] 自动查找 Edge 浏览器路径，提升用户体验
    """
    possible_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expanduser(r"~\AppData\Local\Microsoft\Edge\Application\msedge.exe"),
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None
