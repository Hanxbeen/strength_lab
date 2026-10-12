# 루틴 구성·응답 명세

문서 ID: RUN · 버전 0.2 · 2026-10-12 KST
상태: 설계안. 아래 v3 계약은 기존 v1/v2에 구현됐다는 뜻이 아니다.  
연결 원칙: P02~P09 · 선행: [문헌 검토·근거 데이터](01_EVIDENCE_REVIEW.md)

## 1. 용어와 책임

Programme은 여러 주에 걸친 전체 프로그램, Session은 하루 운동, Set은 작업 세트다. 연구의 Arm, 실행 가능한 ProgrammeDefinition, 사용자의 ProgrammeInstance를 구분한다. ‘루틴 완료’는 화면과 API에서 session_closed와 programme_closed로 명확히 나눈다.

연결 구조는 SourceSnapshot → Arm/EvidenceClaim → DecisionRule → ProgrammeDefinition → ProgrammeInstance → SessionInstance → SetPlan/Event → Result다. 각 연결은 ID와 버전을 가진다. 루틴 배열만 반환해 이 관계를 지우지 않는다.

## 2. 프로그램을 제공할 조건

RUN-01. ProgrammeDefinition은 목표·동작·사용자 적용 조건·전체 일정·주차별 구성·진행 규칙·종료·평가·필요 장비를 명시한다. 근거와 무관한 근육군·기간 확대를 자동으로 붙이지 않는다. 자동 적용 가능한 규칙과 사용자 확인이 필요한 선택을 함께 명시한다.

RUN-02. 출처 유형은 source_reported / evidence_synthesis / product_policy / user_override다. 프로그램은 source_reproduction(원 연구 조건 재현) 또는 evidence_informed(근거 종합)으로 설명한다. 사용자 변경 후에는 변경 항목과 원 연구 대비 차이를 표시한다. 재현 여부는 효과 보장이나 데이터 품질 점수가 아니다.

RUN-03. evidence_readiness, client_compatibility, input_readiness, release_status를 별도 필드로 둔다. 입력을 채웠다고 reviewed/released가 되지 않는다. 실행기는 지원하지 않는 클러스터·등척성·단측 계수 등을 평범한 세트로 축약하지 않는다.

RUN-04. 예상 소요 시간은 연구 보고값인지 앱 추정값인지 표시한다. 세트 수·휴식·준비 시간을 이용한 추정이면 공식·포함 범위·버전을 남긴다. 논문에 없는 피로 점수나 완료 예상 시간을 연구 결과로 표시하지 않는다.

## 3. 준비·1RM·프로그램 시작

Readiness는 필요한 입력, 불일치, 미지원 조건을 모두 구조화해 반환한다. ‘문제가 있어요’만 반환하지 않는다. 각 issue에 code, field, reason, blocking, allowed_actions, evidence/rule_ref를 둔다.

MaxRecord는 record_id, exercise_variant_id, measured/estimated, 값·원단위·canonical_kg, 측정일, 측정 프로토콜 또는 추정 공식 버전, 자기보고 여부를 보존한다. 현재 최고값만 보관하지 않는다. 자동 추정은 검토된 공식·적용 범위가 있을 때만 사용하며 측정값으로 승격하지 않는다.

등록값이 없으면 등록·추정 지원 여부·별도 준비 경로를 보여준다. 최대중량 측정을 무조건 요구하지 않는다. 측정 가이드를 제공하려면 해당 가이드의 검토와 실행 환경 조건이 먼저 필요하다. 미검토 측정 처방은 제공하지 않는다.

RUN-05. ProgrammeInstance는 definition/version, release_id, evidence_snapshot_refs, rule_versions, 당시 프로필·max_record_refs·장비 조건·선택, 기준 달력·사용자 시간대를 고정한다. 이후 기록 정정·1RM 갱신은 새로운 참조 또는 명시적 rebase로 처리하며 과거 계획을 덮어쓰지 않는다.

RUN-06. 첫 등록 시 임의의 후반 세션을 선택해 최초 부하 조건을 우회하지 못하게 한다. 프로그램 중간 합류는 별도 resume/import 절차로 과거 수행 근거·현재 단계·누락·사용자 선택을 기록한다. 근거가 없으면 신규 프로그램의 시작 경로를 제공한다. 이미 수행한 기록을 날짜만으로 자동 추정하지 않는다.

## 4. 중량과 세트 모델

SetPlan에는 source_target, individual_baseline_target, active_target을 구분한다. 중량 변경 제안은 active_target의 새 revision이며 individual_baseline_target은 유지한다. 이벤트의 실제값은 actual에 별도로 저장한다.

목표에는 repetitions 범위, sets 구조, percent_1rm/RM/RIR/속도 등 강도 표현, reference_record_id, effort/failure 정의, tempo, 동작 순서, rest_constraint를 원형대로 둔다. RIR을 임의 %1RM으로 변환하지 않는다.

장비와 중량 의미: barbell_total / dumbbell_each / dumbbell_pair / machine_stack / added_load 등을 명시한다. 단측 반복은 per_side/total과 side를 저장한다. 기구 스택 표시를 다른 장비의 동일 kg과 직접 비교하지 않는다. 체중 동작의 부가 중량 0과 바벨 전체 중량 0은 같은 의미가 아니다.

canonical_kg로 계산하고 원 입력값·unit을 보존한다. 표시 전환은 기록을 바꾸지 않는다. 장비 반올림은 선택된 정책에 따라 원 계산값, 실행 가능한 후보, 선택값, 차이를 기록한다. 최소 장비 중량보다 낮으면 0으로 반올림하지 않고 장비/대안 선택으로 반환한다.

## 5. 수행 상태와 기록 이벤트

Session 상태: prepared → active; active ↔ resting; active/resting → paused → 이전 상태; active/resting/paused → closed. closed에는 completed/partial/stopped/abandoned의 outcome을 둔다. completed는 계획된 모든 작업 세트에 수행 기록이 있다는 뜻이며 반복수·중량 목표 달성과는 별도다. partial은 일부 수행 후 사용자 종료, stopped는 시작 후 수행 없이 명시적 종료, abandoned는 사용자가 확인한 포기다. 네트워크 무응답만으로 abandoned를 확정하지 않는다. 모든 세트가 skipped인 세션을 ‘목표 완료’로 표시하지 않는다. UI는 ‘운동 종료’와 ‘목표 달성’을 구분한다.

| 이벤트 | 의미와 필수 처리 |
|---|---|
| set_recorded | 실제 중량·반복수·계수·수행 시각을 한 요청에 기록. 목표와 다르면 차이 자동 보존 |
| load_selected | 수행 전 선택. 변경값과 이유(모름/응답 안 함 포함)를 저장. 실제 수행을 대신하지 않음 |
| set_skipped | 미수행 이유를 선택적으로 기록. 수행 0회와 구분 |
| rest_started/ended | 기준 세트, 시작·종료, 목표, 실제시간, 조기 종료·연장·중단 구분 |
| session_paused/resumed | 앱 진행 상태. 생리적 휴식의 경과 시간을 정지시키는 것으로 해석하지 않음 |
| session_closed | 남은 계획은 not_attempted, 진행 중 세트는 incomplete_or_unknown으로 확인. 완료 결과와 미확인 구분 |
| record_corrected | 원 이벤트를 참조하는 정정. 이전 내용·수정 이유·시각을 보존하고 파생 결과 재계산 |
| exercise_substituted/extra_set | 원 계획과 연결된 이탈 기록. 자동 동등성·과학적 적합성을 부여하지 않음 |
| session_rescheduled | 기존 달력과 새 달력, 휴식·빈도 제약 검사, 위반·사용자 선택 기록 |

RUN-07. 서버가 받는 실제 중량을 무시하고 이전 선택값으로 대체하지 않는다. actual 필드가 누락되면 확인이 필요한 상태로 저장하거나 필드 오류를 반환한다. 추측한 값으로 성공 응답하지 않는다. 정정·추가·대체 기능은 클라이언트 지원 여부를 명시한다.

각 이벤트는 event_id, instance_id, expected_revision, client_occurred_at, server_received_at, timezone, device_id, payload를 가진다. 시계가 역행하거나 서버와 크게 차이 나면 time_quality=uncertain으로 표시하고 자동 휴식 판정을 보류한다. 오프라인 실제 수행은 통신 지연 때문에 버리지 않는다. 플랫폼이 지원하면 monotonic elapsed와 타이머 구간도 함께 보존한다.

RUN-08. 휴식은 단순히 ‘마지막 클릭까지의 차이’로 확정하지 않는다. 세트 종료/다음 시작 등 관측 구간과 사용자의 확인을 구분한다. 미관측 휴식은 null이다. 최소 휴식보다 더 쉰 경우를 부족으로 처리하지 않는다. 정확한 고정값(eq)과 최소값(gte)은 보존하고 차이 계산도 구분한다.

## 6. 응답·가이드 계약

응답에는 instance_id/revision, pinned_versions, plan, actuals, deviations, rests, summary, decision, available_actions, unsupported_capabilities를 포함한다. 평소 화면은 현재 동작·선택 중량·반복수·휴식·다음 행동을 우선한다. 복잡한 근거는 상세 화면에 둔다.

available_actions는 상태 전이 검사와 같은 규칙에서 생성한다. paused 상태에서 rest_end 버튼을 활성화하거나 closed 상태에서 finish를 제안하지 않는다. 가이드에는 reason, basis, rule_ref, applies_to, missing_inputs, limitations를 둔다. 서로 충돌하는 가이드를 병렬로 내보내지 않는다.

증상 보고 등 우선 확인이 필요한 상태는 change_load, set_recorded, skip, check-in 등 어떤 경로에서 들어와도 같은 판단으로 연결한다. 경로에 따라 안내가 사라지지 않아야 한다. 세션 종료 시에도 미해결 사항을 결과에 보존한다.

루틴 목록은 실행 가능한 released 프로그램과 근거 열람용 자료를 구분한다. 비슷한 프로그램 정렬에는 장비·일정·목표 적합성을 먼저 사용하고, 성장률 보장을 근거로 순위를 만들지 않는다. 근거가 없는 개인 맞춤 점수는 표시하지 않는다.

### 목표 API 경계(제안, 미구현)

| 계약 | 용도 |
|---|---|
| GET /v3/programmes | released 정의의 설명·적용 범위·상태·근거 요약 |
| POST /v3/readiness | 조건 확인과 해결 행동. 저장하지 않음 |
| POST /v3/max-records | 소유자별 측정/추정 기록 등록 |
| POST /v3/programme-instances | 전체 프로그램 시작, idempotency_key와 계획 고정 |
| POST /v3/programme-instances/{id}/sessions | 순서·일정·시작 조건을 검증한 세션 시작 |
| POST /v3/sessions/{id}/events | 실제 수행·변경·휴식·정정 이벤트 |
| GET /v3/programme-instances/{id} | 다른 기기·재설치 후 현재 인스턴스와 이력 복구 |
| GET /v3/programme-instances | 소유자별 진행/완료 목록과 페이지 커서 |
| GET /v3/sessions/{id} | 고정된 계획·이벤트로 재구성한 세션 |
| GET /v3/programme-instances/{id}/summary | 세션·프로그램 종료 분석과 비교 가능성 |
| POST /v3/decisions/preview | 변경하지 않고 후보·근거·fallback 반환 |
| POST /v3/decisions/{id}/apply | 사전 상태 revision 확인 후 선택 적용 |
| POST /v3/programme-instances/{id}/close | 프로그램 종료 이유·평가 누락·완료 범위 보존 |

모든 개인 데이터 작업은 검증된 인증 주체에 귀속한다. Body의 owner_id는 권한 근거가 아니다. 공개 카탈로그에 개인 프로필·기록을 섞지 않는다. Unknown 필드·enum은 명시적 오류를 반환하고 원치 않는 형 변환을 허용하지 않는다.

RUN-09. 동일 시작/이벤트 요청은 저장된 idempotency 결과를 먼저 확인한다. 카탈로그 갱신·일시 장애 때문에 이미 성공한 시작 요청의 재시도가 실패하지 않아야 한다. 동일 키·다른 내용은 409다. 동일 요청 재시도와 후속 수정은 구분한다.

에러는 code, field_issues, retryable, available_actions, request_id를 가진다. 로그인 401, 접근 불가/타인 객체 404, 상태·revision 충돌 409, 입력 문제 422, 저장·근거 서비스 장애 503을 구분한다. 입력 오류를 KeyError라는 이유만으로 404로 바꾸지 않는다.

## 7. 실패·복구와 보존

낮은 네트워크 품질에서는 로컬 이벤트를 보존하고 동기화 여부를 표시한다. 여러 기기의 충돌은 last-write-wins로 세트를 덮지 않고 서버 revision 확인·재구성·사용자 확인으로 처리한다. 서버 접수 전에 성공 저장으로 단정하지 않는다.

RUN-10. 입력 크기·요청 빈도·이력 용량 제한을 둔다. 한도를 넘으면 읽기·종료·내보내기·복구 경로는 유지한다. 이벤트 한도 때문에 운동을 종료할 수 없게 만들지 않는다. 구체 제한은 부하 시험과 함께 배포 설정에 명시한다.

현재 운영 중단·근거 철회가 있어도 과거 기록 열람·정정·내보내기를 가능한 범위에서 유지한다. 폐기된 엔진 버전의 기록도 저장된 결과와 버전별 해석 경로로 읽을 수 있어야 한다. 과거 결과를 새 엔진으로 재해석하면 별도 파생 버전으로 저장한다.

오프라인에서 신규 자동 처방을 제공할 수 있는지는 검증된 릴리스·규칙 캐시와 유효기간·철회 확인 정책에 따른다. 유효 여부를 확인할 수 없으면 신규 자동 조정을 멈추고 사용자 기록·선택을 유지한다. 캐시 유효기간과 재접속 시 보류된 이벤트 처리 규칙은 배포 전에 지정한다.

## 8. 인수 조건과 구현 연결

RUN-A01: 1RM·단위·카탈로그 변경 후 과거 목표가 동일하게 복구된다. RUN-A02: 실제 중량 수정·미수행·미기록이 차트에서 구별된다. RUN-A03: 모든 노출 행동은 해당 상태에서 유효하다. RUN-A04: 시작 재시도가 버전 변경 후에도 원 결과를 돌려준다. RUN-A05: 동일 owner 내 충돌과 타인 접근을 분리해 검증한다. RUN-A06: 기록 일부가 없을 때 계산 불가 범위를 표시한다.

기존 v2는 출처 연결·세트 이벤트·부분 완료의 출발점으로 재사용할 수 있다. ProgrammeInstance, 정정, 단측·중량 의미, 일부 복구 규칙, 목록·동기화·운영 저장소는 확장 또는 교체가 필요하다. v2 전체를 이 명세에 적합하다고 선언하지 않는다. 기존 사용 데이터는 검증된 마이그레이션 없이 v3로 재해석하지 않는다.

다음 문서: [개인화 명세](03_PERSONALIZATION.md)