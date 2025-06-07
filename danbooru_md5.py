import hashlib

from pybooru import Danbooru

from lib import eagle_api
from danbooru_config import config  # 导入配置文件

# 配置常量
class Config:
    USERNAME = config["danbooru"]["username"]
    API_KEY = config["danbooru"]["api_key"]

# 初始化 Danbooru 客户端
client = Danbooru('danbooru', username=Config.USERNAME, api_key=Config.API_KEY)


def calculate_md5(file_path):
    # 创建一个 MD5 哈希对象
    md5_hash = hashlib.md5()

    # 以二进制模式打开文件
    with open(file_path, "rb") as f:
        # 一次读取文件的一部分以避免内存溢出
        for chunk in iter(lambda: f.read(4096), b""):
            md5_hash.update(chunk)

    # 返回计算得出的 MD5 哈希值
    return md5_hash.hexdigest()


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

        if folder_name_to_id["wrong_url"] in folder_ids:
            # 示例：计算图片文件的 MD5 值
            source_file = eagle_folder + id + ".info/" + name + '.' + ext
            md5_value = calculate_md5(source_file)
            print(f"The MD5 hash of the file is: {md5_value}")
            # 使用 MD5 值进行搜索
            post = client.post_list(tags=f'md5:{md5_value}')
            if post:
                # 计算正确的URL
                url = "https://danbooru.donmai.us/posts/" + str(post[0]["id"])
                eagle_api.update_item(id, new_url=url)
