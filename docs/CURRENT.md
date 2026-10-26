# 현재 상태 — 2026-10-27
이 문서가 세션 재개 기준이다. 실제 DB 공급, 로컬 API 검증, 운영 배포를 구분한다.
브랜치 codex/ux-foundations-v2 / GitHub Hanxbeen/strength_lab.

## 고정 결정
- 목적: SBD 중량 향상에 필요한 근거·훈련·수행 기록·다음 선택을 연결한다.
- 숙련도별 실제 선택/시작 가능한 데이터 공급이 최우선이다. UI 재설계, 회복/AI/과금 확장이 공급을 대신하지 않는다.
- 로그인 유지. 운영 인증/권한을 테스트 대역으로 대체해 완료라고 보고하지 않는다.
- 2026-10-26 사용자 확정: Supabase 인증·DB + 기존 Python API 유지. Vercel 필수 아님. API 구현 정리 후 와이어프레임 설계.
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
- 전체 Python287개 통과,57.604초,건너뜀0(2026-10-26 API 보완 포함).
- 근거: data/research/coaching/reviews/all-level-live-api-verification.json.
- 이 검증은 인증 대역+임시 SQLite다. 실제 JWT/서버 Postgres/iPhone 사용자 검증과 구분한다.
- 보안 advisor 기존 private 연구 테이블 RLS 정책 없음 INFO2건만 유지, 신규 경고 없음.
- supply_audit.all_levels_data_ready는 최소 MVP 데이터 준비; all_levels_complete/client_execution_verified는 여전히 false.
- main 병합, 운영 배포, 아이폰 설치는 아직 하지 않았다.

## iOS 연결 구현 — 2026-10-26
- 홈/루틴/기록을 새 서버 경로로 연결. 이전 기기 기록은 별도 접근으로 보존.
- 숙련도별 목록, 적용 조건/1RM 입력, 서버 미리보기→선택→회차 시작 구현.
- 세트 중량/횟수/RPE, 사유, 휴식, 중단, 결과 차트, 다음 회차, 루틴 마무리 API 소비.
- 입문 학습/첫 중량 관찰 및 기존 학습 기록 API 소비.
- 계정별 원자적 outbox에 미확인 요청 ID/리비전 보존. 인증 우회/자동 재전송 없음.
- kg/lb 입력 환산 및 결과 표시. 기존 BrandUI 토큰 사용.
- 무서명 iphoneos Debug 빌드 성공, Swift 검증16개 프로그램 통과.
- 실계정 실행과 실기기 UI 검증은 아직 아님. 상세: coaching-specs/28_IOS_RUNTIME_CONNECTION.md.

## 현재 설치 차단과 다음 작업
1. devicectl에서 아이폰2대 모두 unavailable. USB 연결·잠금 해제·기기 신뢰 필요.
2. 서명 프로파일 없음. 자동 provisioning 재시도도 Xcode No Accounts. Apple 개발 계정 설정 필요.
3. 앱의 HTTPS 테스트 API 주소 미설정. MUGEMUGE_API_URL 빌드 설정으로 v2/v3 테스트 서버를 지정해야 함. Vercel은 필수 아님. 우선 맥북에서 Python API 실행 후 기기 접근 주소/인증서 설정을 검토한다. 실제 사용자 서비스에는 상시 서버가 필요하다.
4. 위 조건 해소 후 실계정/서버 저장→아이폰 설치/사용자 흐름 확인. 운영 배포는 이후.
5. 입문 완료 후보 선택→원기록 ID 연결 UI와 사후 최대중량/비교 조건 UI 구현. 직접 중량 수정 시 원기록 연결 해제. 미측정 마무리 및 종료 후 측정 기록 추가 지원. 실제 화면 조작 인수는 남아 있다.
6. 데이터 재수집으로 되돌아가지 않는다. 최신 DB10훈련 선택/입문1의 실행 연결이 다음 검증 대상.
7. main 병합/운영 배포/아이폰 설치는 아직 수행하지 않았다.

## 재현과 인수인계
- Mac: /Users/hanbeen/codex-workspace/strength_lab.
- Python: .venv-coaching/bin/python (Python3.13, 영속 작업 디렉터리). 이전 /tmp 환경은 없어졌다.
- 의존성 requirements-test.txt / backend/requirements.txt. xlrd==2.0.2는 원표 감사용.
- 원표: python -m scripts.decode_per_formulas → scripts.audit_per_formulas → scripts.build_per_source_labels.
- 데이터 SQL: python -m scripts.export_per_source_sql (허용 해시만 출력). 기존행 덮어쓰기 없음.
- 전체 검사: python -m scripts.verify_tests. 원문 캐시 필요; 건너뜀은 실패.
- 실제 카탈로그: 정상 SUPABASE_URL / SUPABASE_PUBLISHABLE_KEY 설정 후 python -m scripts.verify_live_routine_selection.
- 서버 WORKOUT_POSTGRES_DSN은 비밀 설정, TLS verify-full. staging/production 또는 Vercel에서 DSN 미설정 시503 유지. SQLite fallback을 운영 성공으로 취급하지 않는다.
- execution_private 원장5테이블·소유자RLS는 기존 구현. 운영 재검증은 별도다.
- iOS 빌드/검증은 위 최신 항목을 따른다. 무서명 빌드 성공을 실기기 설치 성공으로 표현하지 않는다.
- 데스크톱 원격 연결 인증서 오류는 NODE_USE_SYSTEM_CA=1 실행으로 연결된 상태다. TLS 검증을 끄지 않는다.

## 연결 후 작업 체크포인트 — 2026-10-26
- Mac 온라인, 여유69GiB. Vercel CLI whoami 및 프로젝트 API200으로 인증 확인.
- 조회 가능한 Vercel 프로젝트5개는 strength_lab과 연결돼 있지 않음. 프로젝트 생성/배포 없음.
- 프로젝트 .env/.env.local/backend/.env 및 현재 프로세스에서 WORKOUT_POSTGRES_DSN 미확인. 다른 앱의 비밀값을 재사용하지 않음.
- 입문 완료 기록을 명시적으로 선택해 kg 원값/event_id/workout_id 전달; lb 표시 환산으로 원값을 바꾸지 않음.
- GET programme 상세에 evaluation_exercise_ids 추가. 서버가 고정 source에서 비교 종목을 반환.
- 사후 측정·same/different/unknown 명시 선택, 미측정 종료, 이전 평가 supersedes_id 보존, 동일 요청 재시도.
- 변경 후 무서명 iphoneos Debug 빌드 성공, Swift16개 프로그램 통과, Python277개60.160초 통과.
- 위 검증은 실제 로그인/서버 Postgres/시뮬레이터 조작/아이폰 검증이 아니다.
- 사용자 확인: iOS 앱에 Vercel 자체는 필수 아님. Python 실행 위치 선택과 앱 배포를 분리. 운영 배포는 실기기 테스트 이후 원칙 유지.

## API 인수 상태 — 2026-10-27
- 최신 계약/실행법: coaching-specs/29_API_IMPLEMENTATION_HANDOFF.md.
- /v3/runtime-readiness: 인증·전체 숙련도 공급·원장5테이블 읽기 확인. 쓰기/사용자 효과/화면 검증 완료를 뜻하지 않음.
- scripts.serve_api: Supabase Auth·Postgres 필수, 호스팅 독립 실행. scripts.verify_runtime_connection: 실제 토큰 읽기 검증, 인증 대역 없음.
- 인증 응답 오류와 토큰 만료/제공자 장애 구분. 운영환경 SQLite 대체 금지를 Vercel 외 호스트에도 적용.
- 실제 HTTPS 카탈로그 재검증: 초급3/중급3/숙련4, 입문학습1. 공개10안 로컬 생명주기 통과. 인증 대역+임시SQLite라는 한계 유지.
- 실행환경 재확인: 현재 Mac 프로세스에 WORKOUT_POSTGRES_DSN, MUGEMUGE_TEST_ACCESS_TOKEN, MUGEMUGE_API_URL 없음.
- 공급 및 주요 운동 API 코드/로컬 계약은 준비. 실계정 Postgres 저장·2계정 격리·동시성·앱실행 인수는 미완료.
- 와이어프레임에는 이미 구현된 성공/입력부족/조건거절/연결실패/충돌/중단 상태를 반영. 이번 작업에서 새 화면 설계를 시작하지 않음.
