# core/sound_manager.py
import os
import wave
from PyQt6.QtCore import QUrl
from PyQt6.QtMultimedia import QSoundEffect
from core.config_manager import config_mgr, ASSETS_DIR

# QSoundEffect는 비압축 PCM WAV 파일만 안정적으로 디코딩 지원합니다.
SUPPORTED_EXTENSIONS = ('.wav',)

def scan_sound_files():
    """assets/sounds/ 디렉토리 및 하위 폴더 내의 모든 유효한 WAV 파일을 스캔하여 반환"""
    found_sounds = {}
    if not os.path.exists(ASSETS_DIR):
        os.makedirs(ASSETS_DIR, exist_ok=True)
        return found_sounds

    for root, _, files in os.walk(ASSETS_DIR):
        for f in sorted(files):
            ext = os.path.splitext(f)[1].lower()
            if ext in SUPPORTED_EXTENSIONS:
                base_name = os.path.splitext(f)[0]
                full_path = os.path.abspath(os.path.join(root, f))
                
                rel_dir = os.path.relpath(root, ASSETS_DIR)
                if rel_dir != ".":
                    display_name = f"[{rel_dir}] {base_name}"
                else:
                    display_name = base_name
                    
                found_sounds[display_name] = full_path

    return found_sounds

class SoundManager:
    def __init__(self):
        self.key_pool = []
        self.click_pool = []
        self.key_idx = 0
        self.click_idx = 0
        self._initialized = False

    def ensure_initialized(self):
        """QApplication이 생성된 후 QSoundEffect 풀을 초기화"""
        if self._initialized:
            return
        self.key_pool = [QSoundEffect() for _ in range(6)]
        self.click_pool = [QSoundEffect() for _ in range(4)]
        self._initialized = True
        self.load_sounds()

    def get_actual_path(self, prefix):
        """설정에 저장된 값으로부터 유효한 WAV 파일 경로 반환"""
        val = config_mgr.settings.get(f"{prefix}_sound_path", "")
        if not val or val == "none":
            return ""

        # 1. 절대 경로로 존재하며 .wav 파일인 경우
        if os.path.isabs(val) and os.path.exists(val) and val.lower().endswith('.wav'):
            return val

        # 2. assets/sounds/ 하위 상대 경로
        candidate = os.path.join(ASSETS_DIR, val)
        if os.path.exists(candidate) and candidate.lower().endswith('.wav'):
            return os.path.abspath(candidate)

        # 3. 스캔 맵 검색
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
        k_vol = config_mgr.settings.get("key_volume", 50) / 100.0
        c_vol = config_mgr.settings.get("click_volume", 50) / 100.0
        for player in self.key_pool:
            player.setVolume(k_vol)
        for player in self.click_pool:
            player.setVolume(c_vol)

    def play_key(self):
        if not self._initialized or not self.key_pool:
            return
        if not config_mgr.settings.get("key_sound_enabled", True):
            return
        self.key_pool[self.key_idx].play()
        self.key_idx = (self.key_idx + 1) % len(self.key_pool)

    def play_click(self):
        if not self._initialized or not self.click_pool:
            return
        if not config_mgr.settings.get("click_sound_enabled", True):
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