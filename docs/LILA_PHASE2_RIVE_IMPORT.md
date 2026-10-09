# 릴라 — 원본 3D 포스터 기반 실제 Rive 구현

> **상태**: 6단계 원본 3D 포스터 이미지가 **실제 Rive 아트보드**에 임베드됨. iPhone 15 Pro 실기기 설치·실행 및 Lv.6 렌더링 확인 완료(2026-10-09). 독립 표정/운동 동작과 원본 이미지 고해상도화는 미완성.

## 디자인 원본과 에셋

사용자가 승인한 원본 3D 포스터의 고릴라를 SVG로 재해석하지 않고, **실제 3D 렌더 이미지에서 분리한 6개의 RGBA 투명 에셋**을 사용한다.

- 원본 포스터: `assets/lila/poster_sprites/poster_reference.jpeg`
- 캐릭터별 원본: `assets/lila/poster_sprites/lila_lv01.webp` ~ `lila_lv06.webp`
- Rive에 포함되는 손실 없는 PNG: `assets/lila/rive_cli/sprites/lila_lv01.png` ~ `lila_lv06.png`
- 이미지별 픽셀 동일성·출처·제약: `assets/lila/poster_sprites/implementation_manifest.json`
- 최종 Rive 파일: `apps/ios/MugeMuge/Resources/lila.riv` (**실제 RIVE 시그니처 바이너리**)

각 이미지의 픽셀·알파 채널은 WebP 디코딩 후 PNG 변환 시 **동일하게 유지**된다. 다른 고릴라 그림이나 기본 타원형 SVG를 본 생산 파일에 사용하지 않는다.

단, 전체 포스터로부터 잘라낸 2D 이미지이고 편집 가능한 3D 모델이 아니다. 3D 음영은 정지 이미지로 보존되지만 **실제 3D 회전/시점 변경은 구현되지 않으며**, 원본 이미지가 작아 확대 시 해상도 제한이 있다. 머리와 손발을 큰 폭으로 독립 움직이려면 고품질 원본 파츠 추가 제작이 필요하다.

## Rive 구현

- 아트보드: `LilaLv1`~`LilaLv6` (6개)
- 상태 머신: 각 레벨별 `LilaCompanion`
- 두 애니메이션 (각 레벨별): `CalmBreath` (발 위치 기준 미세 수직 압축) 및 `SoftSway` (작은 좌우 회전)
- 이미지 파츠: 현 단계에서는 **각 레벨의 전체 캐릭터 이미지 1개**. 독립 눈/팔/다리/머리 파츠는 아직 없음
- Lv.6에만 왕관·망토가 포함되며, 이는 원본 이미지에 이미 렌더되어 있음. 왕관·망토의 별도 분리·운동 중 숨김은 아직 안 됨.
- 실제 SwiftUI 통합: `LilaRiveView.swift` → 공식 `RiveRuntime` → `lila.riv`; `LilaStudioView.swift`에서 Lv.1~6 교체 확인
- Reduce Motion: 켜진 경우 Rive 재생 일시정지

**구현하지 않은 것:** 감정 11종 인터랙션, 독립 눈 깜빡임, 전신 관절 리그, 스쿼트/벤치/데드리프트 등 운동 동작, 정확한 3D 자유 회전. UI에 이 기능을 구현했다고 주장하면 안 된다.

## 정식 빌드 경로

```bash
cd /Users/hanbeen/codex-workspace/strength_lab

# 받은 원본 3D 포스터 에셋을 이미 repo의 assets/lila/poster_sprites에 둠
# 원본 PNG를 임베드하는 RML 생성 → 실제 .riv → 검사 → iOS 리소스 교체
bash scripts/build_lila_rive.sh

# 첫 빌드 전 공식 Rive 6.28.1 xcframework 다운로드/체크섬 검증
bash scripts/install_rive_xcframework.sh

cd apps/ios
xcodegen generate
xcodebuild -project MugeMuge.xcodeproj -scheme MugeMuge \
  -configuration Debug -destination 'generic/platform=iOS' \
  DEVELOPMENT_TEAM=C7C4WB633C CODE_SIGN_STYLE=Automatic \
  CODE_SIGNING_ALLOWED=YES -allowProvisioningUpdates build
```

공식 Rive CLI 1.5.1을 사용하며, RML 생성기는 `scripts/generate_lila_poster_rive_rml.py`이다. 이전 `scripts/generate_lila_rive_rml.py`와 `assets/lila/rive_import/*.svg`는 **히스토리 참고용 레거시**이고, 생산 빌드에서 사용하지 않는다.

앱 아이콘은 `scripts/generate_lila_poster_icon.py`로 **Lv.3 포스터 원본 릴라 얼굴을 추출**해 제작한다. 앱 아이콘에는 Rive 파일을 직접 사용할 수 없으므로 정적 PNG만 사용한다.

### 품질·검증 상태

| 항목 | 상태 |
|---|---|
| 6개 원본 이미지·투명도 | 확인 |
| 각 원본 이미지와 PNG 디코딩 결과 픽셀 일치 | 자동 검증 통과 |
| 6개 실제 Rive 아트보드 | Rive CLI 검사 통과 |
| 기본 호흡·미세 흔들림 키프레임 | 코드 및 Rive CLI 검사 통과 |
| 원본 포스터에서 잘라낸 이미지와 동일한 정면 인상 | 직접 추출이므로 구조·색·형태 동일, 단 원본 해상도 한계 존재 |
| 실제 iPhone 설치·실행 | **iPhone 15 Pro에 같은 번들 ID로 업데이트 설치, 앱 실행 확인** |
| 실제 iPhone 렌더링 | **Lv.6 왕관·빨간 망토가 있는 원본 3D 릴라 화면 캡처로 확인** |
| Rive 애니메이션 시간 차 검증 | **Lv.6 0초 vs 1초 프레임 차이 확인 (밝기차 >5 픽셀 27,729개)** |
| 독립 표정·운동 동작 | 미구현 |
| 3D 모델·해상도 업그레이드 | 미구현 |

### 파일 관리

- `docs/UX_WIREFRAME.html`은 사용자 소유 파일. 이 작업에서 수정·삭제·커밋하지 않는다.
- iOS 번들 ID는 `app.mugemuge.ios` 유지. 같은 앱 위에 업데이트 설치하며 기존 앱을 삭제하지 않는다.

### 2026-10-09 실기기 검수 기록

- 대상: Hanbeen iPhone 15 Pro / iOS 26.5 / USB 페어링 / 개발자 모드 활성화.
- Xcode 27, Apple Development 서명 및 프로비저닝, 코드 서명 무결성 검사 통과.
- 기존 앱을 삭제하지 않고 `app.mugemuge.ios`로 업데이트 설치. 현장 캡처에 릴라 실험실 Lv.6의 원본 3D 렌더와 왕관·망토가 표시된 것을 확인.
- 스크린샷 자체는 개인 기기 상의 콘텐츠가 포함될 수 있어 GitHub에 업로드하지 않음.
- 실제 iPhone 상에서 모든 6개 레벨과 모든 감정/관절 움직임의 실사용 QA 완료를 의미하지 않음.
