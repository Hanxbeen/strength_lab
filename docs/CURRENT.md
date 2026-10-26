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

## 실제 DB 공급과 공개 선택 구현
| 구성 | 공개 선택안 | 회차 | 적용 조건/한계 |
| --- | ---: | --- | --- |
| Petrizzo 네 종목 | 2 | 24 / 36 | 초급 탐색. 네 동작 경험·알려진 시작 중량, OHP 포함 |
| Helms | 2 | 각 23 | 훈련 경험자 탐색. 스쿼트·벤치만, 1RM 비율/RPE |
| METD | 3 | 각 18 | 숙련 탐색. 근력/PL/RPE 경험 요구 |
| PER 보충표 종목 보존 | 1 | 30 | 숙련 탐색. SBD+프런트스쿼트, 원표와 본문 차이 명시 |
| 과거 OHP 생략 시제품 / PER 종목 대체안 | 0 (내부2) | 24 / 30 | 과거 호환·내부 검토. 일반 공개 아님 |

- 활성 정의7개 / 내부 전체 선택안10개 / 중지 과거 버전1개.
- 정확한 해시5개에 공개 선택8안: 초급2, 훈련경험2, 숙련4, 독립 입문0.
- 같은 연구의 arm/일정 변형 포함. 8개 독립 연구 또는 모든 숙련도 공급 완료가 아니다.
- 입문은 지도자 동반 학습3종 기록 API만 구현. 독립 동작 교육·첫 부하 경로 미완료.
- 초급 연구군 다양성, 중급 완전 SBD 구성은 여전히 공백.
- 최신 추가 결정: coaching-specs/26_PER_SOURCE_LABEL_RELEASE.md.
- 기본 공개 결정: 22_EXPLICIT_SELECTION_RELEASE.md. 25_PER_MAPPING_REVIEW.md는 구버전 검토 기록이다.

## 이번 완료 — PER 원표의 실제 API 공급
- source_id pilot2018-per-source-labels-v1, adapter per-source-labels-v1, arm PER_SOURCE_LABELS.
- 해시 c1a67f3ce6ffc7c0bf325fbb1e20b270c41b883d651bee168a9fb7d2d1a3bf98.
- 원 XLS 수식296개 해석, 훈련275행 산술/캐시 대조 불일치0. xlrd 부재 차단 해소.
- 전체10주30회차515인코딩세트, front squat22세트 보존. 515본세트라고 하지 않는다.
- 실제 운동 종목과 1RM 참조 종목 분리. front squat은 원표의 squat 1RM 참조를 사용하며 별도 front 1RM을 강제하지 않는다.
- 수식 검증은 과학적 효과 승인/원 연구 전체 재현이 아니다. 본문과 보충표 종목 차이, 감독 차이 유지.
- 성인 남성, RT2년/PL1년 이상, 독립 SBD/front squat·RPE 활용·이전 중고부하 경험 입력을 검사한다.
- 원본 셀/수식/목표/변경/실제/휴식/중단 출처가 저장된다. front squat은 SBD 평가 합계에서 제외한다.
- 기존 PER 정의 및 저장된 사용자 기록은 덮어쓰지 않았다.

## API·DB·검증
- GET /v3/routines → 공개8선택안/전체 세션/입력 계약/공급 공백.
- POST /v3/routines/preview → 저장 없는 첫 세션 계산. 생성에서도 조건 재검사.
- 실행은 기존 programme-instances 및 v2 workouts의 변경/휴식/통증/미완료/중단/결과 원장 사용.
- Supabase gttvyfeyrnuspnnphuzk는 재접속 시 INACTIVE였고 복구 후 ACTIVE_HEALTHY 확인.
- 카탈로그 RPC v5 추가: schema_version=3, catalog_revision=5. 새 어댑터만 추가.
- v3/v4 응답 집합 유지: 중지 포함 v3=5행, v4=7행, v5=8행. Python은 중지행 제외.
- 적용 migration: 20261026011453_per_source_label_catalog_v5.sql. 새 원본 DB 삽입 완료.
- 2026-10-26 전체 Python268개 통과, 56.218초, 건너뜀0. 새30회차515세트 전체 실행 포함.
- 실제 HTTPS DB 카탈로그 데이터로 8선택안 미리보기→생성→시작→감량/반복변경→중단→재조회→다음회차 로컬 API 검사 통과.
- 위 실행 검사는 인증 대역 + 임시 SQLite다. 운영 JWT/서버 Postgres 운동 저장 완료가 아니다.
- 보안 advisor는 기존 private 연구 테이블 정책 없는 RLS INFO2건만 유지. 새 경고 없음.
- 근거: data/research/coaching/reviews/per-formula-audit.json, per-formulas.json, per-live-api-verification.json.
- main 병합, Vercel 배포, iPhone 설치는 이번에 수행하지 않았다.

## 다음 작업 — 다시 PER 수식 검토부터 시작하지 않는다
1. 독립 입문 경로를 실제 사용 시나리오로 완성한다: 동작 설명/실습 미디어 출처·사용권, 장비 제약, 첫 부하 선택, 중단/도움 요청, 초급 전환 조건.
   원 연구 그대로의 루틴과 교육용 근거 종합/제품 규칙을 구분한다. 지도자 동반 기록3종을 독립 입문 완료로 세지 않는다.
2. 초급 선택2안은 같은 연구의 주2/3회 변형이다. 새로운 실질적 대안을 준비한다. 논문 개수 목표만 채우지 않는다.
3. 중급 완전 SBD 구성 공백을 해소한다. Vargas 공개표는 충돌이 남아 미공개이며 유료 Colquhoun 업로드를 기다리지 않는다.
4. 위 공급 이후 운영 연결: 기존 Vercel/인증 유지, 서버 DSN·소유자 RLS·실계정 흐름과 iOS 단일 API 연결 검증.
5. 연구·코드·실제 DB가 달라지면 갱신한다. 새 버전 자동 공개나 임의 감량계수 추가 금지.

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
