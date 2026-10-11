# 무게무게 네이티브 디자인 파운데이션

승인된 운동 흐름을 네이티브 컴포넌트로 구현한다. 토큰의 단일 출처는 `design-tokens/tokens.json`이다. `scripts/generate_design_tokens.py`가 `BrandUI.swift`의 MugeStyle을 생성하며 `--check`로 불일치를 차단한다. 출처와 보정 사항은 `docs/DESIGN_SYSTEM.md`에 기록한다.

## 역할과 토큰

2026-10-11 첨부 캡처와 차콜 브랜드 지시에 따라 갱신했다. 수치는 `design-tokens/tokens.json`을 따른다.
디자인 출처·화면 간격·타이포 역할·다크 모드·버튼 터치 영역은 `docs/DESIGN_SYSTEM.md`에 명시한다.
화면 여백12 / 카드 안쪽20 / 카드 간격12 / 반경24pt. 주요 버튼50pt, 차콜 #2A2A2A.

## 컴포넌트

- `MugeCard`: 동일한 여백·배경·반경을 적용한다. 승인안의 부드러운 보조 표면을 사용하며 불필요한 테두리를 넣지 않는다.
- `MugeSectionTitle`: 제목을 VoiceOver 헤더로 노출하고 설명은 여러 줄을 허용한다.
- `MugePrimaryButtonStyle`: 화면 전체 폭, 최소 높이, 눌림·비활성 상태를 한 곳에서 관리한다.
- `MugeSecondaryButtonStyle`: 휴식 조절 버튼의 최소 조작 영역과 상태 표현을 공유한다.
- `MugeMetricRow`: 일반 크기에서는 Grid로 같은 행의 카드 높이를 정렬하고 접근성 글자 크기에서는 세로로 배치한다.
- `MugeAdaptiveRow`: 제목·캐릭터, 운동 입력, 완료 지표를 접근성 글자 크기에서 세로로 전환한다.
- `mugeNumber`: 시스템 글자 크기 설정에 따라 숫자를 확대한다.
- `MugeMassInput`: 직접 입력·±조절·범위 오류를 동일하게 표시한다. kg/lb는 MassUnit에서만 변환한다.
- `MugeNavigationLabel`: 라벨과 Lucide chevron을 가진 44pt 이상 탐색 행이다.
- `MugeIcon`: Lucide의 24px/2px 둥근 선 SVG를 template 자산으로 사용한다.

## 아이콘 출처

lucide-icons/lucide commit 70562c1ee1c4fdcf736fe97bc893fb8511927934에서 필요한 10개만 포함했다.
원본 도형은 변경하지 않았으며 currentColor만 template용 검정으로 치환했다.
원본 ISC/MIT 고지는 docs/third-party/Lucide-LICENSE와 앱 설정의 오픈소스 라이선스에 포함한다.
OS 자체 내비게이션·문서 선택·계정 버튼은 시스템 표현을 유지한다.

## 화면 적용 규칙

네이티브 TabView와 NavigationStack을 사용한다. 운동 중에는 탭을 감추고 세트 완료·다음 운동·마무리 액션을 safeAreaInset에 고정한다. 휴식은 전체 화면이며 세로 공간이 부족하면 스크롤할 수 있다. 숫자의 분·초는 VoiceOver에 한국어로 읽힌다.

릴라는 홈·준비·마무리에서 사용한다. 실제 운동 입력과 휴식 타이머에 캐릭터를 배치하지 않는다. 화면 문구는 한국어이며 앱 이름은 무게무게다. 원본 자료의 제목·기술 식별자는 번역된 화면 문구와 구분한다.

## 책임 분리

화면은 표현과 임시 입력 상태를 담당하고, 세트·최대 중량·휴식의 영속 상태는 기존 WorkoutStore의 원자적 연산을 통해 변경한다. 시각 토큰 변경으로 저장 스키마나 연구 검증 정책을 변경하지 않는다. 공통 스타일은 입력값의 유효성이나 성공 여부를 판단하지 않는다.

## 검증 범위

실제 빌드 결과와 자동 테스트 결과는 작업 보고에서 별도로 기록한다. 이 문서는 기기 설치·VoiceOver 수동 검수·모든 Dynamic Type 조합의 통과를 주장하지 않는다. 실기기에서는 큰 글씨, 긴 한국어 라벨, 숫자 입력 키보드, 다크 모드의 대비와 완료·오류 상태를 확인한다.
