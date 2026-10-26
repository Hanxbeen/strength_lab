# iOS 실행 API 연결 — 2026-10-26

## 구현 범위
홈/루틴/기록 진입점을 서버 루틴 경로로 연결했다. 기존 기기 원장은 삭제/변환하지 않으며 홈의 '이전 기기 운동 기록'에서 열 수 있다.
BrandUI.swift의 MugeStyle 색상·타입·간격·버튼을 사용한다. 별도 토큰 시스템을 추가하지 않는다.

- GET /v3/routines: 입문 학습, 초급/중급/숙련 필터, 연구 한계, 전체 회차 수.
- /v3/programme-instances: 본인 목록과 페이지 추가 조회, 고정된 구성/진행 기록.
- 입력 계약 기반 조건 입력. 건강/경험/동의 체크를 자동 true로 채우지 않는다.
- /v2/max-records: 직접 측정한 최대 중량을 서버에 등록하고 선택한다. 기기 과거 추정 기록을 측정값으로 자동 업로드하지 않는다.
- /v3/routines/preview: 서버의 준비 조건 및 첫 회차 검사 성공 후 선택한다.
- /next-session 및 /workouts: 서버 일정 순서를 따르며 작업 중량은 직접 확인한다.
- /v2/workouts 이벤트: 세트 실제 횟수/RPE, 중량 변경과 사유, 건너뛰기, 휴식 목표 변경/종료, 사용자 중단.
- 30초 주기/포그라운드 복귀 reconcile. 서버의 1시간 무활동 중단 규칙을 소비한다.
- 결과: 세트별 목표/실제 중량 점 차트, 실제 횟수, 목표/실제 휴식. 미기록을0으로 채우지 않는다.
- programme evaluations: 사후 최대 중량 측정을 강제하지 않고 수행 기록으로 완료/중단 마무리한다.
- 입문: DB 정의의 설명/외부 시연, 맨몸 관찰, 선택적 첫 중량, 휴식/중단/완료, 기존 학습 기록 조회.
- kg/lb 입력은 원 단위를 표시하고 API 계약이 요구하는 kg으로 환산한다. 운동 결과 차트도 선택 단위로 표시한다.

## 권한·실패 처리
CloudAuth.accessToken()을 사용한다. 로그인 우회나 테스트용 가짜 토큰은 앱에 추가하지 않았다.
요청 전/후 계정 동일성을 검사하고 뷰는 계정 변경 시 재생성한다.
RoutineOutbox는 Application Support에 계정별 미확인 변경 요청을 atomic 저장한다.
토큰을 저장하지 않으며 이벤트 ID/시각/expected_revision을 그대로 유지한다.
재시작 후 미확인 요청은 사용자가 명시적으로 같은 내용으로 재확인한다. 자동 재전송/리비전 덮어쓰기 없음.
409 및 확정4xx는 새 입력 검토로 처리하며 다른 기기 기록을 자동 덮어쓰지 않는다.
응답을 받기 전에 성공 표시하거나 로컬 상태만 변경하지 않는다.

## 실행한 검증
- xcodegen generate 후 iphoneos Debug CODE_SIGNING_ALLOWED=NO 빌드 성공.
- scripts/test_ios_records.sh 전체16개 Swift 검증 프로그램 통과.
- 신규 RoutineAPITests: Bearer 인증, null/0/false 구분, 쿼리 전달, POST/리비전,409/401, 자동 재전송 없음, 계정별 outbox/동일 요청/충돌/확인 후 삭제.
- 이번 변경은 Swift 클라이언트다. Python277개는 직전 데이터 커밋의 검증 결과이며 새 실계정 통합 검증으로 표현하지 않는다.
- UI 조작/실계정/JWT/Postgres/iPhone 실제 실행은 아직 미검증이다.

## 설치 차단 — 실제 확인 결과
1. devicectl: Hanbeen / Yoobin의 iPhone15 Pro 모두 unavailable. 연결/잠금 해제/신뢰 상태 확인 필요.
2. 서명 빌드: provisioning profile 없음. -allowProvisioningUpdates 재시도도 No Accounts.
   Xcode Settings > Accounts에서 Apple 개발 계정 설정 및 Apple Sign In 가능한 팀/프로파일 필요.
3. MUGEMUGE_API_URL 미설정. HTTPS 테스트 서버의 v2/v3 API 및 실계정 원장이 필요하다.
   API URL은 Info.plist의 MugeMugeAPIURL로 전달한다. 빈 주소에서 가짜 루틴이나 번들 루틴으로 대체하지 않는다.
   예: xcodebuild ... MUGEMUGE_API_URL=<검증한 HTTPS 테스트 API 주소>
   DSN/토큰을 Info.plist에 넣지 않는다.

Debug도 실제 Apple Sign In entitlement를 사용하도록 수정했다. 인증 권한을 없애 서명만 성공시키지 않는다.
운영 배포와 main 병합은 하지 않았다. 테스트용 서버 설정과 운영 배포를 구분한다.

## 다음 인수
- 위 설치 차단 해소 후 서명/아이폰 설치.
- 실계정으로 모든 숙련도 목록·조건 거절·정상 시작·감량·반복 변경·통증·휴식 축소/확대·중단·재시작·결과·다음 회차 검사.
- 입력 폼/외부 시연 재생/화면 키보드·접근성은 실제 기기에서 검토해야 한다.
- 입문 후보 중량은 현재 UI에서 자동 초급 전환하지 않는다. 서버 원기록 참조 API는 구현돼 있으나 해당 후보를 고르는 전용 UI는 후속 인수 항목이다.
- 사후 측정 비교 조건을 입력하는 평가 UI는 후속이다. 현재 루틴 마무리는 '미측정'을 명시한 사실 기록만 저장한다.
- 실기기 인수가 끝나기 전 모든 사용자 과정/서비스 완료라고 보고하지 않는다.
