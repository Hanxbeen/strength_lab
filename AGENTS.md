# 작업 시작
1. README.md와 docs/CURRENT.md를 읽고 git status를 확인한다.
2. docs/coaching-specs/SERVICE_PRINCIPLES.md와 09_STRATEGY_RESET.md가 현재 제품 방향이다.
3. 날짜별 검토 문서는 당시 기록이며 현재 출시 상태로 인용하지 않는다.

# 변경 기준
- 가정을 명시하고 필요한 변경만 수행한다. 완료 조건을 먼저 정하고 검증한다.
- 후보 논문 수·테스트 수를 과학적 승인 또는 제품 효과로 표현하지 않는다.
- 연구 조건, 제품 규칙, 사용자 자기보고, 실제 수행을 분리한다.
- 미응답·모름·미질문을 근력 실패나 정상 회복으로 추정하지 않는다.
- 새 루틴 자동 공개, 미검토 대상 처방 확대, 사유 기반 임의 감량 계수는 금지한다.
- 앱은 BrandUI.swift의 디자인 토큰을 사용한다.
- 현재 사용처 확인 없이 호환 코드·마이그레이션·사용자 기록을 삭제하지 않는다.
- 완료 내용·실행한 테스트·남은 제약은 docs/CURRENT.md에 갱신한다.

# 검증
- Python: python -m scripts.verify_tests (실제 원문 캐시 필요; 건너뜀은 실패)
- Swift 기록: bash scripts/test_ios_records.sh
- iOS: apps/ios에서 xcodegen generate 후 xcodebuild
- 빌드·설치 성공과 실제 사용자 상호작용 검증은 구분해 보고한다.
