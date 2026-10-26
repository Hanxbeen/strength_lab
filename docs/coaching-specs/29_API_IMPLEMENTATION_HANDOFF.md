# 운동 API 구현과 와이어프레임 인수
2026-10-27 갱신. 현재 범위는 SBD MVP의 입문·루틴 선택·수행·기록·종료다.
코드 구현, 실제 연구 DB 조회, 실제 사용자 원장 검증, 화면 검증은 별도 상태다.

## 확정 구조
- Swift: UI, 표시 단위, 타이머 표시, 입력, 미확인 요청 보존.
- Supabase Auth: 사용자 로그인과 서버의 토큰 확인.
- Python FastAPI: 루틴 적용 조건·목표 생성·수행 변경 검증·원장 연결·다음 회차·평가.
- Supabase Postgres: 버전 고정 연구 정의 및 소유자별 운동 기록.
- Vercel은 필수 아님. 기존 Python을 유지하고 현재 운영 호스팅은 미선정.
- App Store 배포와 API 호스팅은 별개. 운영 배포는 아이폰 검증 이후.

## 화면이 사용할 API
| 사용자 행동 | API | 응답·불변 조건 |
| --- | --- | --- |
| 숙련도별 선택 | GET /v3/routines?experience=entry 또는 foundation/trained/experienced | 연구 직접 추출/제품 종합 구분, 입문 별도 learning_paths |
| 시작 조건 확인 | POST /v3/programme-readiness | 입력 누락·적용 범위 표시, 저장 없음 |
| 내 중량으로 첫 운동 보기 | POST /v3/routines/preview | 생성 가능 여부와 세션 상태, 저장 없음 |
| 최대 중량 등록/조회 | POST/GET /v2/max-records | 측정/추정·원 단위·시각 보존 |
| 루틴 선택 | POST /v3/programme-instances | 원 정의/규칙/기준 기록 고정 |
| 내 루틴 복원 | GET /v3/programme-instances 및 /{id} | 소유자 격리, 페이지 커서, history/evaluations/evaluation_exercise_ids |
| 다음 운동 | GET /v3/programme-instances/{id}/next-session?at=... | 회차 순서·대기·열린 운동·종료 구분 |
| 운동 시작 | POST /v3/programme-instances/{id}/workouts | 반복 요청 ID와 순차 일정 검증 |
| 수행 변경 | POST /v2/workouts/{id}/events | 중량·반복·RPE·사유·휴식·건너뜀·완료/중단 |
| 운동 복원·결과 | GET /v2/workouts/{id}, /result | 미기록과0 구분, 원 목표와 실제 수행 유지 |
| 무활동 처리 | POST /v2/workouts/{id}/reconcile | 서버 시계로1시간 무활동 종료; 백그라운드 배치 아님 |
| 루틴 마무리·측정 추가 | POST /v3/programme-instances/{id}/evaluations | 선택적 사후 측정, 비교 조건, supersedes_id, 인과 효과 추정 없음 |
| 입문 설명 | GET /v3/entry/learning-paths | 학습이며 연구 훈련 수 제외 |
| 입문 실행·복원 | POST/GET /v3/entry/learning-sessions 및 GET /{id} | 원 정의와 사용자 관찰 보존 |
| 입문 관찰·휴식·종료 | POST /v3/entry/learning-sessions/{id}/events 및 /reconcile | 통증/불확실 중단, 원기록 후보 연결, 자동 자세 인증 없음 |
| 연결 준비 확인 | GET /v3/runtime-readiness | 실제 인증 후 공급·원장 읽기, 실패503; 쓰기·UI 검증 완료 주장 없음 |

정확한 필드와 요청 스키마는 backend.main:app의 /openapi.json을 따른다.
다른 목적의 기존 /v1 및 연구 미리보기 API는 위 소비 경로의 대체 데이터가 아니다.

## 이번 보완
- 입문 후보 선택 및 사후 비교 화면 연결은 직전5fb676e에 구현.
- /v3/runtime-readiness 추가: 전체 숙련도 공급과 원장5테이블 읽기 가능 여부. 데이터 변경 없음.
- Vercel 외에서도 MUGEMUGE_ENV=staging/production이면 Postgres 없이 SQLite로 대체하지 않음.
- 인증 제공자200 응답이 잘못된 형식이면503. 토큰401/403과 제공자 장애429/5xx 구분.
- 서버 직접 의존성 FastAPI/uvicorn을 실제 검증한 버전으로 고정.
- scripts.serve_api: 호스팅 독립 실행, Supabase 설정과 Postgres DSN 없으면 시작 거절.
- scripts.verify_runtime_connection: 실제 토큰으로 Auth/API/Postgres 읽기 검증. 테스트 대역 없음.
  이 스크립트 성공은 쓰기·타인 접근 차단·동시 요청 검증을 대신하지 않는다.

## 실행
비밀값은 저장소/채팅에 넣지 않고 해당 프로세스의 환경변수로 전달한다.
필수: SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, WORKOUT_POSTGRES_DSN.
DB TLS는 verify-full이며 필요한 경우 WORKOUT_DB_SSLROOTCERT를 설정한다.

```sh
.venv-coaching/bin/python -m scripts.serve_api
```

기본은127.0.0.1:8000으로 로컬에서만 접근 가능하다.
기기 연결 시 도달 가능한 호스트 주소 및 신뢰할 TLS 인증서/개인키가 필요하다.
serve_api는 --host, --port, --ssl-certfile, --ssl-keyfile을 지원한다.
현재 iOS 클라이언트는 HTTPS 주소만 허용하며 TLS 검증을 해제하지 않는다.

실계정 읽기 검증은 MUGEMUGE_API_URL과 MUGEMUGE_TEST_ACCESS_TOKEN을 환경변수로 전달한 후 실행한다.

```sh
.venv-coaching/bin/python -m scripts.verify_runtime_connection
```

토큰 없이 호출하면 실패하며 인증 대역으로 대체하지 않는다.
쓰기 인수에는 전용 테스트 계정2개와 서버 Postgres 연결이 필요하다.
개인 실제 운동 기록을 테스트 생성물로 오염시키지 않는다.

## 확인한 결과
- 실제 Supabase SQL: programme 정의10행(중지 포함), 입문 학습1행. 공개 선택 수와 DB행 수는 다른 개념.
- 실제 HTTPS 카탈로그→로컬 API: 초급3/중급3/숙련4, 입문 학습1.
- 공개10안의 미리보기/생성/시작/감량/반복 변경/종료/재조회 통과.
- 위 로컬 실행은 인증 대역+임시SQLite. 실계정 JWT/Postgres 쓰기 성공이 아님.
- Python287개57.604초 통과, 건너뜀0.
- Swift16개 및 무서명 빌드는 직전5fb676e에서 통과; 이번 변경은 서버 코드.

## 다음 단계와 완료 판단
와이어프레임은 위 API 계약을 기준으로 설계할 수 있다.
API 코드 구현을 근거로 실서비스 전체 완료라고 보고하지 않는다.
남은 실행 인수: 실제JWT2계정, Postgres 저장·재조회·소유자격리·중복/동시변경, 앱 재실행, 아이폰 상호작용.
현재 맥북 프로세스에 DSN/테스트 세션 미설정. 호스팅 및 기기 접속 주소도 미설정.
새 연구 수집·루틴 숫자 늘리기·AI/회복/과금 확장은 이 연결 검증을 대체하지 않는다.
