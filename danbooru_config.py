import json
from pathlib import Path
from typing import Dict, Any


class ConfigError(Exception):
    """自定义异常：配置文件错误或缺失。"""

    pass


class ConfigManager:
    CONFIG_FILE = Path("danbooru_config.json")

    @classmethod
    def load_config(cls) -> Dict[str, Any]:
        """
        加载配置文件。
        如果文件不存在，则自动创建默认模板并提示用户修改后重新运行。
        """
        if not cls.CONFIG_FILE.exists():
            default_config = {
                "danbooru": {
                    "username": "YOUR_USERNAME",
                    "api_key": "YOUR_API_KEY_HERE",
                }
            }

            try:
                with cls.CONFIG_FILE.open("w", encoding="utf-8") as f:
                    json.dump(default_config, f, indent=4, ensure_ascii=False)
                print(f"配置文件 '{cls.CONFIG_FILE}' 已自动创建。")
                print("请编辑该文件并填写正确的 API Key 后重新运行程序。")
            except OSError as e:
                raise ConfigError(f"无法创建配置文件：{e}") from e

            raise ConfigError("配置文件未完成，请更新后重试。")

        try:
            with cls.CONFIG_FILE.open("r", encoding="utf-8") as f:
                config = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            raise ConfigError(f"加载配置文件时出错：{e}") from e

        return config


try:
    config = ConfigManager.load_config()
except ConfigError as e:
    print(f"配置加载失败：{e}")
    config = {}
