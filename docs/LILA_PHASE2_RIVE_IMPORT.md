# 릴라 Phase 2 — 실제 Rive 빌드 및 iOS 통합 (실기기 시각 검수 대기)

> 제품: 무게꾼 · 캐릭터: 릴라 · 2026-10-09 · 머리털 A안 (짧게 누운 잔털 2~3가닥)
>
> **중요:** 공식 Rive CLI를 통해 **실제 `lila.riv` 바이너리**가 생성되었고, 공식 RiveRuntime 6.28.1을 링크하는 **iOS 코드 빌드가 통과**했다. 하지만 사용자가 승인한 **원본 3D 모델과 완전히 같은 이미지가 아니다.** 정지 SVG→RML 벡터 포팅은 조명·질감을 단순화한다. 감정 11종 및 운동 동작의 Rive state machine 제작도 아직 완료하지 않았다.

## 이번에 확인한 사실

- Rive CLI 1.5.1 설치 및 환경 진단 정상.
- `assets/lila/rive_cli/scene.rml`은 **Rive Markup Language 실제 소스**. 6개 아트보드 이름 `LilaLv1` ~ `LilaLv6`, 각각 `LilaCompanion` 상태 머신.
- 각 레벨에 **IdleBreath** (머리 미세 회전/몸통 호흡)와 **NaturalBlink** (좌우 눈 수직 스케일) 두 개의 반복 애니메이션이 실제 키프레임으로 존재.
- CLI의 `--verify` 빌드 성공, `rive inspect --summary`에서 **problems=[]**, 6개 아트보드 확인.
- `apps/ios/MugeMuge/Resources/lila.riv`에 실제 바이너리 저장. 정식 Rive magic header `RIVE`.
- `apps/ios/MugeMuge/LilaRiveView.swift`는 공식 `RiveRuntime`의 `AsyncRiveUIViewRepresentable`, `Worker`, `File`, `Rive` API 사용.
- `HomeView.swift`의 홈 마스코트가 `LilaRiveView`로 변경됨. `LilaStudioView.swift`는 DEBUG 전용 레벨 1~6 검수 화면.
- 움직임 감소 설정(`accessibilityReduceMotion`)이 켜지면 재생을 일시정지함.
- Xcode 27에서 공식 XCFramework를 사용하여 `generic/platform=iOS` **서명 없는 빌드 및 Apple Development 서명 빌드 모두 성공**. 서명 프로파일은 `iOS Team Provisioning Profile: app.mugemuge.ios`. 경고 일부는 기존 다른 화면에서 발생.
- Mac과 iPhone이 실제로 연결된 뒤 **코드 서명 빌드 + 설치 + 실제 렌더/충돌 검증은 별도 수행해야 함**. 완료 전 실기기 성공이라 주장하지 않는다.

## 로컬 재현 방법

```bash
cd /Users/hanbeen/codex-workspace/strength_lab

# 최초 1회: 공식 런타임 ZIP 확보, 체크섬 검증, 앱 저장소에서 제외된 바이너리로 압축 해제
bash scripts/install_rive_xcframework.sh

# 단계/얼굴 SVG → RML → 실제 .riv → 6개 아트보드 검사 → iOS 리소스 복사 → 테스트
bash scripts/build_lila_rive.sh

cd apps/ios
xcodegen generate
xcodebuild -project MugeMuge.xcodeproj -scheme MugeMuge \
  -configuration Debug -destination 'generic/platform=iOS' \
  CODE_SIGNING_ALLOWED=NO build
```

### 재현성·저장소 경계

- 공식 릴리스 ZIP 소스 URL: `https://github.com/rive-app/rive-ios/releases/download/6.28.1/RiveRuntime.xcframework.zip`
- SHA-256: `6912ebf2cb6b5b99cac9a255f7d205cf8edf59a22fbdacd561a36d3820cc9baa`
- `apps/ios/RiveRuntimePackage/Package.swift`는 **로컬 바이너리 타깃**의 래퍼. `Binaries/`는 `.gitignore`로 제외되어 Git에 넣지 않는다.
- `assets/lila/rive_cli/build/`는 CLI 빌드 임시 디렉터리. **프로젝트의 `apps/ios/MugeMuge/Resources/lila.riv`만 배포용 바이너리**.
- RML 생성: `scripts/generate_lila_rive_rml.py`; SVG 생성: `scripts/build_lila_phase2_assets.py`; 전체 빌드/검수: `scripts/build_lila_rive.sh`.

## 현재 QA 게이트

| 게이트 | 상태 |
|---|---|
| A1. 원화 6레벨/입 없음/소품 규칙 | 자동 테스트 통과 |
| A2. RML 빌드 및 6개 Rive 아트보드, 2개 실제 애니메이션 | CLI 검증 통과 |
| A3. Rive iOS 프레임워크 링크, 앱 패키지에 .riv 포함 | Xcode 빌드 및 실기기용 개발 서명 통과 |
| B1. 원본 3D 릴라와 동일한 질감·형상 | **미통과 / 추가 디자인 보정 필요** |
| B2. 감정 11종 상태 전환 | **미구현** (현재 2개 idle/blink 반복 애니메이션만 구현) |
| B3. 운동 자세·관절·장비 상호작용 | **미구현** |
| C1. iPhone 실제 설치/실행/상태 전환 | **기기 연결 후 검증 필요** |
| C2. 성능·접근성·저전력·앱 데이터 보존 | 실기기 검증 대기 |

## 실기기에서 확인할 화면

1. iPhone을 Mac에 연결하고 잠금 해제. `xcrun devicectl list devices`에서 `Hanbeen`이 `available`인지 확인.
2. 동일 Bundle ID `app.mugemuge.ios` 개발 앱으로 빌드/설치. 기존 데이터 손실 방지를 위해 앱 삭제·초기화 금지.
3. 홈 상단 마스코트가 실제로 움직이는지 확인하고, **릴라 Rive 실험실**에서 Lv.1~6 선택 및 눈 깜빡임 확인.
4. 정지/백그라운드 동작 및 Reduce Motion, 앱 재실행 검수.
5. 성공 시 앱의 최종 디자인 후보와 실제 Rive 화면을 비교. 원본 3D 품질에는 추가 디자인 반복이 필요.

## 별도 유의사항

이 프로젝트의 사용자 소유 `docs/UX_WIREFRAME.html`은 수정·커밋·삭제하지 않는다.
