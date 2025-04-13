import os
import re
import shutil
from typing import List, Dict, Optional, Tuple
from pathlib import Path

from PIL import Image
from lib.eagle_api import EagleAPI
import wd_tagger
import tag_groups

class ImageTrainer:
    def __init__(self):
        self.eagle = EagleAPI()
        self.destination_folder = Path("D:/train/20241008_1/")
        self.eagle_folder = Path("D:/AI Image.library/images/")
        self.artist_prefix = ""
        
        # 确保目标文件夹存在
        self.destination_folder.mkdir(parents=True, exist_ok=True)

    def _get_folder_mappings(self) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str]]:
        """获取文件夹映射关系"""
        return self.eagle.get_folder_list_recursive()

    def _process_folders(self, folder_ids: List[str], 
                        folder_id_to_name: Dict[str, str],
                        folder_to_root: Dict[str, str]) -> Dict[str, List[str]]:
        """
        处理文件夹分类
        返回: {
            "artists": [],
            "year": [],
            "image_type": [],
            "character": [],
            "count": [],
            "rating": []
        }
        """
        categories = {
            "Artist": "artists",
            "Year": "year",
            "Type": "image_type",
            "Character": "character",
            "Count": "count",
            "Rating": "rating"
        }
        
        result = {v: [] for v in categories.values()}
        
        for folder_id in folder_ids:
            root_folder_name = self.eagle.get_folder_name_by_id(
                folder_to_root[folder_id], folder_id_to_name
            )
            
            if root_folder_name in categories:
                folder_name = self.eagle.get_folder_name_by_id(folder_id, folder_id_to_name)
                if root_folder_name == "Artist":
                    folder_name = self.artist_prefix + folder_name
                result[categories[root_folder_name]].append(folder_name)
                
        return result

    def _write_tags_to_file(self, file_path: Path, tags: List[str]) -> None:
        """将标签写入文本文件"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(", ".join(tag.replace('_', ' ') for tag in tags))

    def _copy_image_with_tags(self, 
                            source_path: Path, 
                            dest_stem: str,
                            tags_list: List[List[str]]) -> int:
        """
        复制图片并生成标签文件
        返回: 生成的文件计数
        """
        count = 0
        ext = source_path.suffix
        
        for i, tags in enumerate(tags_list, start=1):
            if not tags:
                continue
                
            dest_path = self.destination_folder / f"{dest_stem}_{i}{ext}"
            shutil.copy(source_path, dest_path)
            
            txt_path = dest_path.with_suffix(".txt")
            self._write_tags_to_file(txt_path, tags)
            
            count += 1
            print(f"Processed {dest_path}")
            
        return count

    def train_tag_generate(self) -> None:
        """生成训练标签"""
        items_data = self.eagle.get_items()
        if not items_data:
            print("No items data found!")
            return
            
        folder_id_to_name, folder_name_to_id, folder_to_root = self._get_folder_mappings()
        print(f"Total items: {len(items_data)}")
        
        export_folder_id = folder_name_to_id.get("export_69")
        if not export_folder_id:
            print("'export_69' folder not found!")
            return
            
        i = 1
        for item in items_data:
            item_id = item.get("id", [])
            name = item.get("name", [])
            ext = item.get("ext", [])
            tags = item.get("tags", [])
            folder_ids = item.get("folders", [])
            
            if export_folder_id not in folder_ids:
                continue
                
            # 处理文件夹分类
            folder_data = self._process_folders(folder_ids, folder_id_to_name, folder_to_root)
            
            # 准备标签组合
            tags_export1 = [
                *folder_data["count"],
                *folder_data["character"],
                *folder_data["artists"],
                *tags
            ]
            
            tags_export2 = [
                *[tag for tag in tags if tag in tag_groups.view_angle],
                "69",
                *folder_data["count"],
                *folder_data["character"],
                *folder_data["artists"]
            ]
            
            # 源文件路径
            source_path = self.eagle_folder / f"{item_id}.info" / f"{name}.{ext}"
            if not source_path.exists():
                print(f"Source file not found: {source_path}")
                continue
                
            # 复制文件并生成标签
            generated = self._copy_image_with_tags(
                source_path,
                str(i),
                [tags_export1, tags_export2]
            )
            
            i += generated

    def auto_tagger(self) -> None:
        """自动标签处理（包含文件夹分类）"""
        items_data = self.eagle.get_items()
        if not items_data:
            print("No items data found!")
            return
            
        folder_id_to_name, folder_name_to_id, folder_to_root = self._get_folder_mappings()
        wd_tagger_folder_id = folder_name_to_id.get("OvO")
        
        if not wd_tagger_folder_id:
            print("'wd-tagger' folder not found!")
            return
            
        # 定义需要处理的分类文件夹映射
        category_folders = {
            "rating": "Rating",
            "character": "Character",
        }
        
        # 获取或创建根分类文件夹ID
        root_category_ids = {}
        for category, folder_name in category_folders.items():
            if folder_name not in folder_name_to_id:
                created_id = self.eagle.create_folder(folder_name)
                if created_id:
                    folder_name_to_id[folder_name] = created_id
                    folder_id_to_name[created_id] = folder_name
            root_category_ids[category] = folder_name_to_id.get(folder_name)

        predictor = wd_tagger.Predictor()
        model_repo = "SmilingWolf/wd-vit-tagger-v3"
        
        for item in items_data:
            item_id = item.get("id")
            name = item.get("name")
            ext = item.get("ext")
            current_tags = item.get("tags", [])
            current_folders = item.get("folders", [])
            
            if wd_tagger_folder_id not in current_folders:
                continue
                
            # 图像路径
            image_path = self.eagle_folder / f"{item_id}.info" / f"{name}.{ext}"
            if not image_path.exists():
                print(f"Image not found: {image_path}")
                continue
                
            try:
                # 预测标签
                with Image.open(image_path).convert("RGBA") as img:
                    _, rating, character_res, general_res = predictor.predict(
                        image=img,
                        model_repo=model_repo,
                        general_thresh=0.35,
                        general_mcut_enabled=False,
                        character_thresh=0.85,
                        character_mcut_enabled=True
                    )
                    
                # 处理评分标签
                rating_tag = max(rating, key=rating.get)
                rating_folder_name = rating_tag
                
                # 处理角色标签
                characters = [re.sub(r'\s', '_', c) for c in character_res.keys()]
                
                # 处理普通标签
                general_tags = [re.sub(r'\s', '_', tag) for tag in general_res.keys()]
                
                # 准备要添加的新文件夹
                new_folders = current_folders.copy()
                
                # 1. 处理评分文件夹
                if root_category_ids["rating"]:
                    rating_folder_id = folder_name_to_id.get(rating_folder_name)
                    if not rating_folder_id:
                        rating_folder_id = self.eagle.create_folder(rating_folder_name, root_category_ids["rating"])
                        if rating_folder_id:
                            folder_name_to_id[rating_folder_name] = rating_folder_id
                            folder_id_to_name[rating_folder_id] = rating_folder_name
                    
                    if rating_folder_id and rating_folder_id not in new_folders:
                        new_folders.append(rating_folder_id)
                
                # 2. 处理角色文件夹
                if root_category_ids["character"]:
                    for character in characters:
                        if character not in folder_name_to_id:
                            char_folder_id = self.eagle.create_folder(character, root_category_ids["character"])
                            if char_folder_id:
                                folder_name_to_id[character] = char_folder_id
                                folder_id_to_name[char_folder_id] = character
                        
                        char_folder_id = folder_name_to_id.get(character)
                        if char_folder_id and char_folder_id not in new_folders:
                            new_folders.append(char_folder_id)
                
                # 合并所有标签
                new_tags = list(set(
                    [*current_tags, *general_tags]
                ))
                # 移除空标签
                new_tags = [tag for tag in new_tags if tag]
                
                # 更新项目（标签和文件夹）
                self.eagle.update_item(
                    item_id,
                    tags=new_tags,
                    folders=list(set(new_folders))  # 确保文件夹ID唯一
                )
                
                print(f"Updated item {item_id}:")
                print(f" - Tags: {new_tags}")
                print(f" - Folders: {[folder_id_to_name.get(fid, 'Unknown') for fid in new_folders]}")
                
            except Exception as e:
                print(f"Error processing {image_path}: {str(e)}")


if __name__ == "__main__":
    trainer = ImageTrainer()
    # trainer.train_tag_generate()  # 生成训练标签
    trainer.auto_tagger()  # 自动标签处理