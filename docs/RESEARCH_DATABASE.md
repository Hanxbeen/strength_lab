# 연구 배치 → DB → 앱 응답

2026-10-11 실제 Supabase 프로젝트 strength_lab에서 확인했다.

## 이번 실행 결과

- 원문 XML 후보: 목표 20편 중 3편. 제목 기준 후보는 9편이었다.
- PMID: 38816857, 33846516, 32269656. 마지막 논문은 supporting_or_unverified 분류다.
- 원문 셀 회귀 검사: 12/12. 사람 검수·프로그램 재현성 전체의 정확도 지표가 아니다.
- 승인된 실행 루틴 0, 승인된 수치 차트 0. 자동으로 승인 상태를 만들지 않았다.
- DB: 배치 1건, 논문 3건, 검토 후보 3건. 원문 SHA-256·표/문단 근거·필드별 미검증 상태·차단 사유 저장.
- 동일 입력 재저장: 배치 1건·후보 3건 유지. 한 트랜잭션이며 동일 입력 해시로 중복을 막는다.

## 저장 구조

| 테이블 | 내용 | 공개 접근 |
|---|---|---|
| research_internal.batch_runs | 배치 입력 해시, 목표/결과, 감사 요약 | 차단 |
| research_internal.papers | 실제 논문 메타데이터와 원문 위치 | 차단 |
| research_internal.protocol_candidates | 원문 해시, 근거 패킷, 검토 상태, 공개 차단 사유 | 차단 |
| public.research_protocol_versions | 별도로 승인·발행한 불변 루틴 버전 | 공개 상태만 읽기 |
| public.research_catalog_state | 최근 배치의 집계 수치 | 읽기 |

내부 테이블은 RLS 및 스키마/테이블 권한으로 보호한다. 공개 앱 키는 쓰기 권한이 없다.
공개 후 내용 변경은 금지하며 회수만 가능하다. 회수한 버전을 조용히 재공개할 수 없다.
자동 배치 저장기는 approved/publishable 항목의 반입을 거부한다. 사람 검수 후 정식 발행은 별도 경로다.

## 실제 응답 경로

- Supabase POST /rest/v1/rpc/research_catalog: security invoker, RLS 적용. 앱의 기본 데이터 경로다.
- FastAPI GET /v1/protocols: 같은 DB RPC를 읽는다. SUPABASE_URL과 SUPABASE_PUBLISHABLE_KEY 환경변수를 사용한다.
- API 서버 주소를 앱 MugeMugeAPIURL로 제공하면 FastAPI 경로를 사용한다. 없으면 실제 Supabase RPC를 조회한다.
- /v1/demo-protocols 및 앱 번들 예시는 연구 목록과 분리하며 홈의 기록 연습에만 사용한다.
- DB 오류/미설정은 FastAPI 503, 앱 연결 실패 상태로 처리한다. 빈 목록 성공으로 위장하지 않는다.

확인한 응답:

    {"schema_version":1,"items":[],"metadata":{"requested":20,"candidates":3,"awaiting_review":3,"last_batch_id":"batch-ae787a6797b6dec1572f4b41","checked_at":"2026-10-11T02:12:53.153678+00:00"}}

items가 빈 이유는 DB 미연결이 아니라 승인 버전이 0건이기 때문이다. 앱은 후보 3편·검토 대기 3편을 별도로 표시한다.
이 문서는 실행 가능한 루틴 10~20개 확보를 주장하지 않는다.

## 재실행

기존 research_oa_v2 → research_evidence_gate → research_protocol_audit → research_review_queue → research_release_gate 순서를 사용한다.
각 단계의 --output을 같은 실행 폴더에 지정해 이전 자료를 보존한다.

    python3 -m scripts.research_store --directory data/research/runs/20261011 --output /tmp/research-import.sql

이 명령은 공개하지 않고 권한 있는 서버/운영자가 실행할 SQL 트랜잭션을 만든다. 이번 SQL은 연결된 DB에서 실제 실행했다.
기존 GitHub 스케줄에는 DB 쓰기 자격을 추가하지 않았다. 무인 DB 적재는 아직 연결하지 않았다.

## 검증

Python 기존·신규 65개 테스트, Swift 14개 테스트, Swift LiveCatalog 및 Python repository 실제 RPC 호출 통과.
FastAPI TestClient의 GET /v1/protocols도 실제 DB 조회로 HTTP 200, DB 오류 주입 시 HTTP 503을 확인했다. 별도의 FastAPI 서버를 공개 호스트에 배포했다는 의미는 아니다. 앱은 배포된 Supabase RPC를 직접 사용한다.
익명 역할에서 공개 응답 확인, 비공개 스키마 접근 불가, 공개 테이블 쓰기 불가 확인.
보안 Advisor는 조치 후 항목 0건. RLS 설명: https://supabase.com/docs/guides/database/postgres/row-level-security
성능 Advisor의 새 FK 인덱스 항목은 수정했다. 기존 workout_snapshots 및 방금 생성된 research_catalog_last_batch_idx의 미사용 안내는 유지했다. 새 인덱스에 사용 통계가 아직 없는 것이므로 바로 삭제하지 않는다. 설명: https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index
