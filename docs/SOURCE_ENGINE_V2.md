> 호환 구현/과거 설계 기록. 현재 운영·공개 상태와 작업 순서는 [CURRENT.md](CURRENT.md)를 따른다. 이 문서만으로 배치 또는 처방 공개를 활성화하지 않는다.

# 원문 운동 구성 엔진 v2 — 구현 및 검증

2026-10-11. v1의 항상0/대기 상태와 별도인 실제 성공 경로다.
공개 명칭은 source template이며 임상/과학적 승인이나 개인 효과 보장이 아니다.

## 실제 생성 데이터

| 원문 | 실험군 | 기간/빈도 | 세션 | 작업 세트 |
|---|---|---|---|---|
| PMC11140948 / PMID38816857 | SG, DG | 8주 × 주2회 | 각16 | 각160 |
| PMC5003312 / PMID27625750 | LOW, HIGH | 8주 × 주3회 | 각24 | 각504 |
| PMC6974452 / PMID32009980 | TRAD | 8주 × 주3회 | 24 | 432 |

합계 원문3편, 군별 구성5개, 세션104회, 작업 세트1760개.
독립 연구 수를 검증한 숫자가 아니며, 논문/실험군/파생 루틴을 혼동하지 않는다.
PMC6974452 ISO군은 세트 후 등척성 이벤트를 아직 지원하지 않아 제외. 이 개입을 지워 TRAD로 바꾸지 않는다.
기존 PMC8041766은 공통훈련과 추가훈련의 완전한 편성 문제로 이 어댑터 목록에 포함하지 않는다.

## 데이터와 코드

- research_engine/adapters.py: 원문 버전 SHA와 PMID 확인, 해당 절·문단에서 유일한 근거 매치, 필드별 출처 연결.
- research_engine/core.py: 타입/범위/필수 출처/값 변경 검사, 전체 일정 생성, 대상자 범위 비교, 초기 중량, 진행 규칙, 달력 제약, 설명 생성.
- research_engine/batch.py: 전체 성공 시에만 원자적 활성 버전 변경. SQLite로 오프라인 재현 및 중복 적재 검사.
- research_engine/export.py: 원문 전체나 반복된 세션 없이 정의만 Supabase에 적재. v1 published 테이블과 분리.
- research_engine/run.py: 알려진 원문 가져오기 → 버전 확인 → 추출 → 생성 → SQL → 선택적 DB 저장. --offline은 네트워크 미사용.
- backend/source_repository.py: 실제 Supabase source_programme_catalog RPC 조회 후 컴파일 계약 검증.
- GET /v2/source-programmes: 현재 버전의 원문 기반 정의.
- POST /v2/source-programmes/prepare: 명시적 사용자 조건/선택으로 한 세션 준비. 프로필은 저장하지 않음.

## 임의 값 방지

- 하프 스쿼트/트랩바 데드리프트의 1RM은 동작별로 요구한다. 일반 스쿼트 수치를 자동 대입하지 않는다.
- 첫 세션의 초기85%와 이후 사용자가 수행한 실제 중량을 구분한다.
- RIR2를 임의의 1RM비율로 바꾸지 않는다.
- RM 기반 루틴은 해당 운동의 최초10RM/30RM 측정 여부와 실제 중량 입력을 요구한다.
- 준비운동, 원문에 없는 운동 사이 휴식, 명시되지 않은 운동 순서, 불가리안 스플릿 스쿼트의 다리별 반복 해석은 명시적인 사용자 선택으로 보존한다.
- 원문의 최소3분 휴식은 최소값으로 보존한다. 원문에 없는 진행 kg 폭을 생성하지 않는다.
- 장비 반올림은 원문 목표 중량과 별도 product policy로 기록한다.
- 구성은 SOURCE_STRUCTURED / REQUIRES_EXPLICIT_SETUP. 입력 해결 후 READY인 세션도 SOURCE_BASED_WITH_EXPLICIT_USER_CHOICES로 표시한다.
- 최초 구성에는 날짜를 임의로 붙이지 않는다. 별도 달력 검증은 주당 횟수와 비연속일/48시간 조건을 검사한다.

## 검증 결과

실제 원문 캐시를 사용한 신규16개 테스트 통과. 기존77개 포함 전체93개 테스트 통과.
신규 검증은 source hash변조, 필드변조/출처삭제, 미지원 원문, 잘못된 동작1RM, 장비반올림, RIR 비환산, 진행범위, 회복간격, 누락입력, 대상자차이, 중복import, 실패시기존카탈로그보존을 포함한다.
socket을 차단한 상태에서 추출 결과 동일성과 세션 준비·설명 생성 성공을 확인했다. 외부 AI 호출은 없다.
독립 전문가의 이중 추출 검증은 아직 아니다. 숫자93은 과학적 정확도 지표가 아니다.

실제 Supabase에 정의5개 적재. FastAPI TestClient가 실제 DB를 읽어 GET200/5개, 준비POST200/READY/10세트/설명3개, 잘못된동작1RM POST422를 반환했다.
FastAPI 공개 서버를 배포한 결과는 아니다. Supabase RPC는 실제 배포되었다.

## 현재 남은 경계

1. iOS의 schema-v2 실행/기록 UI 연결은 미완료. 기존 v1에5개를 억지로 끼워 넣지 않는다.
2. 임의의 새로운 논문을 해석하는 범용 추출기는 아니다. 승인된3개 문서 버전의 어댑터부터 검증한다.
3. 출처가 바뀌면 자동 차단한다. 새로운 과학적 결론의 채택/근거 충돌 해결/철회 감시는 별도 단계다.
4. 평가용 독립 참조 세트와 전문가 검토, 세트별/주차별 변동 규칙 및 클러스터 중재 확대는 남아 있다.
5. GitHub workflow는 수동 트리거 코드까지 작성. 원격 푸시와 RESEARCH_DATABASE_URL 비밀 설정 없이는 무인 운영되지 않는다.
6. 원문에 없는 자세·중단·안전 지침을 논문에서 나온 것처럼 제공하지 않는다.

## 원문/라이선스 출처

원문 XML은 로컬 캐시이며 커밋·API에 포함하지 않는다. 원문 기반 구조화 사실과 출처 링크만 저장한다.
- PMC11140948: https://doi.org/10.1186/s13102-024-00911-8 — 원문 표기 CC BY4.0.
- PMC5003312: https://doi.org/10.5812/asjsm.29247 — 원문 표기 CC BY-NC4.0. 원문 재배포나 라이선스 권한 확보를 주장하지 않는다.
- PMC6974452: https://doi.org/10.3389/fphys.2019.01571 — 원문 표기 CC BY4.0, Schoenfeld et al.(2020).
원문을 직접 요약·구조화한 데이터이며 원문 저자의 승인이나 공식 소프트웨어가 아니다.

## 재현

    python -m research_engine.run --directory data/research/source-build
    RESEARCH_ENGINE_SOURCE_DIR=data/research/source-build/sources python -m unittest tests.test_source_engine -v
    python -m research_engine.run --directory data/research/source-build --offline --persist

마지막 명령만 서버의 RESEARCH_DATABASE_URL과 psql이 필요하다. 설정이 없으면 DB 저장 성공으로 처리하지 않는다.
