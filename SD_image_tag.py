import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from PIL import Image, PngImagePlugin, JpegImagePlugin
from lib.eagle_api import EagleAPI

class ImageMetadataProcessor:
    def __init__(self):
        self.eagle = EagleAPI()
        self.eagle_folder = Path("D:/AI Image.library/images/")
        self.artist_prefix = "artist:"
        
        # 支持的图像格式
        self.supported_extensions = {'.png', '.jpg', '.jpeg', '.webp'}
        
        # 预定义文件夹映射
        self.target_folders = {
            "new_ai": "new ai",
            "detected": "newaidetected",
            "nai3": "todonai3",
            "ai_generated": "AI Generated"
        }
        
        # 已知模型哈希
        self.novelai_model_hashes = {"c1e1de52", "8ba2af87", "7bccaa2c", "bc59c602", "79f47848", "7abffa2a"}

    def _get_folder_mappings(self) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str]]:
        """获取文件夹映射关系"""
        return self.eagle.get_folder_list_recursive()

    def create_folder_if_valid(self, category: str, folder_type: str, 
                             folder_name_to_id: Dict[str, str]) -> None:
        """
        创建文件夹的辅助函数
        :param category: 文件夹名称
        :param folder_type: 父文件夹类型名称
        :param folder_name_to_id: 文件夹名称到ID的映射
        """
        if category and category not in folder_name_to_id:
            parent_id = folder_name_to_id.get(folder_type)
            if parent_id:
                self.eagle.create_folder(category, parent_id)

    def _extract_model_info(self, metadata: dict) -> Union[str, int]:
        """
        从元数据中提取模型信息
        返回模型哈希或名称，找不到返回-1
        """
        # 优先处理EXIF-37510字段(UNICODE用户注释)
        if 'EXIF-37510' in metadata:
            metadata['EXIF-37510'] = metadata['EXIF-37510'].replace('\x00', '')
            if metadata['EXIF-37510'].startswith('UNICODE'):
                metadata['EXIF-37510'] = metadata['EXIF-37510'][len('UNICODE'):]  # 切片跳过前缀长度
            print(f"EXIF-37510 found: {repr(metadata['EXIF-37510'])}")

        # 其他字段的通用处理
        possible_fields = [
            ('parameters', r'Model hash:\s*([a-fA-F0-9]+)(?:,|\n|$)'),
            ('parameters', r'Stable Diffusion XL\s*([a-fA-F0-9]+)(?:,|\n|$)'),
            ('Comment', r'Model hash:\s*([a-fA-F0-9]+)(?:,|\n|$)'),
            ('Description', r'Model hash:\s*([a-fA-F0-9]+)(?:,|\n|$)'),
            ('Source', r'Stable Diffusion XL\s*([a-fA-F0-9]+)(?:,|\n|$)'),
            ('Source', r'NovelAI Diffusion V\d\s*([a-fA-F0-9]+)(?:,|\n|$)'),
            ('UserComment', r'Model hash:\s*([a-fA-F0-9]+)(?:,|\n|$)'),
        ]
        
        for field, pattern in possible_fields:
            if field in metadata:
                text = str(metadata[field])
                match = re.search(pattern, text)
                if match:
                    result = match.group(1).lower() if match.groups() else text
                    print(f"Found in {field}: {result}")
                    return result
        
        # 尝试从整个元数据中搜索
        combined_text = " ".join(str(v) for v in metadata.values())
        patterns = [
            r'Model hash:\s*([a-fA-F0-9]+)(?:,|\n|$)',
            r'"model_hash":"([a-fA-F0-9]+)(?:,|\n|$)"',
            r'model_hash["\']?\s*[:=]\s*["\']?([a-fA-F0-9]+)(?:,|\n|$)',
            r'Model:\s*([^\s,]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, combined_text)
            if match:
                result = match.group(1).lower()
                print(f"Found in combined text: {result}")
                return result
                
        return -1
    
    def is_metadata_empty(self, metadata) -> bool:
        """
        判断元数据是否为空或所有子项为空
        :param metadata: 元数据字典
        :return: True如果为空或所有子项为空，否则False
        """
        if not metadata:  # 元数据字典本身为空
            return True
        
        # 检查所有值是否为空
        for value in metadata.values():
            if value:  # 如果有任何一个值不为空
                return False
        return True
    
    def read_image_metadata(self, image_path: Path) -> Union[str, int]:
        """
        从图像文件中读取元数据
        返回模型哈希/名称，找不到返回-1
        """
        try:
            with Image.open(image_path) as img:
                metadata = {}
                
                # 处理PNG文件
                if isinstance(img, PngImagePlugin.PngImageFile):
                    for key, value in img.info.items():
                        if isinstance(value, (str, bytes)):
                            try:
                                if isinstance(value, bytes):
                                    value = value.decode('utf-8', errors='ignore')
                                metadata[key] = value
                            except UnicodeDecodeError:
                                continue
                
                # 处理JPEG文件
                elif isinstance(img, JpegImagePlugin.JpegImageFile):
                    if hasattr(img, '_getexif') and img._getexif():
                        exif = img._getexif()
                        for tag, value in exif.items():
                            if isinstance(value, (str, bytes)):
                                try:
                                    if isinstance(value, bytes):
                                        value = value.decode('utf-8', errors='ignore')
                                    metadata[f"EXIF-{tag}"] = value
                                except UnicodeDecodeError:
                                    continue
                
                # 尝试解析JSON格式的注释
                for key, value in metadata.copy().items():
                    if 'comment' in key.lower() or 'description' in key.lower():
                        try:
                            json_data = json.loads(value)
                            if isinstance(json_data, dict):
                                metadata.update(json_data)
                        except (json.JSONDecodeError, TypeError):
                            pass
                
                print(f"Metadata extracted: {metadata}")

                if self.is_metadata_empty(metadata):
                    return 'no_metadata'
                
                return self._extract_model_info(metadata)
                
        except Exception as e:
            print(f"Error reading metadata from {image_path}: {e}")
            return -1

    def process_ai_images(self) -> None:
        """处理所有AI生成的图片"""
        items_data = self.eagle.get_items()
        if not items_data:
            print("No items data found!")
            return
            
        folder_id_to_name, folder_name_to_id, _ = self._get_folder_mappings()
        print(f"Total items: {len(items_data)}")
        
        # 获取目标文件夹ID
        target_folder_ids = {
            key: folder_name_to_id.get(value) 
            for key, value in self.target_folders.items()
        }
        
        if not target_folder_ids["new_ai"]:
            print(f"Target folder '{self.target_folders['new_ai']}' not found!")
            return
            
        processed_count = 0
        for item in items_data:
            item_id = item.get("id")
            name = item.get("name")
            ext = item.get("ext", "").lower()
            folder_ids = item.get("folders", [])
            
            # 只处理支持的图像文件且在目标文件夹中的项目
            if f".{ext}" not in self.supported_extensions or target_folder_ids["new_ai"] not in folder_ids:
                continue
                
            # 构建文件路径
            source_file = self.eagle_folder / f"{item_id}.info" / f"{name}.{ext}"
            if not source_file.exists():
                print(f"File not found: {source_file}")
                continue
                
            print(f"\nProcessing {source_file}")
            
            # 读取模型信息
            model_info = self.read_image_metadata(source_file)
            print(f"Current folders: {[folder_id_to_name.get(fid, '?') for fid in folder_ids]}")
            print(f"Model info: {model_info}")
            
            # 更新文件夹
            new_folder_ids = set(folder_ids)
            
            if model_info == -1:
                print("No model info found")
            else:
                # 添加检测到的标记
                if target_folder_ids["detected"]:
                    new_folder_ids.add(target_folder_ids["detected"])
                
                # 特殊处理NAI3模型
                if isinstance(model_info, str) and model_info in self.novelai_model_hashes:
                    if target_folder_ids["nai3"]:
                        new_folder_ids.add(target_folder_ids["nai3"])
                
                # 创建模型文件夹并添加
                if isinstance(model_info, str):
                    self.create_folder_if_valid(model_info, self.target_folders["ai_generated"], folder_name_to_id)
                    # 刷新文件夹映射
                    _, folder_name_to_id, _ = self._get_folder_mappings()
                    model_folder_id = folder_name_to_id.get(model_info)
                    if model_folder_id:
                        new_folder_ids.add(model_folder_id)
            
            # 更新项目
            if new_folder_ids != set(folder_ids):
                self.eagle.update_item(
                    item_id, 
                    folders=list(new_folder_ids))
                processed_count += 1
                print(f"Updated folders for {item_id}")
        
        print(f"\nProcessing complete. {processed_count} items updated.")

if __name__ == "__main__":
    processor = ImageMetadataProcessor()
    processor.process_ai_images()