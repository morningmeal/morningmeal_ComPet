# core/sound_manager.py
import os
import wave
from PyQt6.QtCore import QUrl
from PyQt6.QtMultimedia import QSoundEffect
from core.config_manager import config_mgr, USER_SOUNDS_DIR, BUNDLE_SOUNDS_DIR

SUPPORTED_EXTENSIONS = ('.wav',)

def scan_sound_files():
    """번들 기본 사운드 및 사용자 추가 사운드 디렉터리를 스캔하여 반환"""
    found_sounds = {}
    
    # 1. 번들 사운드 스캔
    if os.path.exists(BUNDLE_SOUNDS_DIR):
        for root, _, files in os.walk(BUNDLE_SOUNDS_DIR):
            for f in sorted(files):
                if f.lower().endswith(SUPPORTED_EXTENSIONS):
                    base_name = os.path.splitext(f)[0]
                    full_path = os.path.abspath(os.path.join(root, f))
                    rel_dir = os.path.relpath(root, BUNDLE_SOUNDS_DIR)
                    name = f"[{rel_dir}] {base_name}" if rel_dir != "." else base_name
                    found_sounds[name] = full_path

    # 2. 사용자 추가 사운드 스캔
    if os.path.exists(USER_SOUNDS_DIR):
        for root, _, files in os.walk(USER_SOUNDS_DIR):
            for f in sorted(files):
                if f.lower().endswith(SUPPORTED_EXTENSIONS):
                    base_name = os.path.splitext(f)[0]
                    full_path = os.path.abspath(os.path.join(root, f))
                    found_sounds[f"[User] {base_name}"] = full_path

    return found_sounds

class SoundManager:
    def __init__(self):
        self.key_pool = []
        self.click_pool = []
        self.key_idx = 0
        self.click_idx = 0
        self._initialized = False

    def ensure_initialized(self):
        """QApplication 생성 후 호출되어 풀을 초기화"""
        if self._initialized:
            return
        self.key_pool = [QSoundEffect() for _ in range(6)]
        self.click_pool = [QSoundEffect() for _ in range(4)]
        self._initialized = True
        self.load_sounds()

    def get_actual_path(self, prefix):
        snd_conf = config_mgr.config.get("sound", {})
        val = snd_conf.get(f"{prefix}_sound_path", "")
        if not val or val == "none":
            return ""

        if os.path.isabs(val) and os.path.exists(val) and val.lower().endswith('.wav'):
            return val

        candidate = os.path.join(USER_SOUNDS_DIR, val)
        if os.path.exists(candidate) and candidate.lower().endswith('.wav'):
            return os.path.abspath(candidate)

        candidate_bundle = os.path.join(BUNDLE_SOUNDS_DIR, val)
        if os.path.exists(candidate_bundle) and candidate_bundle.lower().endswith('.wav'):
            return os.path.abspath(candidate_bundle)

        scanned = scan_sound_files()
        if val in scanned:
            return scanned[val]

        return ""

    def load_sounds(self):
        if not self._initialized:
            return

        k_path = self.get_actual_path("key")
        c_path = self.get_actual_path("click")

        for player in self.key_pool:
            if k_path and os.path.exists(k_path):
                player.setSource(QUrl.fromLocalFile(k_path))
            else:
                player.setSource(QUrl())

        for player in self.click_pool:
            if c_path and os.path.exists(c_path):
                player.setSource(QUrl.fromLocalFile(c_path))
            else:
                player.setSource(QUrl())

        self.update_volumes()

    def update_volumes(self):
        if not self._initialized:
            return
        snd_conf = config_mgr.config.get("sound", {})
        k_vol = snd_conf.get("key_volume", 50) / 100.0
        c_vol = snd_conf.get("click_volume", 50) / 100.0
        for p in self.key_pool:
            p.setVolume(k_vol)
        for p in self.click_pool:
            p.setVolume(c_vol)

    def play_key(self):
        if not self._initialized or not self.key_pool:
            return
        snd_conf = config_mgr.config.get("sound", {})
        if not snd_conf.get("key_sound_enabled", True):
            return
        self.key_pool[self.key_idx].play()
        self.key_idx = (self.key_idx + 1) % len(self.key_pool)

    def play_click(self):
        if not self._initialized or not self.click_pool:
            return
        snd_conf = config_mgr.config.get("sound", {})
        if not snd_conf.get("click_sound_enabled", True):
            return
        self.click_pool[self.click_idx].play()
        self.click_idx = (self.click_idx + 1) % len(self.click_pool)

    @staticmethod
    def is_valid_wav(path, max_sec=2.5):
        if not path.lower().endswith('.wav'):
            return False
        try:
            with wave.open(path, 'r') as f:
                return (f.getnframes() / float(f.getframerate())) <= max_sec
        except Exception:
            return False

sound_mgr = SoundManager()