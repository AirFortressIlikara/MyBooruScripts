import datetime
import os
import re
from typing import List, Dict, Optional

from pybooru import Danbooru
from lib.eagle_api import EagleAPI
from lib.synap_forest_api import SynapForestAPI
from danbooru_config import config  # 导入配置文件


# ======================================
#           初始化与配置
# ======================================
backend = EagleAPI()
# backend = SynapForestAPI()  # 若使用 SynapForest，可替换上行


class Config:
    """
    全局配置常量类。
    用于集中管理查询条件、账户信息、分页设置等。
    """

    SEARCH_QUERYS = ["order:rank"]  # 支持多标签与反选（-tag）
    USERNAME = config["danbooru"]["username"]
    API_KEY = config["danbooru"]["api_key"]
    LIMIT_PER_PAGE = 50  # 每页请求数量(Danbooru API 最大 100)
    MAX_LIMIT = 50  # 每次查询最大总数量


# 初始化 Danbooru 客户端
client = Danbooru("danbooru", username=Config.USERNAME, api_key=Config.API_KEY)

# 评分映射
RATING_MAP = {"e": "explicit", "s": "sensitive", "g": "general", "q": "questionable"}

# 正则: 匹配特定人物数量标签，如 “2girls” / “multiple_boys” / “solo”
COUNT_TAG_PATTERN = re.compile(
    r"^\d+[\+]?(girls?|boys?|others?)$|^multiple_(girls?|boys?|others?)$|^solo$"
)

# 正则: 提取 Danbooru 图片 URL 中的 ID
DANBOORU_ID_PATTERN = re.compile(r"https://danbooru\.donmai\.us/posts/(\d+)")

# 全局文件夹映射缓存
folder_id_to_name = {}
folder_name_to_id = {}
folder_to_root = {}


# ======================================
#         文件夹映射与创建逻辑
# ======================================
def update_folder_mappings():
    """
    更新全局文件夹映射
    """
    global folder_id_to_name, folder_name_to_id, folder_to_root
    folder_id_to_name, folder_name_to_id, folder_to_root = (
        backend.get_folder_list_recursive()
    )


def add_folder_mappings(name: str, id: str, root_id: str):
    """
    更新本地文件夹映射表。
    """
    global folder_id_to_name, folder_name_to_id, folder_to_root
    folder_name_to_id[name] = id
    folder_id_to_name[id] = name
    folder_to_root[id] = root_id


def create_folder_if_valid(category: str, folder_type: str) -> None:
    """
    创建文件夹(如果不存在)。
    自动在指定的“类型文件夹”下创建“类别子文件夹”。
    :param category: 文件夹类别
    :param folder_type: 文件夹类型名称
    """
    global folder_name_to_id, folder_id_to_name, folder_to_root

    # 创建顶级类型文件夹
    if folder_type not in folder_name_to_id:
        new_id = backend.create_folder(folder_name=folder_type)
        add_folder_mappings(folder_type, new_id, new_id)

    # 创建类别文件夹
    if category and category not in folder_name_to_id:
        folder_type_id = folder_name_to_id.get(folder_type)
        if folder_type_id is not None:
            new_id = backend.create_folder(category, folder_type_id)
            add_folder_mappings(category, new_id, folder_to_root[folder_type_id])


# ======================================
#           查询与过滤逻辑
# ======================================
def parse_query(query: str) -> tuple[list[str], list[str]]:
    """
    解析搜索字符串为包含与排除标签。
    示例: "girl smile -blush -solo" -> (["girl", "smile"], ["blush", "solo"])
    """
    include_tags, exclude_tags = [], []
    for tag in query.split():
        tag = tag.strip()
        if not tag:
            continue
        if tag.startswith("-"):
            exclude_tags.append(tag[1:])
        else:
            include_tags.append(tag)
    return include_tags, exclude_tags


def get_all_results(
    query: str,
    limit_per_page: int = Config.LIMIT_PER_PAGE,
    max_limit: int = Config.MAX_LIMIT,
) -> List[Dict]:
    """
    分页获取 Danbooru 搜索结果，支持多标签本地筛选与反选。
    """
    include_tags, exclude_tags = parse_query(query)

    # API 仅支持两个标签
    api_tags = " ".join(include_tags[:2]) if include_tags else ""
    print(
        f"[Danbooru] API 查询: {api_tags} | 本地过滤: {include_tags[2:]} - {exclude_tags}"
    )

    all_results = []
    page = 1

    while len(all_results) < max_limit:
        try:
            results = client.post_list(tags=api_tags, page=page, limit=limit_per_page)
            if not results:
                break
            all_results.extend(results)
            print(f"[Danbooru] Page {page}: fetched {len(results)} results.")
            page += 1
        except Exception as e:
            print(f"[Error] Fetching '{api_tags}' page {page} failed: {e}")
            break

    print(f"[Danbooru] Total {len(all_results)} results before filtering.")
    return filter_local_posts(all_results, include_tags[2:], exclude_tags)


def filter_local_posts(
    posts: List[Dict], include_tags: List[str], exclude_tags: List[str]
) -> List[Dict]:
    """
    本地标签筛选逻辑:
    - 必须包含所有 include_tags
    - 必须不包含任何 exclude_tags
    """

    def get_all_tags(post):
        """提取该作品的所有标签（包括 general、character、artist、copyright）"""
        tags = set()
        for key in [
            "tag_string_general",
            "tag_string_character",
            "tag_string_copyright",
            "tag_string_artist",
            "tag_string_meta",
        ]:
            tags.update(tag.lower() for tag in post.get(key, "").split())
        return tags

    filtered = []
    for i, post in enumerate(posts):
        tags = get_all_tags(post)
        if i < 3:
            print(f"DEBUG Post {i}: tags={list(tags)[:10]}...")  # 打印前3个的标签

        # 包含判断
        missing = [t for t in include_tags if t not in tags]
        if missing:
            print(f"DEBUG Filtered out (missing tags): {missing}")
            continue

        # 排除判断
        blocked = [t for t in exclude_tags if t in tags]
        if blocked:
            print(f"DEBUG Filtered out (excluded tags): {blocked}")
            continue

        filtered.append(post)

    print(f"[Filter] After local filter: {len(filtered)} / {len(posts)} remain.")
    return filtered


# ======================================
#               标签处理
# ======================================
def process_tags(tag_string: str, pattern: re.Pattern = None) -> tuple:
    """
    将标签字符串拆分为列表，并根据正则过滤。
    :param tag_string: 以空格分隔的标签字符串
    :param pattern: 匹配模式(可选)
    :return: (匹配的标签列表, 未匹配的标签列表)
    """
    tags = tag_string.split(" ") if tag_string else []
    if pattern:
        matched = [tag for tag in tags if pattern.match(tag)]
        remaining = [tag for tag in tags if not pattern.match(tag)]
        return matched, remaining
    return tags, []


# ======================================
#         文件夹 ID 归类逻辑
# ======================================
def get_folder_ids_for_post(post: Dict, search_query: str) -> List[Optional[int]]:
    """
    根据帖子属性(时间、评分、搜索条件)确定初始文件夹 ID
    :param post: 帖子数据
    :param search_query: 当前搜索条件
    :return: 文件夹ID列表
    """
    folder_ids = []

    # 日期解析(兼容多种时间格式)
    try:
        created_at = datetime.datetime.strptime(
            post["created_at"], "%Y-%m-%dT%H:%M:%S.%f%z"
        )
    except ValueError:
        created_at = datetime.datetime.strptime(
            post["created_at"], "%Y-%m-%dT%H:%M:%S%z"
        )

    # 常规归类文件夹
    folder_ids.extend(
        [
            folder_name_to_id.get(created_at.strftime("year_%Y")),
            folder_name_to_id.get("Manual"),
            folder_name_to_id.get("FromDanbooru"),
            folder_name_to_id.get(RATING_MAP.get(post["rating"], "general")),
        ]
    )

    # 特殊归类: 热门榜单
    if "order:rank" in search_query.lower():
        hot_id = folder_name_to_id.get("DanbooruHot")
        if hot_id:
            folder_ids.append(hot_id)

    return [fid for fid in folder_ids if fid is not None]


# ======================================
#           处理单个帖子
# ======================================
def process_post(post: Dict, search_query: str, existing_ids: set) -> None:
    """
    处理单个 Danbooru 帖子:
    - 解析标签
    - 动态创建文件夹
    - 上传图片到 Eagle
    - 更新已存在 ID 集合
    :param post: 帖子数据
    """
    try:
        image_url = post["file_url"]
    except KeyError:
        print(f"[Skip] Post {post.get('id', 'unknown')} has no file_url.")
        return

    post_id = post["id"]
    print(f"[Process] Post {post_id}")

    url = f"https://danbooru.donmai.us/posts/{post_id}"

    # 标签分类解析
    copyrights, _ = process_tags(post["tag_string_copyright"])
    characters, _ = process_tags(post["tag_string_character"])
    artists, _ = process_tags(post["tag_string_artist"])
    all_metadata, _ = process_tags(post["tag_string_meta"])
    count_tags, normal_tags = process_tags(
        post["tag_string_general"], COUNT_TAG_PATTERN
    )

    # 文件夹集合
    folder_ids = set(get_folder_ids_for_post(post, search_query))

    # 根据标签创建/映射文件夹
    tag_groups = [
        ("Count", count_tags),
        ("Artist", artists),
        ("CopyrightNew", copyrights),
        (copyrights[0] if copyrights else "CharacterNew", characters),
        ("metadata", all_metadata),
    ]

    for folder_type, tags in tag_groups:
        for tag in tags:
            if not tag:
                continue
            create_folder_if_valid(tag, folder_type)
            if tag in folder_name_to_id:
                folder_ids.add(folder_name_to_id[tag])

    # 上传图片
    backend.add_from_url(
        image_url,
        os.path.basename(image_url),
        website=url,
        tags=normal_tags,
        annotation=None,
        modificationTime=None,
        folderIds=list(folder_ids) if folder_ids else None,
    )


# ======================================
#        从 Eagle 获取已有 Danbooru ID
# ======================================
def get_existing_danbooru_ids() -> set:
    """
    从 Eagle 获取现有条目，提取已存在的 Danbooru ID 集合。
    """
    existing_items = backend.get_items()
    danbooru_ids = set()

    for item in existing_items:
        url = item.get("url", "")
        match = DANBOORU_ID_PATTERN.match(url)
        if match:
            danbooru_ids.add(int(match.group(1)))

    print(f"[Info] 已存在 {len(danbooru_ids)} 个 Danbooru 条目。")
    return danbooru_ids


# ======================================
#              主程序入口
# ======================================
def main():
    """
    主执行逻辑:
    - 同步 Eagle 文件夹结构
    - 读取已存在条目
    - 执行 Danbooru 查询
    - 下载并导入图片(跳过重复)
    """
    update_folder_mappings()
    existing_ids = get_existing_danbooru_ids()

    unique_queries = list(set(Config.SEARCH_QUERYS))
    print(f"[Start] Processing queries: {unique_queries}")

    for search_query in unique_queries:
        print(f"\n[Query] '{search_query}' 开始处理...")
        results = get_all_results(search_query, max_limit=Config.MAX_LIMIT)
        print(f"[Query] 共获取 {len(results)} 条结果。")

        for post in results:
            post_id = post.get("id")
            if post_id in existing_ids:
                print(f"[Skip] Duplicate post {post_id}")
                continue
            process_post(post, search_query, existing_ids)

            # 动态维护已存在ID
            existing_ids.add(post_id)
            print(f"[Added] Post {post_id} added successfully.")


if __name__ == "__main__":
    main()
