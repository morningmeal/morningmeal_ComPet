# core/config_manager.py
import os
import sys
import json
import uuid
import shutil

def get_bundle_dir():
    """PyInstaller 번들 내부 또는 소스 코드 루트 경로 반환"""
    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            return sys._MEIPASS
        exe_dir = os.path.dirname(sys.executable)
        internal_dir = os.path.join(exe_dir, "_internal")
        if os.path.exists(internal_dir):
            return internal_dir
        if sys.platform == 'darwin':
            res_dir = os.path.join(os.path.dirname(exe_dir), "Resources")
            if os.path.exists(res_dir):
                return res_dir
        return exe_dir
    else:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BUNDLE_DIR = get_bundle_dir()

# 사용자 데이터 저장소: morningmeal_ComPet
if sys.platform == 'darwin':
    USER_DATA_DIR = os.path.expanduser("~/Library/Application Support/morningmeal_ComPet")
else:
    USER_DATA_DIR = os.path.join(os.path.expanduser("~"), ".morningmeal_ComPet")

CONFIG_PATH = os.path.join(USER_DATA_DIR, "config.json")
SKINS_DIR = os.path.join(USER_DATA_DIR, "skins")
USER_SOUNDS_DIR = os.path.join(USER_DATA_DIR, "sounds")
CRASH_LOG_PATH = os.path.join(USER_DATA_DIR, "crash_log.txt")

BUNDLE_SKINS_DIR = os.path.join(BUNDLE_DIR, "assets", "skins")
BUNDLE_SOUNDS_DIR = os.path.join(BUNDLE_DIR, "assets", "sounds")

DEFAULT_CONFIG = {
    "settings": {
        "language": "auto",
        "dark_mode": False,
        "tray_mode": False,
        "click_through": False,
        "clamp_to_screen": True,
        "magnetic_snap": True,
        "snap_distance": 15
    },
    "sound": {
        "key_sound_enabled": True,
        "key_volume": 50,
        "key_sound_path": "",
        "click_sound_enabled": True,
        "click_volume": 50,
        "click_sound_path": ""
    },
    "groups": {
        "기본 그룹": ["", "", ""]
    },
    "timers": [
        {
            "id": str(uuid.uuid4()),
            "name": "작업 1",
            "group": "기본 그룹",
            "idle_timeout": 5,
            "elapsed_seconds": 0,
            "x": 200,
            "y": 300,
            "paused": False
        }
    ],
    "pets": []
}

class ConfigManager:
    def __init__(self):
        self._ensure_dirs()
        self.config = self.load_config()

    def _ensure_dirs(self):
        os.makedirs(USER_DATA_DIR, exist_ok=True)
        os.makedirs(SKINS_DIR, exist_ok=True)
        os.makedirs(USER_SOUNDS_DIR, exist_ok=True)

        default_user_skin = os.path.join(SKINS_DIR, "default")
        bundle_default_skin = os.path.join(BUNDLE_SKINS_DIR, "default")

        if not os.path.exists(default_user_skin):
            if os.path.exists(bundle_default_skin):
                shutil.copytree(bundle_default_skin, default_user_skin)
            else:
                os.makedirs(default_user_skin, exist_ok=True)
                self.save_skin_config("default", {
                    "name": "default",
                    "squash_depth": 0.20,
                    "idle_image": "idle.png",
                    "tap_images": ["tap_left.png", "tap_right.png"],
                    "key_mappings": {}
                })

    def load_config(self):
        data = json.loads(json.dumps(DEFAULT_CONFIG))
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    for k, v in loaded.items():
                        if isinstance(v, dict) and k in data:
                            data[k].update(v)
                        else:
                            data[k] = v
            except Exception as e:
                print(f"[ConfigManager] Load error: {e}")

        # 기본 펫 인스턴스가 없을 경우 1마리 기본 생성
        if not data.get("pets"):
            first_timer_id = data["timers"][0]["id"] if data.get("timers") else ""
            data["pets"].append({
                "id": str(uuid.uuid4()),
                "skin": "default",
                "scale": 1.0,
                "x": 200,
                "y": 200,
                "bound_timer_id": first_timer_id
            })
        return data

    def save_config(self):
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[ConfigManager] Save error: {e}")

    def get_skin_config(self, skin_name):
        path = os.path.join(SKINS_DIR, skin_name, "config.json")
        conf = {
            "name": skin_name,
            "squash_depth": 0.20,
            "idle_image": "idle.png",
            "tap_images": ["tap_left.png", "tap_right.png"],
            "key_mappings": {}
        }
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    conf.update(json.load(f))
            except Exception:
                pass
        return conf

    def save_skin_config(self, skin_name, data):
        target_dir = os.path.join(SKINS_DIR, skin_name)
        os.makedirs(target_dir, exist_ok=True)
        path = os.path.join(target_dir, "config.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[ConfigManager] Skin config save error for {skin_name}: {e}")

config_mgr = ConfigManager()