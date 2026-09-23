# core/config_manager.py
import os
import sys
import json
import uuid

if getattr(sys, 'frozen', False):
    if sys.platform == 'darwin':
        APP_DIR = os.path.dirname(os.path.dirname(os.path.dirname(sys.executable))) 
    else:
        APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if sys.platform == 'darwin':
    USER_DATA_DIR = os.path.expanduser("~/Library/Application Support/morningmeal_Compet")
else:
    USER_DATA_DIR = APP_DIR

SKINS_DIR = os.path.join(USER_DATA_DIR, "skins")
GLOBAL_CONFIG = os.path.join(USER_DATA_DIR, "settings.json")
CRASH_LOG_PATH = os.path.join(USER_DATA_DIR, "crash_log.txt")

ASSETS_DIR = os.path.join(APP_DIR, "assets", "sounds")
PRESETS_DIR = os.path.join(ASSETS_DIR, "presets")

class ConfigManager:
    def __init__(self):
        self._ensure_dirs()
        self.settings = self.load_global_settings()

    def _ensure_dirs(self):
        os.makedirs(USER_DATA_DIR, exist_ok=True)
        os.makedirs(SKINS_DIR, exist_ok=True)
        os.makedirs(PRESETS_DIR, exist_ok=True)
        
        default_skin_dir = os.path.join(SKINS_DIR, "default")
        if not os.path.exists(default_skin_dir):
            os.makedirs(default_skin_dir)
            self.save_skin_config("default", {"squash_depth": 0.20})

    def load_global_settings(self):
        default_settings = {
            "language": "auto",
            "tray_mode": False,
            "click_through": False,
            "lock_position": False,
            "key_sound_enabled": True,
            "key_volume": 50,
            "key_preset": "preset_default",
            "key_sound_path": "",
            "click_sound_enabled": True,
            "click_volume": 50,
            "click_preset": "preset_default",
            "click_sound_path": "",
            "mac_permission_shown": False,
            "instances": []
        }
        if os.path.exists(GLOBAL_CONFIG):
            try:
                with open(GLOBAL_CONFIG, "r", encoding="utf-8") as f:
                    default_settings.update(json.load(f))
            except: pass
        
        if not default_settings["instances"]:
            default_settings["instances"].append({
                "id": str(uuid.uuid4()), "skin": "default", "scale": 1.0, "x": 100, "y": 100
            })
        return default_settings

    def save_global_settings(self):
        with open(GLOBAL_CONFIG, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, indent=4, ensure_ascii=False)

    def get_skin_config(self, skin_name):
        path = os.path.join(SKINS_DIR, skin_name, "config.json")
        conf = {
            "squash_depth": 0.20,
            "key_mappings": {},
            "tap_images": ["tap_left.png", "tap_right.png"],
            "idle_image": "idle.png"
        }
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    conf.update(data)
                    # 이전 버전 호환 (bounce_stiffness만 있고 squash_depth가 없는 경우)
                    if "squash_depth" not in data and "bounce_stiffness" in data:
                        conf["squash_depth"] = 0.20
            except: pass
        return conf

    def save_skin_config(self, skin_name, data):
        path = os.path.join(SKINS_DIR, skin_name, "config.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

config_mgr = ConfigManager()