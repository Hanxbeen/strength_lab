# 릴라 Phase 2 — Rive 제작 패키지 (구현 진행 중)

> 브랜드: 무게꾼 · 캐릭터: 릴라 · 승인된 머리털: **A안(짧게 누운 잔털 2~3가닥)**
>
> 작업 방식: **포스터 생략 → 파츠 원화 → 상태 계약 → Rive Editor에서 리깅 → 실제 .riv 검수**.
>
> 이 저장소의 `assets/lila/rive_import/*.svg`는 **Rive로 가져갈 편집 가능한 SVG 원화**이고, 아직 **Rive 애니메이션 파일(.riv)은 아니다**. 기존 홈 마스코트/앱 아이콘은 변경하지 않았다.

## 생성된 산출물

- `assets/lila/rive_import/lila_level_01.svg` ... `lila_level_06.svg`: 단계별 개별 벡터(동일 기본 얼굴, 소품 Lv.6만 왕관+망토).
- `assets/lila/rive_import/lila_face_master.svg`: 머리와 얼굴 독립 파츠.
- `assets/lila/manifest.json`: 레벨·리그 파츠·감정·피벗·금지 요소 계약.
- `assets/lila/lila_motion_preview.html`: 브라우저에서 단계·감정을 선택하는 인터랙티브 **CSS 동작 프로토타입**.
- `scripts/build_lila_phase2_assets.py`: SVG 원화를 재생성하는 스크립트.
- `tests/test_lila_phase2_assets.py`: 6단계, 소품, A안 머리털, 입 금지, SVG 구조 검수.

### 원본 3D와 충실도 제한

사용자가 선택한 **원본 3D 릴라 이미지는 현재 맥북 저장소에 파일로 존재하지 않는다.** 따라서 지금 만든 SVG는 색·아이덴티티·움직일 수 있는 파츠 구조를 검증하는 **리깅용 기초 원화**이다. 실제 3D/클레이 렌더와 픽셀 수준으로 같다고 말할 수 없고, 그 목표에는 원본 마스터의 얼굴·조명·비율을 비교하면서 고품질 벡터/레이어 이미지를 별도 보정해야 한다.

Rive는 SVG를 **편집 가능한 벡터 형태로 가져올 수 있지만**, SVG가 자동으로 완성된 애니메이션이나 관절 본을 만들어 주지는 않는다. (공식 안내: https://rive.app/docs/editor/assets/svg)

## 1. 편집 가능한 파츠 구조

레이어는 `assets/lila/manifest.json > part_groups`가 진실 공급원이다.

| 그룹 | 역할 | 권장 피벗/제어 |
|---|---|---|
| `character_root` | 전체 캐릭터 컨테이너 | 중심 기준 |
| `head_group` | 귀·두개골·잔털·이마·주둥이·눈·코 통합 | 목 근처 회전·스웨이 |
| `head_skull` | 두개골 및 차콜 털 | 움직임 부모와 함께 |
| `tuft_A` | 짧게 누운 3가닥 잔털 | head_group 종속 |
| `ear_left`, `ear_right` | 둥근 귀 | 머리 종속 |
| `forehead_skin`, `muzzle_skin` | 이마·아이보리 주둥이 | 머리 종속 |
| `eye_left`, `eye_right` | 세로 타원 눈 | 깜빡임/감정 스케일 |
| `nostril_left`, `nostril_right` | 작은 콧구멍 | 머리 종속 |
| `body_torso`, `belly_skin` | 성장 단계별 체형 | 호흡 미세 변화 |
| `arm_left`, `arm_right` | 좌우 팔·손 | 운동/도구 관절 목표 |
| `leg_left`, `leg_right` | 좌우 허벅지·종아리 통합 | 골반 피벗 별도 그룹 (현재 실루엣 프로토타입) |
| `foot_left`, `foot_right` | 좌우 발 | 발목 피벗으로 회전/바닥 접촉 |
| `crown_front`, `cape_back` | Lv.6만의 왕관·망토 | 운동 중 자동 숨김 |

**미해결:** 현재 좌우 다리와 발을 분리했지만, 무릎·골반·팔꿈치·손가락/바벨 그립은 실제 SBD 리깅 전에 추가 분해해야 한다. 벡터 기본형을 완성된 3D 본 리그로 취급하지 않는다.

## 2. 레벨 계약

1. 아기 — 큰 머리, 앉음, 짧은 팔/다리, 빈손.
2. 새싹 — 두 발 직립, 작고 가는 팔다리, 빈손.
3. 성장 — 어깨·가슴 볼륨이 처음 명확해짐, 빈손.
4. 단단함 — 전완·상완·허벅지가 굵어짐, 빈손.
5. 숙련 — 넓은 어깨·승모·굵은 팔·안정된 하체, 빈손.
6. 무게왕 — **Lv.5와 동일한 성숙 체형 + 왕관·망토만 추가**.

동일 모델 전체 확대만으로 1~6을 표현하면 불합격. 실측 신장/중량 수치를 임의 부여하지 않는다.

## 3. Rive state machine 계약 — 추후 실제 파일에 구현

예정 아트보드 `LilaCharacter`, 상태 머신 `LilaCompanion`.

| 입력 | 타입 | 의미 |
|---|---|---|
| `level` | Number(1~6) | 성장 레벨. 기본 1 |
| `mood` | Number(0~10) | 아래 enum 인덱스 |
| `action` | Number | 대기, 운동, 기록, 정비, 축하. 상세 값 추후 |
| `isWorkingOut` | Boolean | 실제 운동 중이면 왕관·망토 숨김 |
| `isVisible` | Boolean | 비가시 상태면 애니메이션 정지 |
| `reduceMotion` | Boolean | 접근성: 최소화/정지 |
| `celebrate` | Trigger | 운동 완료/PR 인정 후 1회 재생 |
| `blink` | Trigger | 필요 시 깜빡임 |

`mood` enum(순서 유지): `idle, happy, surprise, curious, dizzy, focus, sleepy, confident, celebrate, repairing, warning`.

우선순위: 실제 오류/안전 > 현재 수행 중인 운동 > 1회성 완료/PR > 화면 별 맥락 > idle.

**잘못된 상태 금지:** 저장 전 성공 표시, 동기화 완료 전 축하, 운동 중 설정 애니메이션, Lv.6 운동 중 왕관/망토 착용.

## 4. 실제 Rive Editor 작업 순서

1. **사용자 원본 3D와 마스터 SVG를 나란히 비교**해서 얼굴·귀·주둥이·털 형태를 수작업 보정(원본은 레퍼런스이며 SVG가 아직 똑같지 않음).
2. [Rive Editor](https://rive.app/)에서 `LilaCharacter` 아트보드를 만들고 `lila_level_03.svg`부터 Import SVG한다.
3. 그룹/경로를 점검하고, 머리·좌우 팔·골반·좌우 다리·발 및 소품을 각각 리깅한다. 원본 머리와 같은 실루엣으로 레벨 1~6을 단계별 컴포넌트에 바인딩한다.
4. `idle`에서 작은 호흡/간헐적 눈깜빡임만 구현하고 눈/주둥이/귀/잔털이 분리되지 않는지 확인.
5. `focus`, `surprise`, `dizzy`, `repairing` 등 눈+주변 기호 상태 전환 구성.
6. 레벨 변경 시 **체형 변화가 실제로 일어나는지** 검수한다. 레벨5~6은 몸체가 동일하고 왕관·망토만 다르다.
7. 정상적인 `LilaCompanion` state machine을 export한 `lila.riv` 파일을 앱 리소스에 넣는다.
8. 그때 공식 [Rive Apple runtime](https://rive.app/docs/runtimes/apple/apple)을 SPM으로 연결하고, 홈 화면 기존 임시 마스코트를 **사용자 QA 후** 교체한다.

Rive 편집기에서 내보낸 `.riv` 없이 현재 파일들만으로 Rive iOS runtime을 실행했다고 주장하지 않는다.

## 5. 검수 게이트

- **Gate A — 구조 자동 검수**: 6단계 SVG 구조가 유효; A안 잔털; 2눈/2콧구멍; 입 없음; 임의 손 소품 없음; 6단계만 왕관·망토.
- **Gate B — 시각 수동 검수**: 원본 릴라와 같은 얼굴; 거의 블랙인 차콜과 아이보리; 2~5 단계 체형의 발전; 작은 기기 크기에서 동일 캐릭터.
- **Gate C — Rive editor 리그**: 본·피벗·팔/다리 4지 분리, 시점/원판/벤치/바벨 관통 없음; 6레벨 변형과 11 감정 전환.
- **Gate D — 실기기**: .riv 렌더가 앱 화면 상태와 일치하며 CPU/메모리, 화면 밖 정지, Reduce Motion 검수.

**진행 상태:** Gate A 자동 구조 검수 및 Chrome 정적 화면 렌더링 확인. Chrome 개발자 프로토콜 자동 버튼 클릭 검사는 연결 시간 초과로 **미검증**. B는 원본 참조 파일의 수동 비교 필요. C/D는 아직 진행되지 않음.

## 6. 맥북에서 미리보기

```bash
cd /Users/hanbeen/codex-workspace/strength_lab
python3 scripts/build_lila_phase2_assets.py
open assets/lila/lila_motion_preview.html
python3 -m unittest discover -s tests -q
```

지금까지 사용자 소유의 `docs/UX_WIREFRAME.html`에는 손대지 않는다.
