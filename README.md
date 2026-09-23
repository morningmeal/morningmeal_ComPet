# 🐾 morningmeal Desktop Pet
Windows와 macOS를 모두 지원하며, 멀티 펫 관리와 실시간 커스텀 스킨 편집을 제공합니다.

---

## 📥 즉시 다운로드 (Latest Release)

설치 과정 없이 압축을 풀고 바로 실행할 수 있는 무설치 포터블 버전입니다.

| 플랫폼 | 다운로드 링크 | 파일 포맷 |
| :--- | :--- | :--- |
| **Windows** | [⬇️ Compet-Windows.zip 다운로드](https://github.com/morningmeal/morningmeal_ComPet/releases/latest/download/Compet-Windows.zip) | `.zip` (실행 파일 포함) |
| **macOS** | [⬇️ Compet-macOS.zip 다운로드](https://github.com/morningmeal/morningmeal_ComPet/releases/latest/download/Compet-macOS.zip) | `.zip` (`.app` 번들) |

---

## 🚀 실행 방법 및 주의사항

### 🪟 Windows
1. `Compet-Windows.zip` 압축을 해제합니다.
2. 폴더 내 `Compet.exe`를 실행합니다.
3. Windows SmartScreen 경고가 뜨는 경우 **[추가 정보] -> [실행]**을 클릭합니다.

### 🍎 macOS
1. `Compet-macOS.zip` 압축을 풀고 `Compet.app`을 `응용 프로그램(/Applications)` 폴더로 이동합니다.
2. **필수 권한 설정**:
   * 백그라운드 키보드/마우스 입력을 감지하기 위해 권한이 필요합니다.
   * **[시스템 설정] -> [개인정보 보호 및 보안] -> [손쉬운 사용]**에서 `Compet`을 허용해 주세요.
3. **미확인 개발자 보안 경고 해결**:
   * 실행 시 "확인되지 않은 개발자" 경고가 뜨면 `Compet.app`을 **우클릭 -> [열기]**를 선택하거나 터미널에서 아래 명령어를 실행합니다:
     ```bash
     xattr -cr /Applications/Compet.app
     ```

---

## ✨ 주요 기능
- **Cross-Platform 지원**: Windows 및 macOS Dock 제어/권한 분기 처리
- **동적 3×N 펫 관리**: 여러 마리의 펫을 독립된 크기(30%~300%)와 스킨으로 동시 배치
- **모션 압축 깊이(Squash Depth) 제어**: 타건 강도와 속도(APM)에 비례한 물리 압축 애니메이션
- **사운드 자동 스캔**: `assets/sounds/` 폴더 내 WAV 파일 자동 감지 및 개별 볼륨 제어
- **단축키 & 상호작용**:
  * `Ctrl(또는 Cmd) + 마우스 휠`: 펫 크기 실시간 조절
  * 펫 우클릭: 펫 복제, 즉시 스킨 변경, 설정 창 열기
  * 화면 모서리 자석 스냅 & 마우스 클릭 관통(Click-Through) 모드