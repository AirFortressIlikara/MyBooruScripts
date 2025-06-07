import os
import json
from typing import Dict

class ConfigManager:
    CONFIG_FILE = "danbooru_config.json"
    
    @classmethod
    def load_config(cls) -> Dict:
        """加载配置文件，如果不存在则创建"""
        if not os.path.exists(cls.CONFIG_FILE):
            default_config = {
                "danbooru": {
                    "username": "YOUR_USERNAME",
                    "api_key": "YOUR_API_KEY_HERE"
                }
            }
            with open(cls.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4)
            
            print(f"⚠️ 配置文件 {cls.CONFIG_FILE} 已自动创建，请修改其中的API key后再运行程序！")
            exit(1)
        
        with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

# 加载配置
config = ConfigManager.load_config()
