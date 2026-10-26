# 현재 상태 — 2026-10-26
이 문서가 세션 재개 기준이다. 실제 DB 공급, 로컬 API 검증, 운영 배포를 구분한다.
브랜치 codex/ux-foundations-v2 / GitHub Hanxbeen/strength_lab.

## 고정 결정
- 목적: SBD 중량 향상에 필요한 근거·훈련·수행 기록·다음 선택을 연결한다.
- 숙련도별 실제 선택/시작 가능한 데이터 공급이 최우선이다. UI 재설계, 회복/AI/과금 확장이 공급을 대신하지 않는다.
- 로그인 유지. 운영 인증/권한을 테스트 대역으로 대체해 완료라고 보고하지 않는다.
- OHP/보조 운동 일괄 제외는 폐기했다. 원 연구의 종목과 역할을 보존하고 변경은 제품 결정으로 명시한다.
- 입문(자세/첫 부하 모름)과 초급(독립 수행/알려진 작업 중량)을 구분한다. 릴라 레벨/1RM 크기만으로 분류하지 않는다.
- 연구 조건 / 제품 규칙 / 사용자 자기보고 / 실제 수행을 분리한다. 수행률을 성장 효과로 바꾸지 않는다.
- 새 연구는 발견/검토 후 버전별 채택한다. 자동 공개하지 않는다.
- 명시적 중단·1시간 무활동 중단은 닫힌 stopped, 중단 후 재개 없음. 미기록을 0회/실패로 채우지 않는다.
- BrandUI.swift 토큰, 차콜/아이보리, kg/lb 유지.
- 장기 전략은 PRODUCT_VISION.md: SBD MVP 이후 회복 관찰→근거 기반 회복/영양→종목 확장. 현재 범위 확장 아님.

## 실제 DB 공급 — 2026-10-26 최신
| 경로 | 공개 선택안 | 구성 |
| --- | ---: | --- |
| 입문 | 학습1 (훈련 수 제외) | DB 기반 동작3종, 외부 시연, 선택적 첫 중량·휴식·중단 기록 |
| 초급 | 3 | Petrizzo 주2/3회 + 명시적 근거 종합 SBD 주2회 |
| 중급 | 3 | Helms SB 두 arm + 명시적 근거 종합 SBD 주3회 |
| 숙련 | 4 | METD 세 arm + PER 원종목 보존 구성 |

- 실제 공개 훈련 선택10개. 동일 연구 arm/일정 변형 포함; 독립 연구10개라는 뜻이 아니다.
- 신규 SBD 주2회:16회차96세트 / 주3회:24회차216세트, 모두8주.
- 신규 구성은 ACSM2026 일반 저항훈련 근거를 참고한 제품 종합이다. 정확한 SBD 8주5회 프로토콜이 실험 검증됐다고 주장하지 않는다.
- source_extracted와 reviewed_product_synthesis는 구분한다. scientific_approval=false.
- 상세 현재 공급 결정: coaching-specs/27_ALL_LEVEL_DATA_DELIVERY.md.
- 과거 PER 검토26, 기존 선택22는 그 당시 공급 기록이며 현재 수는 이 문서를 따른다.

## 이번 구현 및 실제 검증
- coaching_programme_catalog_v6 및 coaching_learning_catalog_v1 추가. 기존 v3/v4/v5 응답 유지.
- 실제 DB migration 20261026061650_all_level_synthesis_catalog_v6.sql 적용, 신규 정의3개 저장.
- DB행 수(중지 포함): v5=8, v6=10, 학습=1. 응답 arm 수와 DB 정의 행 수는 다르다.
- GET /v3/routines는 훈련10안과 별도 learning_paths를 반환한다.
- /v3/entry/learning-sessions 소유자별 스냅샷/이벤트/중단/재조회 구현.
- 입문 중량을 사용할 때 같은 소유자의 완료 원기록·event_id·중량·시각 검증. 1RM/자세 인증/자동 해금 없음.
- 공개10안 실제 HTTPS DB 조회 → 로컬 API 미리보기/생성/시작/감량/반복변경/중단/재조회/다음 회차 검증 통과.
- 입문 통증/불확실/누락/중복/권한/원기록 불일치/1시간 무활동 검사 통과.
- 전체 Python277개 통과,57.929초,건너뜀0.
- 근거: data/research/coaching/reviews/all-level-live-api-verification.json.
- 이 검증은 인증 대역+임시 SQLite다. 실제 JWT/서버 Postgres/iPhone 사용자 검증과 구분한다.
- 보안 advisor 기존 private 연구 테이블 RLS 정책 없음 INFO2건만 유지, 신규 경고 없음.
- supply_audit.all_levels_data_ready는 최소 MVP 데이터 준비; all_levels_complete/client_execution_verified는 여전히 false.
- main 병합, 운영 배포, 아이폰 설치는 아직 하지 않았다.

## 다음 작업 — 데이터 재수집부터 반복하지 않는다
1. iOS가 새 /v3/routines 및 입문 학습 API를 실제 소비하도록 연결 상태를 확인한다.
2. 실계정 인증/소유자 원장과 테스트 서버를 연결해 아이폰 설치 전 통합 검증한다.
3. 아이폰 설치 및 선택→입력→운동→변경/휴식/중단→결과→다음 선택을 검사한다. 외부 시연 링크도 실제 재생 확인한다.
4. 사용자 확인 후 운영 배포. 사용자 최신 순서는 데이터 준비→아이폰 테스트→운영 배포이며 뒤집지 않는다.
5. 자기보고 자세/중량의 한계, 연구군 다양성, 제품 구성의 효과 미검증을 유지한다. 새 연구 자동 공개 금지.

## 재현과 인수인계
- Mac: /Users/hanbeen/codex-workspace/strength_lab.
- Python: .venv-coaching/bin/python (Python3.13, 영속 작업 디렉터리). 이전 /tmp 환경은 없어졌다.
- 의존성 requirements-test.txt / backend/requirements.txt. xlrd==2.0.2는 원표 감사용.
- 원표: python -m scripts.decode_per_formulas → scripts.audit_per_formulas → scripts.build_per_source_labels.
- 데이터 SQL: python -m scripts.export_per_source_sql (허용 해시만 출력). 기존행 덮어쓰기 없음.
- 전체 검사: python -m scripts.verify_tests. 원문 캐시 필요; 건너뜀은 실패.
- 실제 카탈로그: 정상 SUPABASE_URL / SUPABASE_PUBLISHABLE_KEY 설정 후 python -m scripts.verify_live_routine_selection.
- 서버 WORKOUT_POSTGRES_DSN은 비밀 설정, TLS verify-full. Vercel 미설정 시503 유지. SQLite fallback을 운영 성공으로 취급하지 않는다.
- execution_private 원장5테이블·소유자RLS는 기존 구현. 운영 재검증은 별도다.
- Swift/iOS 변경 시 해당 테스트·빌드를 수행한다. 이번은 Python/데이터 변경이며 iOS 빌드 결과를 주장하지 않는다.
- 데스크톱 원격 연결 인증서 오류는 NODE_USE_SYSTEM_CA=1 실행으로 연결된 상태다. TLS 검증을 끄지 않는다.
