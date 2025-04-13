import wd_tagger
from PIL import Image
import requests


def get_items():
    url = "http://localhost:41595/api/item/list"
    params = {
        "limit": 10000,
        "orderBy": "NAME",
        "ext": "png"
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

# Dataset v3 series of models:
SWINV2_MODEL_DSV3_REPO = "SmilingWolf/wd-swinv2-tagger-v3"
CONV_MODEL_DSV3_REPO = "SmilingWolf/wd-convnext-tagger-v3"
VIT_MODEL_DSV3_REPO = "SmilingWolf/wd-vit-tagger-v3"

Predictor = wd_tagger.Predictor()

sorted_general_strings, rating, character_res, general_res = Predictor.predict(
    image=Image.open("D:\AI Image.library\images\LULK8AH4PMNKE.info\臭いフェチ 约稿【托帕奶牛装营业】 - afei的插画.jpg").convert("RGBA"),
    model_repo=VIT_MODEL_DSV3_REPO,
    general_thresh=0.5,
    general_mcut_enabled=False,
    character_thresh=0.3,
    character_mcut_enabled=False)

characters = character_res.keys()

print(max(rating, key=rating.get))
print(list(character_res.keys()))
print(list(general_res.keys()))

# for character in characters:
#     if character in folder_name_to_id

# items_data = get_items()