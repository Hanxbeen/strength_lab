# 릴라 Phase 2 — 원본 3D풍 Rive 실기기 구현 기록

> 브랜드 **무게꾼**, 마스코트 **릴라**, 머리털 A안, 기준 이미지: 사용자가 승인한 6단계 3D 포스터.
> 상태: **초해상도/눈 깜빡임/호흡·흔들림 구현 완료**, 정식 관절 운동 리그 **미구현**.
> 2026-10-09 Hanbeen iPhone 15 Pro 업데이트 설치·실행 확인. 레벨별 실기기 육안 QA는 별도.

## 실제 산출물

- **원본:** `assets/lila/poster_sprites/lila_lv01.webp` ~ `lila_lv06.webp`.
  처음 포스터에서 잘라낸 이미지의 각 레벨 높이는 265~478px. 3D 메쉬/조명 데이터가 포함된 3D 원본은 아니다.
- **AI 초해상도:** `assets/lila/poster_upscaled/lila_lv01_4x.png` ~ `lila_lv06_4x.png`.
  4배 확대(최대 2136×1912px). [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN)의
  `RealESRGAN_x4plus_anime_6B`(RRDBNet, 6 blocks, ×4)를 Apple M4 Pro MPS로 실행.
  모델 가중치 공식 URL:
  `https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth`.
  검증 SHA256: `f872d837d3c90ed2e05227bed711af5671a6fd1c9f7d7e91c911a61f155e99da`.
  가중치는 사용자의 `~/.cache/lila-upscale/`에 설치; **GitHub 저장소에는 커밋하지 않는다**.
  색/질감에 일부 AI 추정이 들어가므로 실제 원본 3D의 소실된 정보가 복원되는 것이 아니다.
- **눈꺼풀 2개:** `assets/lila/poster_eyelids/lila_lvNN_blink_overlay.png`.
  원본의 두 검은 세로 눈의 위치를 측정해, 바로 인접한 아이보리 피부 색으로 폐안 상태를 합성한 **투명 이미지 레이어**.
  입·코·표정 모양을 새 고릴라로 재해석하지 않는다. 한 프레임 내부의 눈 감기만 표현한다.
- **Rive 소스:** `assets/lila/rive_cli/scene.rml`.
  `ImageAsset` 12개(각 레벨당 고해상도 원본+독립 눈꺼풀), `LilaLv1`~`LilaLv6` 아트보드.
  각 아트보드 `LilaCompanion` State Machine과 반복 애니메이션 3개:
    - `CalmBreath`: 발 기준 수직 미세 호흡.
    - `SoftSway`: 다리 기준 작은 몸 기울임.
    - `NaturalBlink`: 얼굴의 **눈꺼풀 레이어 opacity만** 0→1→0으로 키프레임 제어.
  Rive 이미지의 기본 크기가 4배가 되었으므로 drawable scale은 양축 **0.25**.
- **실제 Rive 바이너리:** `apps/ios/MugeMuge/Resources/lila.riv` (현재 약 6.6MiB).
  Mac Rive CLI에서 `--verify`, 실제 화면 `--screenshot` 및 `inspect` 검사 통과, 오류 0개.
- **실제 앱:** `LilaRiveView.swift`에서 `RiveRuntime`으로 로컬 `lila.riv`을 표시.
  `LilaStudioView.swift` DEBUG 전용 레벨 1~6 검수 화면.
  **릴라 얼굴 앱 아이콘**도 Lv3 초해상도 원화 기반 정적 1024×1024 PNG로 업데이트.

## 재현/빌드

```bash
cd /Users/hanbeen/codex-workspace/strength_lab
# 첫 재생성인 경우 모델 가중치를 위 공식 주소에서
# ~/.cache/lila-upscale/RealESRGAN_x4plus_anime_6B.pth 로 내려받는다.
# 기본 macOS /usr/bin/python3 대신 torch가 설치된 Homebrew Python3.13을 사용
/opt/homebrew/bin/python3.13 scripts/upscale_lila_posters.py
python3 scripts/build_lila_eye_blinks.py
bash scripts/build_lila_rive.sh
python3 scripts/generate_lila_poster_icon.py
cd apps/ios && xcodegen generate
xcodebuild -project MugeMuge.xcodeproj -scheme MugeMuge \
  -configuration Debug -destination 'platform=iOS,id=00008130-00190DD602D8001C' \
  DEVELOPMENT_TEAM=C7C4WB633C CODE_SIGN_STYLE=Automatic \
  CODE_SIGNING_ALLOWED=YES -allowProvisioningUpdates build
```

`scripts/build_lila_rive.sh`는 업스케일 이미지가 이미 생성돼 있으면 그대로 사용해 매번 AI 추정 결과를 바꾸지 않는다.
공식 RiveRuntime 6.28.1은 `bash scripts/install_rive_xcframework.sh` 로 설치.

## 2026-10-09 검증 결과

| 검사 | 판정 |
|---|---|
| 6레벨 독립 고해상도 원화 | 통과(4배×4배 총 픽셀, 6장) |
| 원본 레벨 얼굴/몸 실루엣 유지 | 참조 기반 확대; AI 처리로 색·질감 변화 가능 |
| Rive StateMachine/Keyframes | 통과(6 아트보드, 12 이미지, 18 반복 애니메이션) |
| Rive 실제 프레임 시각 비교 | 통과: Lv3 눈 뜸 vs 눈 감음이 다름 |
| 전체 이미지 조작이 아닌 눈 독립 애니메이션 | **통과: 두 눈이 있는 반투명 눈꺼풀 이미지 단독 opacity 변경** |
| Xcode iPhone Debug 개발 서명 빌드 | 통과(Xcode 27) |
| 기존 앱 삭제 없이 Hanbeen iPhone 15 Pro 업데이트 설치 | 통과; bundle ID app.mugemuge.ios 유지 |
| iPhone 앱 실행 | 통과. 앱 전환 화면 캡처 시점에는 앱이 백그라운드여서 상세 애니메이션 육안 판정은 보류 |
| 자동 테스트 | 54개 통과 |
| 팔·다리 별도 관절과 바벨·기구 상호작용 | **미구현** |
| 감정 11종과 레벨별 활동 | **미구현** |
| 3D 자유 회전·진짜 3D 고해상도 복원 | **불가능한 주장. 별도 3D 모델/고해상도 재렌더 필요** |

### 다음 리깅 Gate

1. 사용자가 6단계의 초해상도 렌더링이 원본 릴라 인상을 잘 보존했는지 실기기에서 확인.
2. 정면/사선/측면별 고해상도 신규 원화를 확보하거나 실제 3D 모델 리깅·렌더링.
3. 원본 입체감 유지하는 **머리·상완·전완·손·골반·허벅지·발** 분리 이미지 및 가려진 부분 복원.
4. Rive 이미지 Mesh와 Bone으로 독립 관절 동작을 구현. 릴라 몸이 찌그러지거나 손/바벨이 관통하면 불합격.
5. 임의 동작을 완성했다고 주장하지 말고 실제 운동 종목별 폼 검증 및 실기기 프레임 QA를 통과시킨 후 앱 반영.

역사적 SVG/도형 버전은 `scripts/generate_lila_rive_rml.py`와 `assets/lila/rive_import/`에 비교용으로만 존재한다. 생산 빌드는 반드시 포스터 원본에서 생성한다.

**사용자 파일 보호**: `docs/UX_WIREFRAME.html` 수정/삭제/커밋 금지.
