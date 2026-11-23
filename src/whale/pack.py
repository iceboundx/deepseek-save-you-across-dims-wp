"""Write the Wallpaper Engine metadata and a thumbnail from the built video."""

import json

from PIL import Image

from .timeline import SIZE


VIDEO_NAME = "wallpaper.mp4"


def pack(directory, preview, size, fps, frame_count):
    thumbnail = Image.frombytes("RGB", SIZE, preview)
    thumbnail.thumbnail((512, 512), Image.Resampling.LANCZOS)
    thumbnail.save(directory / "preview.jpg", quality=94)

    project = {
        "title": "穿越次元壁，也要拯救你",
        "description": (
            "DeepSeek 鲸鱼娘隔着屏幕伸出手，指尖的彩光和眼角的蓝色方块随水光明灭。\n"
            f"{size[0]} × {size[1]}｜{fps} fps｜{frame_count / fps:g} 秒循环｜无声\n\n"
            "原图作者：dy翩翩（抖音）\n原视频作者：偶鲸鲸（哔哩哔哩）\n"
            "原视频：《穿越次元壁也要拯救你》\nhttps://www.bilibili.com/video/BV1pxe16QEcT"
        ),
        "type": "video",
        "version": 1,
        "file": VIDEO_NAME,
        "preview": "preview.jpg",
        "contentrating": "Everyone",
        "ratingsex": "none",
        "ratingviolence": "none",
        "tags": ["Anime"],
        "general": {"properties": {"schemecolor": {
            "order": 0, "text": "ui_browse_properties_scheme_color",
            "type": "color", "value": "0 0 0",
        }}},
    }
    (directory / "project.json").write_text(
        json.dumps(project, ensure_ascii=False, indent=4) + "\n", encoding="utf-8"
    )
