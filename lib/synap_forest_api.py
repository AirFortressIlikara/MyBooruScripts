import requests
from typing import Dict, List, Optional, Tuple, Any


class SynapForestAPI:
    root_folder_id = "00000000-0000-0000-0000-000000000000"

    def __init__(self):
        """
        初始化 SynapForest API 客户端
        """
        self.base_url = "http://127.0.0.1:42595"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "TEST123123",
        }

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Optional[Dict]:
        """
        内部请求方法
        :param method: HTTP 方法 ('get' 或 'post')
        :param endpoint: API 端点
        :param is_item_api: 是否使用项目API端口(41695)
        :param data: 请求数据
        :param params: 查询参数
        :return: 响应数据字典或 None
        """
        base_url = self.base_url
        url = f"{base_url}{endpoint}"

        try:
            if method.lower() == "get":
                response = requests.get(url, params=params, headers=self.headers, proxies={'http': None, 'https': None})
            else:
                response = requests.post(url, json=data, headers=self.headers, proxies={'http': None, 'https': None})

            if response.status_code == 200:
                return response.json()
            else:
                print(
                    f"Error in {method.upper()} request to {url}. "
                    f"Status code: {response.status_code}, Response: {response.text}"
                )
                return None

        except requests.exceptions.RequestException as e:
            print(f"Request failed for {url}: {str(e)}")
            return None

    def add_from_url(
        self,
        img_url: str,
        name: str,
        website: Optional[str] = None,
        tags: Optional[List[str]] = None,
        annotation: Optional[str] = None,
        modificationTime: Optional[str] = None,
        folderIds: Optional[List[str]] = None,
        headers: Optional[Dict] = None,
    ) -> bool:
        """
        从 URL 添加项目
        """
        data = {
            "items": [
                {
                    "url": img_url,
                    "name": name,
                    "website": website,
                    "tags": tags,
                    "annotation": annotation,
                    "modificationTime": modificationTime,
                }
            ],
            "tag_mode": "name",
            "folderIds": folderIds,
            "headers": headers,
        }
        print(folderIds)
        data = {k: v for k, v in data.items() if v is not None}

        result = self._make_request("post", "/api/item/addFromUrls", data=data)
        if result and result.get("status") == "success":
            print("addFromURL successfully.")
            return True
        return False

    def create_folder(
        self, folder_name: str, parent: Optional[str] = None
    ) -> Optional[str]:
        """
        创建文件夹
        """
        data = {"folderName": folder_name}
        if parent:
            data["parent"] = parent
        else:
            data["parent"] = self.root_folder_id

        result = self._make_request("post", "/api/folder/create", data=data)
        if result and result.get("status") == "success":
            folder_data = result["data"][0]  # 获取列表中的第一个文件夹
            print(folder_data)
            folder_id = folder_data.get("id")
            print(f"Folder '{folder_name}' created successfully. ID: {folder_id}")
            return folder_id
        return None

    def update_item(
        self,
        item_id: str,
        tags: Optional[List[str]] = None,
        annotation: Optional[str] = None,
        new_url: Optional[str] = None,
        star: Optional[bool] = None,
        name: Optional[str] = None,
        folders: Optional[List[str]] = None,
    ) -> bool:
        """
        更新项目
        """
        data = {
            "id": item_id,
            "tags": tags,
            "annotation": annotation,
            "url": new_url,
            "star": star,
            "name": name,
            "folders": folders,
            "tag_mode": name,
        }
        data = {k: v for k, v in data.items() if v is not None}

        result = self._make_request(
            "post", "/api/item/update", is_item_api=True, data=data
        )
        if result and result.get("status") == "success":
            print(f"Item {item_id} updated successfully.")
            return True
        return False

    def get_items(
        self, limit: int = 100000, orderBy: str = "NAME", ext: str = ""
    ) -> Optional[List[Dict]]:
        """
        获取项目列表
        """
        params = {"limit": limit, "orderBy": orderBy, "exts": [ext]}
        result = self._make_request("post", "/api/item/list", params=params)
        if result and result.get("status") == "success":
            return result.get("data")
        return None

    def get_folder_list_recursive(
        self,
    ) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str]]:
        """
        获取文件夹结构
        返回: (folder_id_to_name, folder_name_to_id, folder_to_root)
        """
        data = {}
        result = self._make_request("post", "/api/folder/list", data=data)
        if not result or result.get("status") != "success":
            return {}, {}, {}

        folders = result.get("data", []) or []
        folder_id_to_name = {}
        folder_name_to_id = {}
        folder_to_root = {}

        stack = [(folder, None) for folder in folders]  # (folder, root_id)

        while stack:
            folder, root_id = stack.pop()
            folder_id = folder.get("id")
            folder_name = folder.get("name")

            folder_id_to_name[folder_id] = folder_name
            folder_name_to_id[folder_name] = folder_id

            current_root = root_id if root_id else folder_id
            folder_to_root[folder_id] = current_root

            children = folder.get("children", [])
            for child in children:
                stack.append((child, current_root))

        return folder_id_to_name, folder_name_to_id, folder_to_root

    def get_folders_by_root_id(
        self, root_id: str, folder_to_root: Dict[str, str]
    ) -> List[str]:
        """获取指定根文件夹下的所有文件夹ID"""
        return [fid for fid, rid in folder_to_root.items() if rid == root_id]

    def get_folder_name_by_id(
        self, folder_id: str, folder_id_to_name: Dict[str, str]
    ) -> str:
        """获取文件夹名称"""
        return folder_id_to_name.get(folder_id, "Folder not found")
