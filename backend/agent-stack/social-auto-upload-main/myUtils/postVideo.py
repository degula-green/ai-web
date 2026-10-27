import asyncio
from pathlib import Path

from conf import BASE_DIR
from uploader.douyin_uploader.main import (
    DOUYIN_PUBLISH_STRATEGY_IMMEDIATE,
    DOUYIN_PUBLISH_STRATEGY_SCHEDULED,
    DouYinVideo,
)
from uploader.ks_uploader.main import KSVideo
from uploader.tencent_uploader.main import TencentVideo
from uploader.xiaohongshu_uploader.main import (
    XIAOHONGSHU_PUBLISH_STRATEGY_IMMEDIATE,
    XIAOHONGSHU_PUBLISH_STRATEGY_SCHEDULED,
    XiaoHongShuVideo,
)
from utils.constant import TencentZoneTypes
from utils.files_times import generate_schedule_time_next_day


def post_video_tencent(
    title,
    desc,
    files,
    tags,
    account_file,
    category=TencentZoneTypes.LIFESTYLE.value,
    enableTimer=False,
    videos_per_day=1,
    daily_times=None,
    start_days=0,
    is_draft=False,
    headless=True,
):
    account_file = [Path(BASE_DIR / "cookiesFile" / file) for file in account_file]
    files = [Path(BASE_DIR / "videoFile" / file) for file in files]
    if enableTimer:
        publish_datetimes = generate_schedule_time_next_day(len(files), videos_per_day, daily_times, start_days)
    else:
        publish_datetimes = [0 for _ in range(len(files))]

    for index, file in enumerate(files):
        for cookie in account_file:
            print(f"文件路径{str(file)}")
            print(f"视频文件名：{file}")
            print(f"标题：{title}")
            print(f"Hashtag：{tags}")
            app = TencentVideo(title, str(file), tags, publish_datetimes[index], cookie, category, is_draft, headless=headless)
            asyncio.run(app.main(), debug=False)


def post_video_DouYin(
    title,
    desc,
    files,
    tags,
    account_file,
    category=TencentZoneTypes.LIFESTYLE.value,
    enableTimer=False,
    videos_per_day=1,
    daily_times=None,
    start_days=0,
    thumbnail_path="",
    productLink="",
    productTitle="",
    headless=True,
):
    account_file = [Path(BASE_DIR / "cookiesFile" / file) for file in account_file]
    files = [Path(BASE_DIR / "videoFile" / file) for file in files]
    publish_strategy = DOUYIN_PUBLISH_STRATEGY_SCHEDULED if enableTimer else DOUYIN_PUBLISH_STRATEGY_IMMEDIATE
    if enableTimer:
        publish_datetimes = generate_schedule_time_next_day(len(files), videos_per_day, daily_times, start_days)
    else:
        publish_datetimes = [0 for _ in range(len(files))]

    for index, file in enumerate(files):
        for cookie in account_file:
            print(f"文件路径{str(file)}")
            print(f"视频文件名：{file}")
            print(f"标题：{title}")
            print(f"Hashtag：{tags}")
            app = DouYinVideo(
                title,
                str(file),
                tags,
                publish_datetimes[index],
                cookie,
                thumbnail_path,
                productLink,
                productTitle,
                desc=desc,
                publish_strategy=publish_strategy,
                headless=headless,
            )
            asyncio.run(app.douyin_upload_video(), debug=False)


def post_video_ks(
    title,
    desc,
    files,
    tags,
    account_file,
    category=TencentZoneTypes.LIFESTYLE.value,
    enableTimer=False,
    videos_per_day=1,
    daily_times=None,
    start_days=0,
    headless=True,
):
    account_file = [Path(BASE_DIR / "cookiesFile" / file) for file in account_file]
    files = [Path(BASE_DIR / "videoFile" / file) for file in files]
    if enableTimer:
        publish_datetimes = generate_schedule_time_next_day(len(files), videos_per_day, daily_times, start_days)
    else:
        publish_datetimes = [0 for _ in range(len(files))]

    for index, file in enumerate(files):
        for cookie in account_file:
            print(f"文件路径{str(file)}")
            print(f"视频文件名：{file}")
            print(f"标题：{title}")
            print(f"Hashtag：{tags}")
            app = KSVideo(title, str(file), tags, publish_datetimes[index], cookie, desc=desc, headless=headless)
            asyncio.run(app.main(), debug=False)


def post_video_xhs(
    title,
    desc,
    files,
    tags,
    account_file,
    category=TencentZoneTypes.LIFESTYLE.value,
    enableTimer=False,
    videos_per_day=1,
    daily_times=None,
    start_days=0,
    headless=True,
):
    account_file = [Path(BASE_DIR / "cookiesFile" / file) for file in account_file]
    files = [Path(BASE_DIR / "videoFile" / file) for file in files]
    file_num = len(files)
    publish_strategy = XIAOHONGSHU_PUBLISH_STRATEGY_SCHEDULED if enableTimer else XIAOHONGSHU_PUBLISH_STRATEGY_IMMEDIATE
    if enableTimer:
        publish_datetimes = generate_schedule_time_next_day(file_num, videos_per_day, daily_times, start_days)
    else:
        publish_datetimes = [0 for _ in range(file_num)]

    for index, file in enumerate(files):
        for cookie in account_file:
            print(f"视频文件名：{file}")
            print(f"标题：{title}")
            print(f"Hashtag：{tags}")
            app = XiaoHongShuVideo(
                title,
                file,
                tags,
                publish_datetimes[index],
                cookie,
                desc=desc,
                publish_strategy=publish_strategy,
                headless=headless,
            )
            asyncio.run(app.main(), debug=False)
