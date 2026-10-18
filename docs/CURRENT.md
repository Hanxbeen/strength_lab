# 현재 상태 — 2026-10-18
이 문서가 세션 재개 기준이다. 상태는 명시적 선택 API 구현(2026-10-18) 기준이다. 운영 배포 완료와 구분하며 코드/DB를 확인한다.
브랜치: codex/ux-foundations-v2. GitHub: Hanxbeen/strength_lab.
과거 진행 일지와 폐기된 다음 작업은 현재 문서에서 제거했다. 복구: git show c8ff613:docs/CURRENT.md.
상태 변경 시 과거 일지를 덧붙이지 말고 해당 현재 항목을 갱신한다.

## 고정 결정
- 목적: SBD 중량 향상에 필요한 근거·훈련·수행 기록·다음 선택을 연결한다.
- OHP/보조 운동 일괄 제외는 폐기했다. 원 연구와 역할을 확인해 유지한다. 제외/대체는 제품 변경으로 명시한다.
- 로그인 아키텍처 유지. UI 재설계보다 실제 루틴 공급/실행을 우선한다.
- 입문(자세/첫 중량 모름)과 초급(독립 수행/알려진 작업 중량)을 구분한다. 릴라 레벨이나 1RM 크기로 숙련도를 확정하지 않는다.
- 원 연구 / 제품 규칙 / 사용자 선택 / 실제 수행을 분리한다. 수행률을 성장 효과로 바꾸지 않는다.
- 새 연구 자동 공개를 하지 않는다. 초기 근거 체계를 구축하고 이후 발견/변경 검토를 한다.
- 명시적 중단·한 시간 무활동 중단은 닫힌 stopped. 중단 후 재개 없음. 미기록을 실패/0회로 채우지 않는다.
- 디자인은 BrandUI.swift 토큰, 릴라 털 차콜, 단위 kg/lb. 현재 작업은 UI 확장이 아니다.

## 실제 공급과 공백
| 구성 | 내부 선택안 | 회차 | 조건/한계 |
| --- | ---: | --- | --- |
| Petrizzo 네 종목 | 2 | 24 / 36 | 알려진 시작 중량과 네 동작 경험. OHP 포함. 156 / 228 본세트 |
| 기존 OHP 생략 시제품 | 1 | 24 | 과거 기록 호환용 정의 보존. 현재 기본 방향을 뜻하지 않음 |
| PER 조정안 | 1 | 30 | 원 종목 변경이 있는 제품 조정 |
| Helms | 2 | 각 23 훈련 회차 | 스쿼트·벤치. 검사 회차 제외. 1RM 비율/RPE 구분 |
| METD | 3 | 각 18 | 경험/RPE 요구. 적은 세트 수가 낮은 난이도를 의미하지 않음 |

DB 활성 내부 정의6개 / 선택안9개 / 중지된 과거 버전1개.
같은 연구의 arm/일정 변형이 포함되며 독립된9편이나 공개 루틴9개가 아니다.
정확한 해시 4개에 대한 명시적 선택 7안 구현: 초급2 / 훈련경험2 / 숙련3. 개인 추천이 아니다.
입문 학습·첫 부하 안내와 자동 적합성 추천은 미완료다. 운영 배포/실계정 검증은 미완료다.
공개 선택 조건·한계는 [22_EXPLICIT_SELECTION_RELEASE.md](coaching-specs/22_EXPLICIT_SELECTION_RELEASE.md)가 최신이다.
근거/적용 결정: [21_FOUR_LIFT_DELIVERY.md](coaching-specs/21_FOUR_LIFT_DELIVERY.md).
과거 후보/교육 근거: data/research/coaching/reviews/ (실행 여부를 개별 확인).

## API와 저장 경로
- backend/coaching_api.py: GET /v3/routines → 활성 7선택안/전체 구성/입력 계약/실제 coverage.
- POST /v3/routines/preview → 저장 없는 첫 세션 계산/부족 입력. 생성·시작에서도 조건 재검증.
- 기존 GET /v3/research-programmes는 연구·내부 조정안 호환용. 사용자 선택 화면은 /v3/routines 사용.
- backend/programme_readiness.py: 입력 충족/접근 상태/다음 세션. 적합성 평가 완료라는 의미가 아니다.
- research_engine/petrizzo.py: 주2/3회 전체 정의, 시작 중량 출처, 사용자 직접 선택.
- backend/programme_evaluation.py: 기간 종료/비교 조건. OHP는 별도 표시하고 SBD 합계에서 제외.
- 기존 v2 workout API: 변경/휴식/통증/미완료/중단/결과. 원 목표와 실제 수행, revision/재시도 보존.
- 프로그램 목록/상세/next-session으로 새 클라이언트에서 복구 가능. 앱 자동 호출/배포 종단 검증과 구분한다.
- Supabase project: gttvyfeyrnuspnnphuzk.
- 카탈로그 RPC v4: schema_version=3 구조 + catalog_revision=4. 신규 어댑터 포함.
- RPC v3는 구버전 서버 호환용 집합 유지. v3 총5행 / v4 총7행, 각각 중지1 포함. Python은 중지행 제외.
- execution_private 5개 원장 테이블과 소유자 RLS 생성/검증 완료.
- PostgresWorkoutStore는 기존 실행 로직 재사용, 소유자별 트랜잭션 잠금 및 authenticated 역할 적용.
- WORKOUT_POSTGRES_DSN은 서버 전용 설정. TLS verify-full, libpq17+의 system CA 또는 WORKOUT_DB_SSLROOTCERT.
- Vercel에서 DSN 누락 시503. SQLite fallback으로 운영 성공을 가장하지 않는다.
- backend/programme_access.py는 정확한 버전 해시만 명시적 선택 허용. 새 해시 자동 공개 금지.
- COACHING_PREVIEW_OWNER_IDS는 미공개 내부 조정안 허용 목록이며 일반 7선택안에는 필요하지 않다. 사용자 동의나 JWT user_metadata로 권한을 부여하지 않는다.

## 확인된 검증
- 2026-10-18 최종 전체 Python255개 통과, 건너뜀 없음. 입문 연습/공급 공백 반례 포함. git diff --check 통과.
- main 병합/운영 배포는 이번 작업에서 수행하지 않았다. codex/ux-foundations-v2 구현과 운영 응답을 구분한다.
- 신규 일정 전체60회차 로컬 API 수행/읽기/종료, 재시도, 정보 부족, 변경·통증·미완료 반례.
- 실제 Supabase HTTPS 카탈로그: 파일/DB/버전 해시 일치, 구버전 응답 호환성 확인.
- 실제 Supabase HTTPS 데이터를 사용한 일반 사용자 대역 로컬 API: 7선택안 전부 미리보기→생성→시작→35kg/1회 변경→중단→재조회→다음 회차 응답 확인.
- 재현: python -m scripts.verify_live_routine_selection. 운영 사용자 데이터 쓰기 없음.
- 위 로컬 실행은 인증 대체 + 임시 SQLite. 배포 인증/Postgres 운동 저장 검증이 아니다.
- DB RLS: 본인/타인 접근과 소유자 변경 차단 검증. 테스트 쓰기 롤백.
- 보안 advisor: 기존 private 연구 테이블의 정책 없는 RLS INFO2건. 신규 경고 없음.
- 최신 마이그레이션: 20261017123755_petrizzo_four_lift_catalog.sql, 20261018005609_version_four_lift_catalog_rpc.sql. 실제 적용 완료. 재적용 전에 원격 이력 확인.

## 다음 작업 — 숙련도별 공급 공백 우선
최신 사용자 지시: 7선택안 API 실행 통과가 아니라 숙련도별 실제 공급을 마무리한다.
최신 검토/구현: [23_ENTRY_PRACTICE_AND_SUPPLY_GAPS.md](coaching-specs/23_ENTRY_PRACTICE_AND_SUPPLY_GAPS.md).
- 입문 지도자 동반 학습3종 시작·기록·휴식·중단 API 추가. 독립 입문/첫 바벨 부하 미완료. 교육 정의는 서버 코드이며 DB 훈련 루틴 수에 포함하지 않는다.
- /v3/routines.supply_audit에서 선택안/연구군/SBD포함/공백을 분리. 전체 완료 false.
- Colquhoun 저널·학위논문 진행표 일부 재확인. 전체 처방표 시각 검증 필요. 원 PDF 다운로드 HTTP403으로 중지; 원 PDF 또는 Tables1-3 필요.
- 최종 전체255개 통과, 건너뜀 없음. 새 교육 흐름은 로컬 검증이며 운영 사용자 쓰기 없음.
- 다음 우선순위: 독립 입문 경로 → 초급 실제 다양성 → 중급 SBD 원표 검증/데이터화 → 숙련 목적 범위. 아래 배포는 이 공급 작업을 대신하지 않는다.

## 이후 배포·실기기 인수
1. 기존 Vercel 프로젝트/배포 버전/서버 설정을 확인한다. 이전 인증 조회는 fetch failed 또는 HTML 응답으로 실패했으며 현재 연결 상태를 다시 확인해야 한다.
2. 기존 인증을 유지한 채 WORKOUT_POSTGRES_DSN 연결과 사용자 역할/RLS를 실제 서버에서 검증한다. 테스트 로그인 세션 필요. 비밀값은 기록하지 않는다.
3. 실제 계정으로 카탈로그→입력→생성→세트/감량/휴식/중단·완료→재접속→다음 회차를 실행한다. 타인 접근/만료 토큰도 확인한다.
4. 22번 명세의 7선택안/고정 해시만 배포한다. 입문·미검토 조정안까지 범위를 확대하지 않는다.
5. iOS 단일 API 경로를 연결해 실기기 검증한다. 입문 학습/첫 부하 공백은 별도 산출물로 남기고 완료라고 표시하지 않는다.
인수 세부: [20_RUNTIME_DELIVERY_PLAN.md](coaching-specs/20_RUNTIME_DELIVERY_PLAN.md).
해결되지 않은 접근 문제를 새 호스팅·인증 우회·비밀번호 초기화로 우회하지 않는다.

## 재현 환경
- 알려진 Mac 경로: /Users/hanbeen/codex-workspace/strength_lab (세션별 연결 확인).
- 알려진 Python: /tmp/mugemuge-coaching-env/bin/python (임시 경로이므로 존재 여부 확인).
- 의존성: backend/requirements.txt, requirements-test.txt. 원문 캐시가 필요한 검사는 verify_tests가 건너뜀을 실패로 처리한다.
- 전체 검사: python -m scripts.verify_tests.
- 실제 카탈로그: SUPABASE_URL / SUPABASE_PUBLISHABLE_KEY를 정상 설정하고 python -m scripts.verify_live_petrizzo_catalog.
- Swift 기록: bash scripts/test_ios_records.sh. iOS 빌드는 apps/ios/README.md 참고.
- 배포된 실제 앱 버전, 운영 DSN, 로그인 세션은 이 문서에 확보됐다고 가정하지 않는다.
- 권한/연결 실패는 관측 오류와 필요한 조치를 기록한다. 같은 실패 요청을 계속 반복하지 않는다.
- 2026-10-18 인수인계 정리: CLAUDE/AGENTS/README와 상세 문서의 폐기 지침을 대조·수정했다. 리뷰 JSON 관련 기존5개 검사와 diff 점검 통과. 문서 변경에서 전체239개 코드를 재검증했다고 주장하지 않는다.
