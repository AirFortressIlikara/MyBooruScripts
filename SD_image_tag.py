import json
import re

import png

from lib import eagle_api


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


def read_text_chunk(png_file):
    reader = png.Reader(filename=png_file)
    chunks = reader.chunks()
    for chunk_type, chunk_data in chunks:
        if chunk_type == b'tEXt':
            text = chunk_data.decode('utf-8')
            text = re.sub(r'[^\x20-\x7E]+', ' ', text)
            if text.startswith('Comment'):
                comment_json = text.split('Comment', 1)[1].strip()
                comment_data = json.loads(comment_json)
                return comment_data

def read_modelhash(png_file):
    reader = png.Reader(filename=png_file)
    chunks = reader.chunks()
    for chunk_type, chunk_data in chunks:
        print(chunk_type)
        if chunk_type == b'iTXt': #comfy style
            text = chunk_data.decode('utf-8')
            text = re.sub(r'[^\x20-\x7E]+', ' ', text)
            print(text)
            # 使用正则表达式匹配 Model hash
            match = re.search(r'Model hash: ([a-fA-F0-9]+)', text)
            if match:
                model_hash = match.group(1)
                print("Model hash:", model_hash)
                return model_hash
            else:
                print("Model hash not found.")
                return -1
        if chunk_type == b'tEXt': #nai3 style
            text = chunk_data.decode('utf-8')
            text = re.sub(r'[^\x20-\x7E]+', ' ', text)
            print(text)
            # 使用正则表达式匹配 Model hash
            match = re.search(r'Model hash: ([a-fA-F0-9]+)', text)
            if match:
                model_hash = match.group(1)
                print("Model hash:", model_hash)
                return model_hash
            else:
                text = chunk_data.decode('utf-8')
                text = re.sub(r'[^\x20-\x7E]+', ' ', text)
                if text.startswith('Source'):
                    print(text)
                    # 使用正则表达式提取 hash 部分
                    match = re.search(r'Stable Diffusion XL\s+([a-fA-F0-9]+)', text)
                    if match:
                        model_hash = match.group(1).lower()  # 提取并转换为小写
                        print("Model hash:", model_hash)
                        return model_hash
                    else:
                        print("Model hash not found.")
                        return -1
    reader1 = png.Reader(filename=png_file)
    chunks1 = reader1.chunks()
    for chunk_type, chunk_data in chunks1:
        print(chunk_type)
        if chunk_type == b'iTXt' or chunk_type == b'tEXt': #comfy style
            text = chunk_data.decode('utf-8')
            text = re.sub(r'[^\x20-\x7E]+', ' ', text)
            print(text)
            # 使用正则表达式匹配 Model hash
            match = re.search(r'Model:\s*([^\s,]+)', text)
            if match:
                model_name = match.group(1)
                print("Model name:", model_name)
                return model_name
            else:
                print("Model name not found.")
                return -1
    return -1


eagle_folder = "D:/AI Image.library/images/"
artist_prefix = "artist:"

items_data = eagle_api.get_items()
folder_id_to_name, folder_name_to_id, folder_to_root = eagle_api.get_folder_list_recursive()
print(len(items_data))
if items_data:
    # 进一步处理“items_data”
    print("成功提取数据！")
    i = 1
    for item in items_data:
        # 提取tags和folders
        id = item.get("id", [])
        name = item.get("name", [])
        ext = item.get("ext", [])
        folder_ids = item.get("folders", [])
        if ext != 'png':
            continue
        if folder_name_to_id["new ai"] in folder_ids:
        # if folder_name_to_id["new ai"] in folder_ids:
            # 示例用法
            source_file = eagle_folder + id + ".info/" + name + '.' + ext
            print(source_file)
            data = read_modelhash(source_file)
            print([folder_id_to_name[folder_id] for folder_id in folder_ids])
            print(data)
            if data == -1:
                # folder_ids.append(folder_name_to_id["qwqqwqqwq"])
                print(-1)
            else:
                folder_ids.append(folder_name_to_id["newaidetected"])
                if data == "c1e1de52" or data == "8ba2af87" or data == "7bccaa2c":
                    folder_ids.append(folder_name_to_id["todonai3"])
                create_folder_if_valid(data, "AI Generated")
                folder_id_to_name, folder_name_to_id, folder_to_root = eagle_api.get_folder_list_recursive()
                folder_ids.append(folder_name_to_id[data])

                # artists = re.findall(r'artist:([^,}\]]+)', data['prompt'])
                # artists = [artist.strip().replace(' ', '_') for artist in artists]
                # # 处理 artists
                # for artist in artists:
                #     create_folder_if_valid(artist, "Artist")
                #
                # # 获取文件夹列表并更新 ID 映射
                # folder_id_to_name, folder_name_to_id, folder_to_root = eagle_api.get_folder_list_recursive()
                # for artist in artists:
                #     if artist:  # 只有在 artist 不是空字符串时才进行操作
                #         folder_id = folder_name_to_id.get(artist, None)
                #         if folder_id not in folder_ids:
                #             folder_ids.append(folder_id)
                # print([folder_id_to_name[folder_id] for folder_id in folder_ids])
                # print(folder_ids)
            folder_ids = list(set(folder_ids))
            eagle_api.update_item(id, folders=folder_ids)
