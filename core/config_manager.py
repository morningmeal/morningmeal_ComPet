# core/config_manager.py
import os
import sys
import json
import uuid
import shutil

# 1. 번들된 리소스(읽기 전용 에셋)가 위치한 루트 경로 계산
if getattr(sys, 'frozen', False):
    # PyInstaller로 패키징된 환경
    if hasattr(sys, '_MEIPASS'):
        BUNDLE_DIR = sys._MEIPASS
    else:
        if sys.platform == 'darwin':
            # macOS .app/Contents/MacOS -> .app/Contents/Resources
            BUNDLE_DIR = os.path.dirname(sys.executable)
        else:
            BUNDLE_DIR = os.path.dirname(sys.executable)
else:
    # 개발 중 로컬 소스 실행 환경
    BUNDLE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 2. 사용자 데이터(설정, 커스텀 스킨)가 저장될 디렉터리 (쓰기 가능 경로)
if sys.platform == 'darwin':
    USER_DATA_DIR = os.path.expanduser("~/Library/Application Support/morningmeal_Compet")
else:
    USER_DATA_DIR = os.path.join(os.path.expanduser("~"), ".morningmeal_Compet")

SKINS_DIR = os.path.join(USER_DATA_DIR, "skins")
GLOBAL_CONFIG = os.path.join(USER_DATA_DIR, "settings.json")
CRASH_LOG_PATH = os.path.join(USER_DATA_DIR, "crash_log.txt")

# 번들 리소스 경로
ASSETS_DIR = os.path.join(BUNDLE_DIR, "assets", "sounds")
BUNDLE_SKINS_DIR = os.path.join(BUNDLE_DIR, "skins")

class ConfigManager:
    def __init__(self):
        self._ensure_dirs()
        self.settings = self.load_global_settings()

    def _ensure_dirs(self):
        os.makedirs(USER_DATA_DIR, exist_ok=True)
        os.makedirs(SKINS_DIR, exist_ok=True)

        # 번들에 포함된 기본 스킨(default 등)을 사용자 스킨 폴더로 자동 복사
        default_user_skin = os.path.join(SKINS_DIR, "default")
        bundle_default_skin = os.path.join(BUNDLE_SKINS_DIR, "default")

        if not os.path.exists(default_user_skin):
            if os.path.exists(bundle_default_skin):
                shutil.copytree(bundle_default_skin, default_user_skin)
            else:
                os.makedirs(default_user_skin, exist_ok=True)
                self.save_skin_config("default", {
                    "squash_depth": 0.20,
                    "idle_image": "idle.png",
                    "tap_images": ["tap_left.png", "tap_right.png"],
                    "key_mappings": {}
                })

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
            except:
                pass
        
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
                    conf.update(json.load(f))
            except:
                pass
        return conf

    def save_skin_config(self, skin_name, data):
        path = os.path.join(SKINS_DIR, skin_name, "config.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

config_mgr = ConfigManager()