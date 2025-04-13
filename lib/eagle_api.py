import requests
from typing import Dict, List, Optional, Tuple, Any

class EagleAPI:
    def __init__(self):
        """
        初始化 Eagle API 客户端
        保留原始的两个不同端口：
        - 41595 用于文件夹和项目列表操作
        - 41695 用于项目添加和更新操作
        """
        self.base_url_item = "http://localhost:41695"  # 项目操作端口
        self.base_url_folder = "http://localhost:41595"  # 文件夹操作端口
        self.headers = {"Content-Type": "application/json"}

    def _make_request(self, method: str, endpoint: str, 
                     is_item_api: bool = False,
                     data: Optional[Dict] = None, 
                     params: Optional[Dict] = None) -> Optional[Dict]:
        """
        内部请求方法
        :param method: HTTP 方法 ('get' 或 'post')
        :param endpoint: API 端点
        :param is_item_api: 是否使用项目API端口(41695)
        :param data: 请求数据
        :param params: 查询参数
        :return: 响应数据字典或 None
        """
        base_url = self.base_url_item if is_item_api else self.base_url_folder
        url = f"{base_url}{endpoint}"
        
        try:
            if method.lower() == 'get':
                response = requests.get(url, params=params, headers=self.headers)
            else:
                response = requests.post(url, json=data, headers=self.headers)

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error in {method.upper()} request to {url}. "
                      f"Status code: {response.status_code}, Response: {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Request failed for {url}: {str(e)}")
            return None

    def add_from_url(self, img_url: str, name: str, 
                    website: Optional[str] = None, 
                    tags: Optional[List[str]] = None, 
                    annotation: Optional[str] = None, 
                    modificationTime: Optional[str] = None, 
                    folderIds: Optional[List[str]] = None, 
                    headers: Optional[Dict] = None) -> bool:
        """
        从 URL 添加项目 (使用 41695 端口)
        """
        data = {
            "url": img_url,
            "name": name,
            "website": website,
            "tags": tags,
            "annotation": annotation,
            "modificationTime": modificationTime,
            "folderIds": folderIds,
            "headers": headers
        }
        data = {k: v for k, v in data.items() if v is not None}
        
        result = self._make_request('post', '/api/item/addFromURL', is_item_api=True, data=data)
        if result and result.get("status") == "success":
            print("addFromURL successfully.")
            return True
        return False

    def create_folder(self, folder_name: str, parent: Optional[str] = None) -> Optional[str]:
        """
        创建文件夹 (使用 41595 端口)
        """
        data = {"folderName": folder_name}
        if parent:
            data["parent"] = parent

        result = self._make_request('post', '/api/folder/create', data=data)
        if result and result.get("status") == "success":
            folder_id = result.get("data", {}).get("id")
            print(f"Folder '{folder_name}' created successfully. ID: {folder_id}")
            return folder_id
        return None

    def update_item(self, item_id: str, 
                   tags: Optional[List[str]] = None, 
                   annotation: Optional[str] = None, 
                   new_url: Optional[str] = None, 
                   star: Optional[bool] = None, 
                   name: Optional[str] = None, 
                   folders: Optional[List[str]] = None) -> bool:
        """
        更新项目 (使用 41695 端口)
        """
        data = {
            "id": item_id,
            "tags": tags,
            "annotation": annotation,
            "url": new_url,
            "star": star,
            "name": name,
            "folders": folders
        }
        data = {k: v for k, v in data.items() if v is not None}

        result = self._make_request('post', '/api/item/update', is_item_api=True, data=data)
        if result and result.get("status") == "success":
            print(f"Item {item_id} updated successfully.")
            return True
        return False

    def get_items(self, limit: int = 100000, orderBy: str = "NAME", ext: str = "") -> Optional[List[Dict]]:
        """
        获取项目列表 (使用 41595 端口)
        """
        params = {
            "limit": limit,
            "orderBy": orderBy,
            "ext": ext
        }
        result = self._make_request('get', '/api/item/list', params=params)
        if result and result.get("status") == "success":
            return result.get("data")
        return None

    def get_folder_list_recursive(self) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str]]:
        """
        获取文件夹结构 (使用 41595 端口)
        返回: (folder_id_to_name, folder_name_to_id, folder_to_root)
        """
        result = self._make_request('get', '/api/folder/list')
        if not result or result.get("status") != "success":
            return {}, {}, {}

        folders = result.get("data", [])
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

    def get_folders_by_root_id(self, root_id: str, folder_to_root: Dict[str, str]) -> List[str]:
        """获取指定根文件夹下的所有文件夹ID"""
        return [fid for fid, rid in folder_to_root.items() if rid == root_id]

    def get_folder_name_by_id(self, folder_id: str, folder_id_to_name: Dict[str, str]) -> str:
        """获取文件夹名称"""
        return folder_id_to_name.get(folder_id, "Folder not found")