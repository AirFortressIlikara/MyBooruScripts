import requests

def addFromURL(img_url, name, website=None, tags=None, annotation=None, modificationTime=None, folderIds=None, headers=None):
    url = "http://localhost:41695/api/item/addFromURL"
    data = {"url": img_url, "name": name}

    if website:
        data["website"] = website
    if tags:
        data["tags"] = tags
    if annotation:
        data["annotation"] = annotation
    if modificationTime:
        data["modificationTime"] = modificationTime
    if folderIds:
        data["folderIds"] = folderIds
    if headers:
        data["headers"] = headers
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        result = response.json()
        print("addFromURL successfully. Response:", result)
    else:
        print(f"Error addFromURL. Status code: {response.status_code}")


def create_folder(folder_name, parent=None):
    url = "http://localhost:41595/api/folder/create"
    data = {"folderName": folder_name}

    if parent:
        data["parent"] = parent

    headers = {"Content-Type": "application/json"}

    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        result = response.json()
        print("Folder created successfully. Response:", result)
    else:
        print(f"Error creating folder. Status code: {response.status_code}")


def update_item(item_id, tags=None, annotation=None, new_url=None, star=None, name = None, folders = None):
    url = "http://localhost:41695/api/item/update"
    data = {"id": item_id}

    if tags:
        data["tags"] = tags
    if annotation:
        data["annotation"] = annotation
    if new_url:
        data["url"] = new_url
    if star:
        data["star"] = star
    if name:
        data["name"] = name
    if folders:
        data["folders"] = folders

    headers = {"Content-Type": "application/json"}

    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        result = response.json()
        print("Item updated successfully. Response:", result)
    else:
        print(f"Error updating item. Status code: {response.status_code}")


def get_items():
    url = "http://localhost:41595/api/item/list"
    params = {
        "limit": 100000,
        "orderBy": "NAME",
        "ext": ""
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        api_data = response.json()  # 将响应内容转换为Python字典
        status = api_data.get("status")  # 获取“status”键的值
        if status == "success":
            data = api_data.get("data")  # 提取“data”字段
            # 根据需要进一步处理“data”
            return data
        else:
            print(f"API请求失败。状态：{status}")
            return None
    else:
        print(f"获取项目时出错。状态码：{response.status_code}")
        return None


def get_folder_list_recursive():
    url = "http://localhost:41595/api/folder/list"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        folders = data.get("data", [])
        folder_id_to_name = {}
        folder_name_to_id = {}
        folder_to_root = {}  # 初始化一个字典来存储文件夹到根文件夹的映射
        queue = folders.copy()

        while queue:
            folder = queue.pop(0)
            folder_id = folder.get("id")
            folder_name = folder.get("name")
            folder_id_to_name[folder_id] = folder_name
            folder_name_to_id[folder_name] = folder_id
            if folder_to_root.get(folder_id) is None:
                folder_to_root[folder_id] = folder_id

            # 检查文件夹是否有子文件夹
            children = folder.get("children", [])
            if children:
                # 将子文件夹添加到队列中以进一步处理
                queue.extend(children)

                # 更新每个子文件夹的文件夹到根文件夹映射
                for child in children:
                    child_id = child.get("id")
                    folder_to_root[child_id] = folder_to_root[folder_id]

        return folder_id_to_name, folder_name_to_id, folder_to_root
    else:
        print(f"获取文件夹列表时出错。状态码：{response.status_code}")
        return None, None


def get_folders_by_root_id(root_id, folder_to_root):
    folders = []
    for folder_id, root_folder_id in folder_to_root.items():
        if root_folder_id == root_id:
            folders.append(folder_id)
    return folders


def get_folder_name_by_id(folder_id, folder_id_to_name):
    return folder_id_to_name.get(folder_id, "Folder not found")
