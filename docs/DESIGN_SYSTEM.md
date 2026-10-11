# 무게무게 공유 파운데이션

원본: `design-tokens/tokens.json`. iOS `MugeStyle`은 `scripts/generate_design_tokens.py`로 생성한다.
2026-10-11 사용자 지시가 이전 파란색 시안보다 우선한다. 브랜드 primary는 릴라 털 차콜 #2A2A2A다.
공유 파운데이션과 네이티브 컴포넌트 원칙은 유지한다.

## 화면 기준

사용자가 첨부한 토스 캡처의 비례를 기준으로 추정했다. 토스의 공식 토큰이나 정확한 측정값은 아니다.
- 밝은 회색 canvas #F2F4F6, 흰색 surface, 제목 #191F28, 보조 글자 #6B7684.
- 화면 가로 여백 12pt, 카드 안쪽 20pt, 카드 간격 12pt, 카드 반경 24pt.
- 주요 버튼 최소 50pt, 반경 14pt, 16pt semibold. 이전 56pt/17pt보다 작게 조정.
- 보조 버튼 최소 시각 높이 32pt(글자/패딩에 따라 증가), 반경 10pt, 13pt semibold. 실제 터치 영역은 최소 44pt.
- 헤더 22pt bold, 섹션/카드 17pt, 본문16pt, 설명15pt, 주석13pt, 주요 숫자26pt.
- iOS Dynamic Type으로 큰 글씨 설정을 따른다. 접근성 크기에 맞춰 행을 세로로 전환한다.
- 주요 버튼은 다크에서도 차콜/흰 글자. 링크·탭 등 tint는 다크에서 밝은 중립색으로 전환한다.
- 차콜/흰 글자 대비 14.35:1. 성공·오류 색은 상태 의미를 위해 별도 역할을 유지한다.
- 홈의 루틴 이동은 큰 채움 버튼 대신 행으로 변경. 운동 시작·세트 완료 등 핵심 행동만 primary.

## 검증

`python3 scripts/generate_design_tokens.py --check`
`python3 scripts/check_ux_foundations.py`

정적 계약과 Xcode 컴파일 검증은 실제 기기 시각 검수와 다르다. 캡처와 픽셀 단위 일치를 주장하지 않는다.
