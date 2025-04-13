import os
import re
import shutil

from PIL import Image

from lib import eagle_api
import wd_tagger

import tag_groups

destination_folder = "D:/train/20241008_1/"
eagle_folder = "D:/AI Image.library/images/"
artist_prefix = ""


def train_tag_generate():
    # 创建目标文件夹（如果不存在）
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

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

            artists = []
            year = []
            image_type = []
            character = []
            count = []
            rating = []

            tags_export1 = []
            tags_export2 = []

            tags = item.get("tags", [])
            folder_ids = item.get("folders", [])

            if folder_name_to_id["export_69"] in folder_ids:
                # if True:
                for folder_id in folder_ids:
                    match eagle_api.get_folder_name_by_id(folder_to_root[folder_id], folder_id_to_name):
                        case "Artist":
                            artists.append(
                                artist_prefix + eagle_api.get_folder_name_by_id(folder_id, folder_id_to_name))
                        case "Year":
                            year.append(eagle_api.get_folder_name_by_id(folder_id, folder_id_to_name))
                        case "Type":
                            image_type.append(eagle_api.get_folder_name_by_id(folder_id, folder_id_to_name))
                        case "Character":
                            character.append(eagle_api.get_folder_name_by_id(folder_id, folder_id_to_name))
                        case "Count":
                            count.append(eagle_api.get_folder_name_by_id(folder_id, folder_id_to_name))
                        case "Rating":
                            rating.append(eagle_api.get_folder_name_by_id(folder_id, folder_id_to_name))

                # 控制标签排序
                tags_export1.extend(count)
                tags_export1.extend(character)
                # tags_export1.extend(rating)
                tags_export1.extend(artists)
                # tags_export1.extend(["Ilikara_style1"])
                # tags_export1.extend(year)
                tags_export1.extend(tags)

                # tags_export2.extend(count)
                # tags_export2.extend(character)
                # tags_export2.extend(rating)
                # tags_export2.extend(artists)
                # tags_export2.extend(year)
                tags_export2[:] = [tag for tag in tags if tag in tag_groups.view_angle]
                tags_export2.extend(["69"])
                tags_export2.extend(count)
                tags_export2.extend(character)
                tags_export2.extend(artists)
                if tags_export1:
                    # 将文件复制到目标文件夹
                    source_file = eagle_folder + id + ".info/" + name + '.' + ext
                    destination_file = destination_folder + str(i) + '.' + ext
                    shutil.copy(source_file, destination_file)

                    # 创建同名文本文件
                    text_file_path = os.path.join(destination_folder, f"{str(i)}.txt")
                    with open(text_file_path, "w", encoding="utf-8") as text_file:
                        formatted_folders_str = ", ".join(tags_export1)
                        text_file.write(formatted_folders_str.replace('_', ' '))
                    print(i)
                    i = i + 1

                if tags_export2:
                    # 将文件复制到目标文件夹
                    source_file = eagle_folder + id + ".info/" + name + '.' + ext
                    destination_file = destination_folder + str(i) + '.' + ext
                    shutil.copy(source_file, destination_file)

                    # 创建同名文本文件
                    text_file_path = os.path.join(destination_folder, f"{str(i)}.txt")
                    with open(text_file_path, "w", encoding="utf-8") as text_file:
                        formatted_folders_str = ", ".join(tags_export2)
                        text_file.write(formatted_folders_str.replace('_', ' '))
                    print(i)
                    i = i + 1

                    # # 将文件复制到目标文件夹
                    # source_file = eagle_folder + id + ".info/" + name + '.' + ext
                    # destination_file = destination_folder + str(i) + '.' + ext
                    # shutil.copy(source_file, destination_file)
                    #
                    # # 创建同名文本文件
                    # text_file_path = os.path.join(destination_folder, f"{str(i)}.txt")
                    # with open(text_file_path, "w", encoding="utf-8") as text_file:
                    #     formatted_folders_str = ", ".join(tags_export1)
                    #     text_file.write("Ilikara_style1")
                    # print(i)
                    # i = i + 1

                    # tags_export3 = []
                    # for character_tag in character:
                    #     if character_tag not in native_tags.copyrights and character_tag in native_tags.tags:
                    #         tags_export3.extend([tag for tag in tags_export1 if tag not in native_tags.tags[character_tag]])
                    # # 将文件复制到目标文件夹
                    # source_file = eagle_folder + id + ".info/" + name + '.' + ext
                    # destination_file = destination_folder + str(i) + '.' + ext
                    # shutil.copy(source_file, destination_file)
                    #
                    # # 创建同名文本文件
                    # text_file_path = os.path.join(destination_folder, f"{str(i)}.txt")
                    # with open(text_file_path, "w", encoding="utf-8") as text_file:
                    #     formatted_folders_str = ", ".join(tags_export3)
                    #     text_file.write(formatted_folders_str.replace('_', ' '))
                    # print(i)
                    # i = i + 1


def auto_tagger():
    items_data = eagle_api.get_items()
    folder_id_to_name, folder_name_to_id, folder_to_root = eagle_api.get_folder_list_recursive()
    print(folder_id_to_name)
    if items_data:
        # 进一步处理“items_data”
        print("成功提取数据！")
        for item in items_data:
            # 提取tags和folders
            id = item.get("id", [])
            name = item.get("name", [])
            ext = item.get("ext", [])
            tags = item.get("tags", [])
            folder_ids = item.get("folders", [])

            if folder_name_to_id["wd-tagger"] in folder_ids:

                SWINV2_MODEL_DSV3_REPO = "SmilingWolf/wd-swinv2-tagger-v3"
                CONV_MODEL_DSV3_REPO = "SmilingWolf/wd-convnext-tagger-v3"
                VIT_MODEL_DSV3_REPO = "SmilingWolf/wd-vit-tagger-v3"

                Predictor = wd_tagger.Predictor()

                sorted_general_strings, rating, character_res, general_res = Predictor.predict(
                    image=Image.open(eagle_folder + id + ".info/" + name + '.' + ext).convert("RGBA"),
                    model_repo=VIT_MODEL_DSV3_REPO,
                    general_thresh=0.35,
                    general_mcut_enabled=False,
                    character_thresh=0.85,
                    character_mcut_enabled=True
                )

                # Eagle暂无修改所属文件夹api

                characters = character_res.keys()
                characters = [re.sub(r'\s', '_', character) for character in characters]
                for character in characters.copy():
                    if character not in folder_name_to_id:
                        eagle_api.create_folder(character, folder_name_to_id["new_Character"])
                #     characters.remove(character)
                #     folder_ids = list(set(folder_ids + [folder_name_to_id[character]]))
                #
                # folder_ids = list(set(folder_ids + [folder_name_to_id[max(rating, key=rating.get)]]))
                tags = list(set(tags + [max(rating, key=rating.get)]))

                tags = list(set(tags + list(general_res.keys()) + list(character_res.keys())))
                tags = [re.sub(r'\s', '_', tag) for tag in tags]
                # for tag in tags.copy():
                #     if tag in folder_name_to_id:
                #         tags.remove(tag)
                #         folder_ids = list(set(folder_ids + [folder_name_to_id[tag]]))
                if "" in tags:
                    tags.remove("")
                print(tags)

                eagle_api.update_item(
                    id,
                    tags=tags
                )

                # for character in characters:
                #     if character in folder_name_to_id


if __name__ == "__main__":
    train_tag_generate()
    # auto_tagger()
