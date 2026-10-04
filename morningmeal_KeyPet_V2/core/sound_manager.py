# core/config_manager.py
import os
import sys
import json
import uuid
import shutil

def get_bundle_dir():
    """PyInstaller 번들 내부의 읽기 전용 에셋 루트 경로를 안전하게 반환"""
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

# 사용자 데이터 디렉터리
if sys.platform == 'darwin':
    USER_DATA_DIR = os.path.expanduser("~/Library/Application Support/morningmeal_Compet")
else:
    USER_DATA_DIR = os.path.join(os.path.expanduser("~"), ".morningmeal_Compet")

SKINS_DIR = os.path.join(USER_DATA_DIR, "skins")
GLOBAL_CONFIG = os.path.join(USER_DATA_DIR, "settings.json")
CRASH_LOG_PATH = os.path.join(USER_DATA_DIR, "crash_log.txt")

ASSETS_DIR = os.path.join(BUNDLE_DIR, "assets", "sounds")
BUNDLE_SKINS_DIR = os.path.join(BUNDLE_DIR, "skins")

class ConfigManager:
    def __init__(self):
        self._ensure_dirs()
        self.settings = self.load_global_settings()

    def _ensure_dirs(self):
        """필요한 사용자 디렉터리를 생성하고 기본 번들 스킨을 복사"""
        os.makedirs(USER_DATA_DIR, exist_ok=True)
        os.makedirs(SKINS_DIR, exist_ok=True)

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

    def load_global_settings(self):
        """전역 설정 파일(settings.json) 로드 및 기본값 초기화"""
        default_settings = {
            "language": "auto",
            "tray_mode": False,
            "click_through": False,
            "lock_position": False,
            "clamp_to_screen": True,
            "enable_bounce_animation": True,  # ★ 압축(바운스) 애니메이션 활성화 옵션
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
                    loaded = json.load(f)
                    default_settings.update(loaded)
            except Exception:
                pass
        
        if not default_settings["instances"]:
            default_settings["instances"].append({
                "id": str(uuid.uuid4()),
                "skin": "default",
                "scale": 1.0,
                "x": 100,
                "y": 100
            })
        return default_settings

    def save_global_settings(self):
        """전역 설정을 settings.json에 저장"""
        try:
            with open(GLOBAL_CONFIG, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[ConfigManager] Failed to save settings: {e}")

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
                    data = json.load(f)
                    conf.update(data)
                    if "squash_depth" not in data and "bounce_stiffness" in data:
                        conf["squash_depth"] = 0.20
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
            print(f"[ConfigManager] Failed to save skin config for {skin_name}: {e}")

config_mgr = ConfigManager()