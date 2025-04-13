import datetime
import os
import re

from pybooru import Danbooru

from lib import eagle_api

# 设置搜索条件
# search_querys = ["order:rank"]  # 修改为你想要搜索的条件
search_querys = ["kieed"]  # 修改为你想要搜索的条件
OvO = []
qwq = ["niliu_chahui","kupa_(jesterwii)","juejue_174","efuri_(riarea00)",
       "classic_(zildjian33)","hhh_(wave)","aoi_sakura_(seak5545)","meion"]
client = Danbooru('danbooru', username='YOUR_USERNAME', api_key='YOUR_API_KEY')


# 检查并处理每个类别
def create_folder_if_valid(category, folder_type):
    """
    创建文件夹的辅助函数，如果文件夹类型和类别有效则创建
    :param category: 文件夹类别
    :param folder_type: 文件夹类型名称
    """
    if category:  # 确保类别不是空字符串
        if category not in folder_name_to_id:
            folder_type_id = folder_name_to_id.get(folder_type)
            if folder_type_id is not None:  # 确保文件夹类型的 ID 有效
                eagle_api.create_folder(category, folder_type_id)


def get_all_results(query, limit_per_page=50, limit=200):
    # 存储所有结果的列表
    all_results = []
    # 初始化页数
    page = 1

    while len(all_results) < limit:
        # 获取当前页面的结果
        try:
            results = client.post_list(tags=query, page=page, limit=limit_per_page)
        except Exception as e:
            print(f"Error fetching data: {e}")
            break

        # 如果没有更多结果，退出循环
        if not results:
            break

        # 添加当前页面的结果到列表
        all_results.extend(results)
        print(f"Fetched {len(results)} results from page {page}")

        # 增加页数
        page += 1

    return all_results

list = list(set(search_querys))
print(list)
for search_query in list:
    # 获取所有结果
    results = get_all_results(search_query, limit=9999)

    print(f"Total results fetched: {len(results)}")

    rating_map = {
        'e': 'explicit',
        's': 'sensitive',
        'g': 'general',
        'q': 'questionable'
    }
    # 显示前几个结果
    for post in results:
        try:
            image_url = post['file_url']
        except:
            continue
        print(post)
        # print(datetime.datetime.strptime(post["created_at"], '%Y-%m-%dT%H:%M:%S.%f%z').strftime('year_%Y'))
        # url = post["source"]
        url = "https://danbooru.donmai.us/posts/" + str(post["id"])
        copyrights = post["tag_string_copyright"].split(' ')
        characters = post["tag_string_character"].split(' ')
        artists = post["tag_string_artist"].split(' ')
        all_metadata = post["tag_string_meta"].split(' ')
        normal_tag = post["tag_string_general"].split(' ')
        # 正则表达式模式，用于匹配我们感兴趣的标签
        pattern = re.compile(r'^\d+(girls?|boys?|others?)$|^multiple_(girls?|boys?|others?)$|^solo$')

        # 提取符合模式的标签
        count_tag = [tag for tag in normal_tag if pattern.match(tag)]

        # if "solo" not in count_tag:
        #     continue
        # 留下不符合模式的标签在原数组中
        normal_tag[:] = [tag for tag in normal_tag if not pattern.match(tag)]

        folder_id_to_name, folder_name_to_id, folder_to_root = eagle_api.get_folder_list_recursive()
        folderIds = [
            folder_name_to_id[
                datetime.datetime.strptime(post["created_at"], '%Y-%m-%dT%H:%M:%S.%f%z').strftime('year_%Y')],
            folder_name_to_id["Manual"], folder_name_to_id["FromDanbooru"],
            folder_name_to_id[rating_map[post["rating"]]],
            # folder_name_to_id["DanbooruHot"],
        ]

        # 处理 count_tag
        for count in count_tag:
            create_folder_if_valid(count, "Count")

        # 获取文件夹列表并更新 ID 映射
        folder_id_to_name, folder_name_to_id, folder_to_root = eagle_api.get_folder_list_recursive()
        for count in count_tag:
            if count:  # 只有在 count 不是空字符串时才进行操作
                folderIds.append(folder_name_to_id.get(count, None))

        # 处理 artists
        for artist in artists:
            create_folder_if_valid(artist, "Artist")

        # 获取文件夹列表并更新 ID 映射
        folder_id_to_name, folder_name_to_id, folder_to_root = eagle_api.get_folder_list_recursive()
        for artist in artists:
            if artist:  # 只有在 artist 不是空字符串时才进行操作
                folderIds.append(folder_name_to_id.get(artist, None))

        # 处理 copyrights
        for copyRight in copyrights:
            create_folder_if_valid(copyRight, "CopyrightNew")

        # 获取文件夹列表并更新 ID 映射
        folder_id_to_name, folder_name_to_id, folder_to_root = eagle_api.get_folder_list_recursive()
        for copyRight in copyrights:
            if copyRight:  # 只有在 copyRight 不是空字符串时才进行操作
                folderIds.append(folder_name_to_id.get(copyRight, None))

        # 处理 characters
        for character in characters:
            if len([c for c in copyrights if c]) != 0:
                create_folder_if_valid(character, copyrights[0])
            else:
                create_folder_if_valid(character, "CharacterNew")

        # 获取文件夹列表并更新 ID 映射
        folder_id_to_name, folder_name_to_id, folder_to_root = eagle_api.get_folder_list_recursive()
        for character in characters:
            if character:  # 只有在 character 不是空字符串时才进行操作
                folderIds.append(folder_name_to_id.get(character, None))

        # 处理 all_metadata
        for metadata in all_metadata:
            create_folder_if_valid(metadata, "metadata")

        # 获取文件夹列表并更新 ID 映射
        folder_id_to_name, folder_name_to_id, folder_to_root = eagle_api.get_folder_list_recursive()
        for metadata in all_metadata:
            if metadata:  # 只有在 metadata 不是空字符串时才进行操作
                folderIds.append(folder_name_to_id.get(metadata, None))

        if not folderIds:
            folderIds.append(None)
        eagle_api.addFromURL(image_url,
                             os.path.basename(image_url),
                             website=url,
                             tags=normal_tag,
                             annotation=None,
                             modificationTime=None,
                             folderIds=folderIds)
