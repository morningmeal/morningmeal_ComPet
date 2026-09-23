# core/i18n.py
from PyQt6.QtCore import QLocale, QObject, pyqtSignal

TRANSLATIONS = {
    "ko": {
        "settings_title": "morningmeal_Compet - 환경 설정", "tab_general": "⚙️ 일반", "tab_sound": "🎵 사운드", "tab_pets": "🐾 펫 관리", "tab_skin": "🎨 스킨 편집",
        "language": "언어 (Language)", "tray_mode": "작업표시줄에 표시하지 않고 트레이로 숨기기",
        "sound_enable": "사운드 활성화", "volume": "볼륨", "upload_sound": "사운드 파일 업로드",
        "key_sound": "키보드 타건음 설정", "click_sound": "마우스 클릭음 설정",
        "add_pet": "➕ 새 펫 추가", "pet_list": "활성 펫 목록",
        "current_skin": "편집할 스킨", "squash_depth": "모션 압축 정도 (눌림 강도)",
        "save_apply": "💾 설정 저장 및 전체 적용",
        "upload_err": "사운드 파일은 2초 이하의 WAV 파일만 지원됩니다.",
        "tray_show": "설정 열기", "tray_exit": "종료",
        "click_through": "클릭 관통 (마우스 무시)", "lock_position": "위치 고정 (드래그 방지)",
        "import_skin": "스킨 패키지 가져오기 (.zip)", "export_skin": "현재 스킨 내보내기 (.zip)",
        "critical_error": "치명적인 오류", "crash_msg": "프로그램에 예기치 않은 오류가 발생했습니다.\ncrash_log.txt 파일을 확인해주세요.",
        "error": "오류", "complete": "완료", "applied": "적용됨",
        "skin_label": "스킨:", "size_label": "크기:",
        "using_default_sound": "사운드 미사용 중", "select_sound": "사운드 선택:",
        "select_wav": "WAV 파일 선택", "wav_filter": "WAV Files (*.wav)",
        "skin_pkg_manage": "스킨 패키지 관리", "open_skin_zip": "스킨 ZIP 열기", "zip_filter": "ZIP Files (*.zip)",
        "import_success": "스킨을 성공적으로 추가했습니다.", "import_fail": "가져오기 실패:",
        "save_skin_zip": "스킨 ZIP 저장", "export_success": "스킨을 성공적으로 내보냈습니다.", "export_fail": "내보내기 실패:",
        "save_complete_msg": "설정이 저장되고 전체 펫에 적용되었습니다.",
        "preset_default": "기본 사운드", "preset_blue": "청축 (Blue Switch)", "preset_brown": "갈축 (Brown Switch)", 
        "preset_pebble": "조약돌 (Pebble)", "preset_light": "가벼운 클릭", "preset_heavy": "묵직한 클릭", "preset_custom": "사용자 정의...",
        "mac_permission_title": "macOS 권한 안내", 
        "mac_permission_msg": "macOS에서는 백그라운드 키보드/마우스 감지를 위해 권한이 필요합니다.\n\n[시스템 설정] -> [개인정보 보호 및 보안] -> [손쉬운 사용] 및 [입력 모니터링]에서 이 앱을 허용해주세요.",
        "change_skin": "스킨 변경", "duplicate_pet": "펫 복제",
        "create_skin": "새 스킨 생성", "open_skin_folder": "폴더 열기",
        "idle_image": "대기 상태 이미지 (Idle):", "tap1_image": "타건 1 이미지 (왼손):", "tap2_image": "타건 2 이미지 (오른손):",
        "browse": "찾아보기", "key_mapping_title": "특정 키 및 마우스 매핑",
        "add_mapping": "매핑 추가", "del_mapping": "선택 삭제",
        "col_input": "감지 입력값", "col_image": "출력 이미지 파일", "col_browse": "파일 탐색",
        "input_waiting": "입력 대기", "input_detecting": "입력 감지 중...",
        "create_skin_prompt": "생성할 스킨의 영문 이름을 입력하세요:",
        "skin_exists_warn": "이미 존재하는 스킨 이름입니다.", "image_filter": "Images (*.png *.jpg *.jpeg *.gif *.webp)",
        "remove_pet": "펫 삭제"
    },
    "en": {
        "settings_title": "morningmeal_Compet - Settings", "tab_general": "⚙️ General", "tab_sound": "🎵 Sound", "tab_pets": "🐾 Pets", "tab_skin": "🎨 Skin Editor",
        "language": "Language", "tray_mode": "Hide from Taskbar (Tray mode)",
        "sound_enable": "Enable Sound", "volume": "Volume", "upload_sound": "Upload File",
        "key_sound": "Keyboard Sound", "click_sound": "Mouse Click Sound",
        "add_pet": "➕ Add New Pet", "pet_list": "Active Pets",
        "current_skin": "Editing Skin", "squash_depth": "Squash Depth (Compression)",
        "save_apply": "💾 Save & Apply",
        "upload_err": "Only WAV files under 2 seconds are allowed.",
        "tray_show": "Settings", "tray_exit": "Exit",
        "click_through": "Click-Through (Ignore Mouse)", "lock_position": "Lock Position",
        "import_skin": "Import Skin Package (.zip)", "export_skin": "Export Current Skin (.zip)",
        "critical_error": "Critical Error", "crash_msg": "An unexpected error occurred.\nPlease check crash_log.txt.",
        "error": "Error", "complete": "Complete", "applied": "Applied",
        "skin_label": "Skin:", "size_label": "Size:",
        "using_default_sound": "Sound Disabled", "select_sound": "Select Sound:",
        "select_wav": "Select WAV", "wav_filter": "WAV Files (*.wav)",
        "skin_pkg_manage": "Skin Package Management", "open_skin_zip": "Open Skin ZIP", "zip_filter": "ZIP Files (*.zip)",
        "import_success": "Skin successfully added.", "import_fail": "Import failed:",
        "save_skin_zip": "Save Skin ZIP", "export_success": "Skin successfully exported.", "export_fail": "Export failed:",
        "save_complete_msg": "Settings saved and applied to all pets.",
        "preset_default": "Default Sound", "preset_blue": "Blue Switch", "preset_brown": "Brown Switch", 
        "preset_pebble": "Pebble", "preset_light": "Light Click", "preset_heavy": "Heavy Click", "preset_custom": "Custom...",
        "mac_permission_title": "macOS Permissions Required", 
        "mac_permission_msg": "For background input detection on macOS, please grant permissions:\n\nGo to [System Settings] -> [Privacy & Security] -> [Accessibility] & [Input Monitoring].",
        "change_skin": "Change Skin", "duplicate_pet": "Duplicate Pet",
        "create_skin": "New Skin", "open_skin_folder": "Open Folder",
        "idle_image": "Idle Image:", "tap1_image": "Tap 1 Image (Left):", "tap2_image": "Tap 2 Image (Right):",
        "browse": "Browse", "key_mapping_title": "Specific Key & Mouse Mappings",
        "add_mapping": "Add Mapping", "del_mapping": "Delete Selected",
        "col_input": "Input Key", "col_image": "Image File", "col_browse": "Browse",
        "input_waiting": "Wait for Input", "input_detecting": "Press any key...",
        "create_skin_prompt": "Enter new skin name (English recommended):",
        "skin_exists_warn": "A skin with that name already exists.", "image_filter": "Images (*.png *.jpg *.jpeg *.gif *.webp)",
        "remove_pet": "Remove Pet"
    },
    "ja": {
        "settings_title": "morningmeal_Compet - 設定", "tab_general": "⚙️ 一般", "tab_sound": "🎵 サウンド", "tab_pets": "🐾 ペット管理", "tab_skin": "🎨 スキン編集",
        "language": "言語 (Language)", "tray_mode": "タスクバーから隠す（トレイモード）",
        "sound_enable": "サウンド有効化", "volume": "音量", "upload_sound": "アップロード",
        "key_sound": "キーボード音", "click_sound": "マウスクリック音",
        "add_pet": "➕ ペットを追加", "pet_list": "アクティブなペット",
        "current_skin": "編集するスキン", "squash_depth": "圧縮の深さ (押し込み強度)",
        "save_apply": "💾 保存して適用",
        "upload_err": "2秒以下のWAVファイルのみサポートされています。",
        "tray_show": "設定を開く", "tray_exit": "終了",
        "click_through": "クリック透過 (マウス無視)", "lock_position": "位置をロック",
        "import_skin": "スキンをインポート (.zip)", "export_skin": "スキンをエクスポート (.zip)",
        "critical_error": "致命的なエラー", "crash_msg": "予期せぬエラーが発生しました。\ncrash_log.txt を確認してください。",
        "error": "エラー", "complete": "完了", "applied": "適用されました",
        "skin_label": "スキン:", "size_label": "サイズ:",
        "using_default_sound": "サウンド無効", "select_sound": "サウンド選択:",
        "select_wav": "WAV 選択", "wav_filter": "WAV Files (*.wav)",
        "skin_pkg_manage": "スキンパッケージ管理", "open_skin_zip": "スキン ZIP を開く", "zip_filter": "ZIP Files (*.zip)",
        "import_success": "スキンを正常に追加しました。", "import_fail": "インポート失敗:",
        "save_skin_zip": "スキン ZIP を保存", "export_success": "スキンを正常にエクスポートしました。", "export_fail": "エクスポート失敗:",
        "save_complete_msg": "設定が保存され、すべてのペットに適用されました。",
        "preset_default": "デフォルト", "preset_blue": "青軸 (Blue Switch)", "preset_brown": "茶軸 (Brown Switch)", 
        "preset_pebble": "小石 (Pebble)", "preset_light": "軽いクリック", "preset_heavy": "重いクリック", "preset_custom": "カスタム...",
        "mac_permission_title": "macOS 権限案内", 
        "mac_permission_msg": "バックグラウンド入力検出のために権限が必要です。\n\n[システム設定] -> [プライバシーとセキュリティ] -> [アクセシビリティ] で許可してください。",
        "change_skin": "スキン変更", "duplicate_pet": "ペットを複製",
        "create_skin": "新規スキン", "open_skin_folder": "フォルダを開く",
        "idle_image": "待機画像 (Idle):", "tap1_image": "打鍵 1 画像 (左手):", "tap2_image": "打鍵 2 画像 (右手):",
        "browse": "参照", "key_mapping_title": "特定キーおよびマウスマッピング",
        "add_mapping": "マッピング追加", "del_mapping": "選択削除",
        "col_input": "入力キー", "col_image": "画像ファイル", "col_browse": "参照",
        "input_waiting": "入力待機", "input_detecting": "キー入力待ち...",
        "create_skin_prompt": "新しいスキン名を入力してください:",
        "skin_exists_warn": "同名のスキンが既に存在します。", "image_filter": "Images (*.png *.jpg *.jpeg *.gif *.webp)",
        "remove_pet": "ペットを削除"
    },
    "zh_CN": {
        "settings_title": "morningmeal_Compet - 设置", "tab_general": "⚙️ 常规", "tab_sound": "🎵 声音", "tab_pets": "🐾 宠物管理", "tab_skin": "🎨 皮肤编辑",
        "language": "语言 (Language)", "tray_mode": "隐藏任务栏图标 (托盘模式)",
        "sound_enable": "启用声音", "volume": "音量", "upload_sound": "上传声音",
        "key_sound": "键盘声音", "click_sound": "鼠标点击声音",
        "add_pet": "➕ 添加新宠物", "pet_list": "活动宠物",
        "current_skin": "当前编辑皮肤", "squash_depth": "动作压缩程度 (按压深度)",
        "save_apply": "💾 保存并应用",
        "upload_err": "仅支持2秒以下的WAV文件。",
        "tray_show": "打开设置", "tray_exit": "退出",
        "click_through": "鼠标穿透 (忽略点击)", "lock_position": "锁定位置",
        "import_skin": "导入皮肤包 (.zip)", "export_skin": "导出当前皮肤 (.zip)",
        "critical_error": "严重错误", "crash_msg": "发生意外错误。\n请检查 crash_log.txt。",
        "error": "错误", "complete": "完成", "applied": "已应用",
        "skin_label": "皮肤:", "size_label": "大小:",
        "using_default_sound": "未使用声音", "select_sound": "选择声音:",
        "select_wav": "选择 WAV", "wav_filter": "WAV Files (*.wav)",
        "skin_pkg_manage": "皮肤包管理", "open_skin_zip": "打开皮肤 ZIP", "zip_filter": "ZIP Files (*.zip)",
        "import_success": "成功添加皮肤。", "import_fail": "导入失败:",
        "save_skin_zip": "保存皮肤 ZIP", "export_success": "成功导出皮肤。", "export_fail": "导出失败:",
        "save_complete_msg": "设置已保存并应用于所有宠物。",
        "preset_default": "默认声音", "preset_blue": "青轴 (Blue Switch)", "preset_brown": "茶轴 (Brown Switch)", 
        "preset_pebble": "鹅卵石 (Pebble)", "preset_light": "轻击", "preset_heavy": "重击", "preset_custom": "自定义...",
        "mac_permission_title": "macOS 权限提示", 
        "mac_permission_msg": "macOS 需要辅助功能权限以监控全局按键。\n\n请前往 [系统设置] -> [隐私与安全性] -> [辅助功能] 中允许本程序。",
        "change_skin": "更换皮肤", "duplicate_pet": "复制宠物",
        "create_skin": "新建皮肤", "open_skin_folder": "打开文件夹",
        "idle_image": "待机图片 (Idle):", "tap1_image": "打键 1 图片 (左手):", "tap2_image": "打键 2 图片 (右手):",
        "browse": "浏览", "key_mapping_title": "特定按键与鼠标映射",
        "add_mapping": "添加映射", "del_mapping": "删除所选",
        "col_input": "输入按键", "col_image": "图片文件", "col_browse": "浏览",
        "input_waiting": "等待输入", "input_detecting": "正在检测输入...",
        "create_skin_prompt": "请输入新皮肤名称:",
        "skin_exists_warn": "该名称的皮肤已存在。", "image_filter": "Images (*.png *.jpg *.jpeg *.gif *.webp)",
        "remove_pet": "删除宠物"
    },
    "zh_TW": {
        "settings_title": "morningmeal_Compet - 設定", "tab_general": "⚙️ 常規", "tab_sound": "🎵 聲音", "tab_pets": "🐾 寵物管理", "tab_skin": "🎨 皮膚編輯",
        "language": "語言 (Language)", "tray_mode": "隱藏任務欄圖標 (托盤模式)",
        "sound_enable": "啟用聲音", "volume": "音量", "upload_sound": "上傳聲音",
        "key_sound": "鍵盤聲音", "click_sound": "滑鼠點擊聲音",
        "add_pet": "➕ 添加新寵物", "pet_list": "活動寵物",
        "current_skin": "當前編輯皮膚", "squash_depth": "動作壓縮程度 (按壓深度)",
        "save_apply": "💾 保存並應用",
        "upload_err": "僅支援2秒以下的WAV文件。",
        "tray_show": "打開設定", "tray_exit": "退出",
        "click_through": "滑鼠穿透 (忽略點擊)", "lock_position": "鎖定位置",
        "import_skin": "導入皮膚包 (.zip)", "export_skin": "導出當前皮膚 (.zip)",
        "critical_error": "嚴重錯誤", "crash_msg": "發生意外錯誤。\n請檢查 crash_log.txt。",
        "error": "錯誤", "complete": "完成", "applied": "已應用",
        "skin_label": "皮膚:", "size_label": "大小:",
        "using_default_sound": "未使用聲音", "select_sound": "選擇聲音:",
        "select_wav": "選擇 WAV", "wav_filter": "WAV Files (*.wav)",
        "skin_pkg_manage": "皮膚包管理", "open_skin_zip": "打開皮膚 ZIP", "zip_filter": "ZIP Files (*.zip)",
        "import_success": "成功添加皮膚。", "import_fail": "導入失敗:",
        "save_skin_zip": "保存皮膚 ZIP", "export_success": "成功導出皮膚。", "export_fail": "導出失敗:",
        "save_complete_msg": "設定已保存並應用於所有寵物。",
        "preset_default": "默認聲音", "preset_blue": "青軸 (Blue Switch)", "preset_brown": "茶軸 (Brown Switch)", 
        "preset_pebble": "鵝卵石 (Pebble)", "preset_light": "輕擊", "preset_heavy": "重擊", "preset_custom": "自定義...",
        "mac_permission_title": "macOS 權限提示", 
        "mac_permission_msg": "macOS 需要輔助功能權限以監控全域按鍵。\n\n請前往 [系統設定] -> [隱私與安全性] -> [輔助功能] 中允許本程式。",
        "change_skin": "更換皮膚", "duplicate_pet": "複製寵物",
        "create_skin": "新建皮膚", "open_skin_folder": "開啟資料夾",
        "idle_image": "待機圖片 (Idle):", "tap1_image": "打鍵 1 圖片 (左手):", "tap2_image": "打鍵 2 圖片 (右手):",
        "browse": "瀏覽", "key_mapping_title": "特定按鍵與滑鼠映射",
        "add_mapping": "添加映射", "del_mapping": "刪除所選",
        "col_input": "輸入按鍵", "col_image": "圖片檔案", "col_browse": "瀏覽",
        "input_waiting": "等待輸入", "input_detecting": "正在檢測輸入...",
        "create_skin_prompt": "請輸入新皮膚名稱:",
        "skin_exists_warn": "該名稱的皮膚已存在。", "image_filter": "Images (*.png *.jpg *.jpeg *.gif *.webp)",
        "remove_pet": "刪除寵物"
    }
}

class I18nManager(QObject):
    language_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._current_lang = "ko"

    def detect_os_language(self):
        sys_lang = QLocale.system().name()
        if sys_lang.startswith("en"): self.set_language("en")
        elif sys_lang.startswith("ja"): self.set_language("ja")
        elif sys_lang == "zh_CN": self.set_language("zh_CN")
        elif sys_lang.startswith("zh"): self.set_language("zh_TW")
        else: self.set_language("ko")

    def set_language(self, lang_code):
        if lang_code in TRANSLATIONS and self._current_lang != lang_code:
            self._current_lang = lang_code
            self.language_changed.emit()

    def get_lang(self):
        return self._current_lang

    def tr(self, key):
        return TRANSLATIONS.get(self._current_lang, TRANSLATIONS["ko"]).get(key, key)

I18n = I18nManager()