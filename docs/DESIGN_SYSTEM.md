# 무게무게 공유 파운데이션

원칙은 2026-10-08 합의한 **공유 파운데이션·UI 모델 + 플랫폼 네이티브 컴포넌트**다.
토큰 원본은 design-tokens/tokens.json 하나이며 iOS MugeStyle은 scripts/generate_design_tokens.py가 생성한다.
기존 BrandUI.swift의 임의 RGB·시스템 그룹 배경을 공통 원본으로 간주했던 구현을 수정한다.
Android 구현은 아직 없으며, 같은 JSON의 의미 역할을 해당 플랫폼 컴포넌트에 매핑한다.

## 출처와 변경

- 색상·표면·반경: 2026-10-10 승인된 40화면 시안의 라이트/다크 값을 기준으로 한다.
- CTA 파란색: 원본 #2474EE와 흰색의 대비는 4.37:1이었다. 팔레트 원본은 유지하고 텍스트·액션 역할은 #216EE6으로 대비 보정했다. 다크 모드는 #70A9FF / #102542.
- 화면 배경 흰색 / #17191F, 보조 표면 #F5F6F8 / #242731. 밝기 모드에 따라 개별 의미 색상이 변한다.
- 페이지 여백 20, 카드 반경 22, 버튼 반경 17, 입력 반경 12, CTA 최소 56, 행 최소 48.
- 타이포는 고정 폰트 대신 iOS Dynamic Type 역할을 사용한다. 제목 title/bold(28), 섹션 title3/bold(20), 카드·액션 headline(17), 본문 body(17), 상세 subheadline(15), 주석 footnote(13).
- 릴라 차콜·아이보리는 마스코트 팔레트이며 전체 액션 색상으로 바꿔 적용하지 않는다.
- 외부 ‘Solid’ 라이브러리를 쓰기로 확정했다는 근거는 찾지 못했다. 검토용 45화면 스타일과 최신 승인안은 구분한다.

## 구성요소와 책임

BrandUI는 Card, PrimaryAction, SecondaryAction, NavigationRow, MassInput, MetricRow, AdaptiveRow, Icon과 숫자 스타일을 제공한다.
화면은 토큰 원값을 정의하지 않는다. TabView, NavigationStack, Toolbar, TextField, Picker, Toggle, Sheet는 네이티브를 사용한다.
유리 효과는 iOS에서 NativeGlassPanel이 맡으며, 모든 콘텐츠 카드에 일괄 적용하지 않는다.
연구·운동 데이터 검증은 디자인 컴포넌트가 담당하지 않는다.

## 검증 명령

    python3 scripts/generate_design_tokens.py --check
    python3 scripts/check_ux_foundations.py

토큰 동기화·계산 대비 검증과 실제 글자 크기·다크 모드·VoiceOver 검수는 별개다.
