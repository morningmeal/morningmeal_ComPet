import os
import sys
import json
import uuid

if sys.platform == 'darwin':
    USER_DATA_DIR = os.path.expanduser("~/Library/Application Support/morningmeal_Timer")
else:
    USER_DATA_DIR = os.path.join(os.path.expanduser("~"), ".morningmeal_Timer")

CONFIG_PATH = os.path.join(USER_DATA_DIR, "config.json")

DEFAULT_CONFIG = {
    "settings": {
        "language": "auto",
        "magnetic_snap": True,
        "snap_distance": 15,
        "dark_mode": False
    },
    "groups": {
        "Default": ["", "", ""]
    },
    "timers": [
        {
            "id": str(uuid.uuid4()),
            "name": "Task 1",
            "group": "Default",
            "idle_timeout": 5,
            "elapsed_seconds": 0,
            "x": 100,
            "y": 100,
            "paused": False
        }
    ]
}

class ConfigManager:
    def __init__(self):
        os.makedirs(USER_DATA_DIR, exist_ok=True)
        self.config = self.load_config()

    def load_config(self):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for k, v in DEFAULT_CONFIG.items():
                        if k not in data:
                            data[k] = v
                    return data
            except Exception as e:
                print(f"[Config] Load error: {e}")
        return json.loads(json.dumps(DEFAULT_CONFIG))

    def save_config(self):
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[Config] Save error: {e}")

config_mgr = ConfigManager()