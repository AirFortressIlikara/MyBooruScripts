import datetime
import os
import re
import time
from typing import List, Dict, Optional

from pybooru import Danbooru

from lib.eagle_api import EagleAPI
from lib.synap_forest_api import SynapForestAPI

# 初始化API客户端
backend = EagleAPI()
# backend = SynapForestAPI()

# 配置常量
class Config:
    SEARCH_QUERYS = ["order:rank"]  # 修改为你想要搜索的条件
    USERNAME = 'YOUR_USERNAME'
    API_KEY = 'YOUR_API_KEY'
    LIMIT_PER_PAGE = 50
    MAX_LIMIT = 50

# 初始化客户端
client = Danbooru('danbooru', username=Config.USERNAME, api_key=Config.API_KEY)

# 评分映射
RATING_MAP = {
    'e': 'explicit',
    's': 'sensitive',
    'g': 'general',
    'q': 'questionable'
}

# 正则表达式模式，用于匹配我们感兴趣的标签
COUNT_TAG_PATTERN = re.compile(r'^\d+(girls?|boys?|others?)$|^multiple_(girls?|boys?|others?)$|^solo$')

def create_folder_if_valid(category: str, folder_type: str, 
                         folder_name_to_id: Dict[str, int]) -> None:
    """
    创建文件夹的辅助函数，如果文件夹类型和类别有效则创建
    :param category: 文件夹类别
    :param folder_type: 文件夹类型名称
    :param folder_name_to_id: 文件夹名称到ID的映射字典
    """
    if folder_type not in folder_name_to_id:
        backend.create_folder(folder_name=folder_type)

    if category and category not in folder_name_to_id:
        folder_type_id = folder_name_to_id.get(folder_type)
        if folder_type_id is not None:
            backend.create_folder(category, folder_type_id)

def get_all_results(query: str, limit_per_page: int = Config.LIMIT_PER_PAGE, 
                    max_limit: int = Config.MAX_LIMIT) -> List[Dict]:
    """
    获取所有符合查询条件的结果
    :param query: 搜索查询
    :param limit_per_page: 每页限制
    :param max_limit: 最大结果限制
    :return: 结果列表
    """
    all_results = []
    page = 1

    while len(all_results) < max_limit:
        try:
            results = client.post_list(tags=query, page=page, limit=limit_per_page)
            if not results:
                break
                
            all_results.extend(results)
            print(f"Fetched {len(results)} results from page {page}")
            page += 1
        except Exception as e:
            print(f"Error fetching data for query '{query}' on page {page}: {e}")
            break

    return all_results

def process_tags(tag_string: str, pattern: re.Pattern = None) -> tuple:
    """
    处理标签字符串
    :param tag_string: 标签字符串
    :param pattern: 正则表达式模式
    :return: (匹配的标签列表, 剩余的标签列表)
    """
    tags = tag_string.split(' ') if tag_string else []
    if pattern:
        matched = [tag for tag in tags if pattern.match(tag)]
        remaining = [tag for tag in tags if not pattern.match(tag)]
        return matched, remaining
    return tags, []

def get_folder_ids_for_post(post: Dict, folder_name_to_id: Dict[str, int], 
                          search_query: str) -> List[Optional[int]]:
    """
    获取帖子对应的所有文件夹ID
    :param post: 帖子数据
    :param folder_name_to_id: 文件夹名称到ID的映射
    :param search_query: 当前搜索条件
    :return: 文件夹ID列表
    """
    folder_ids = [
        folder_name_to_id.get(
            datetime.datetime.strptime(post["created_at"], '%Y-%m-%dT%H:%M:%S.%f%z').strftime('year_%Y')
        ),
        folder_name_to_id.get("Manual"),
        folder_name_to_id.get("FromDanbooru"),
        folder_name_to_id.get(RATING_MAP[post["rating"]])
    ]
    
    # 只有当搜索条件包含order:rank时才添加DanbooruHot文件夹
    if "order:rank" in search_query.lower():
        danbooru_hot_id = folder_name_to_id.get("DanbooruHot")
        if danbooru_hot_id:
            folder_ids.append(danbooru_hot_id)
    
    # 过滤掉None值
    return [fid for fid in folder_ids if fid is not None]

def process_post(post: Dict, search_query: str) -> None:
    """
    处理单个帖子
    :param post: 帖子数据
    """
    try:
        image_url = post['file_url']
    except KeyError:
        print(f"Post {post.get('id', 'unknown')} has no file_url, skipping...")
        return

    print(f"Processing post {post['id']}")
    url = f"https://danbooru.donmai.us/posts/{post['id']}"
    
    # 获取文件夹结构
    folder_id_to_name, folder_name_to_id, folder_to_root = backend.get_folder_list_recursive()
    
    # 处理各种标签
    copyrights, _ = process_tags(post["tag_string_copyright"])
    characters, _ = process_tags(post["tag_string_character"])
    artists, _ = process_tags(post["tag_string_artist"])
    all_metadata, _ = process_tags(post["tag_string_meta"])
    count_tags, normal_tags = process_tags(post["tag_string_general"], COUNT_TAG_PATTERN)
    
    # 获取基础文件夹ID
    folder_ids = get_folder_ids_for_post(post, folder_name_to_id, search_query)
    
    # 处理并添加各类标签对应的文件夹
    tag_groups = [
        ("Count", count_tags),
        ("Artist", artists),
        ("CopyrightNew", copyrights),
        (copyrights[0] if copyrights else "CharacterNew", characters),
        ("metadata", all_metadata)
    ]
    
    for folder_type, tags in tag_groups:
        for tag in tags:
            if tag:
                create_folder_if_valid(tag, folder_type, folder_name_to_id)
        
        # 刷新文件夹映射
        folder_id_to_name, folder_name_to_id, folder_to_root = backend.get_folder_list_recursive()
        
        # 添加有效的文件夹ID
        for tag in tags:
            if tag and tag in folder_name_to_id:
                folder_ids.append(folder_name_to_id[tag])

    # 添加图片到Eagle
    backend.add_from_url(
        image_url,
        os.path.basename(image_url),
        website=url,
        tags=normal_tags,
        annotation=None,
        modificationTime=None,
        folderIds=folder_ids if folder_ids else [None]
    )

def main():
    unique_queries = list(set(Config.SEARCH_QUERYS))
    print(f"Processing queries: {unique_queries}")
    
    for search_query in unique_queries:
        print(f"\nStarting processing for query: '{search_query}'")
        results = get_all_results(search_query, max_limit=Config.MAX_LIMIT)
        print(f"Total results fetched: {len(results)}")
        
        for post in results:
            # try:
                process_post(post, search_query)
            # except Exception as e:
            #     print(f"Error processing post {post.get('id', 'unknown')}: {e}")

if __name__ == "__main__":
    main()