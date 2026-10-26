# 숙련도별 데이터 공급 — 2026-10-26

## 사용자에게 생기는 변화
- 입문: 동작 설명/외부 시연, 맨몸 연습, 선택적 첫 중량 관찰, 휴식/중단 기록을 DB 버전으로 제공한다.
- 초급: 기존 Petrizzo 두 일정 외에 SBD 주2회 근거 종합 구성을 추가한다.
- 중급: 기존 Helms 스쿼트·벤치 두 arm 외에 데드리프트 포함 SBD 주3회 구성을 추가한다.
- 숙련: 기존 METD 세 arm 및 PER 원종목 구성 유지.
- 학습1개와 훈련 선택10개를 분리한다. 10개 독립 논문 또는 개인별 효과 검증을 뜻하지 않는다.

## 근거와 제품 결정
ACSM 2026 Position Stand:
https://pmc.ncbi.nlm.nih.gov/articles/PMC12965823/
일반 건강 성인 저항훈련 근거 종합이다. Table6의 근력 관련 빈도/세트 정보는 참고 근거다.
아래 정확한 8주 SBD 일정, 5회 반복, 사용자 작업 중량 선택 조합은 연구 실험군이 아니라 제품 구성이다.
초급: 8주×주2회×SBD각2세트×5회 = 16회차,96세트.
중급: 8주×주3회×SBD각3세트×5회 = 24회차,216세트.
휴식/워밍업/실제 부하는 명시적 사용자 선택이며 자동 증량·정체 판정·성장 예측은 하지 않는다.
독립적인 SBD 수행과 알려진 작업 중량이 필요하다. 중급은 최소6개월 훈련 자기보고 조건이다.
이는 탐색/적용 조건이며 분류만으로 적합성·안전성을 보장하지 않는다.
2009 ACSM 지침을 최신 근거인 것처럼 사용하지 않는다.

입문 출처:
- https://www.nhs.uk/live-well/exercise/strength-exercises/
- https://www.nsca.com/education/articles/ptq/teaching-resistance-training-movement-patterns/
- NSCA squat/deadlift technique pages and strength-and-conditioning manual linked in versioned JSON.
외부 링크를 제공하며 시연 저작물을 복제하지 않는다. 기기별 실제 재생은 아이폰 검사 항목이다.
NSCA 전문가 교육 흐름을 독립 학습으로 구성한 부분과 벽 밀기 단일5회 연습은 제품 결정이다.
입문 연습을 힘 증가 실험 루틴으로 주장하지 않는다.

## 데이터 계약
- coaching_programme_catalog_v6: 기존 v3/v4/v5 응답을 변경하지 않는 추가 RPC.
- coaching_learning_catalog_v1: 학습 정의 전용.
- GET /v3/routines: 훈련 선택 + 별도 learning_paths 및 data_ready 상태.
- GET /v3/entry/learning-paths: DB 해시가 고정된 입문 정의.
- POST /v3/entry/learning-sessions: 소유자별 원본 스냅샷.
- learning-sessions/{id}/events, reconcile: 동작/중량 관찰, 휴식, 완료/중단.
- 입문 원기록을 사용할 때 setup.entry_trial_references[exercise_id]={workout_id,event_id}를 요구한다.
  starting_load_origins의 self_reported_intro_trial과 일치해야 하며, 같은 소유자/완료 기록/실제 후보 중량/시각을 검사한다.
  나중에 임의 중량으로 바꾼 값은 같은 원기록의 측정값으로 주장할 수 없다.
- 1RM 자동 생성, 자세 인증, 초급 자동 해금 없음. 알려진 작업 중량 자기보고는 별도 출처다.
- 현재 통증/운동 제한 미응답은 시작 준비로 취급하지 않는다.
- 통증/자세 불확실은 중단, 입문 후보 무효화. 미기록은 실패로 바꾸지 않는다.
- 1시간 무활동은 stopped. 열린 휴식은 실제 회복시간으로 확정하지 않는다.
- source_extracted와 reviewed_product_synthesis를 DB CHECK 및 응답에서 구분한다.

## 완료 판정과 남은 인수
데이터 준비, 로컬 API 실행, 실계정 서버 저장, iPhone 실행, 운영 배포는 서로 다른 상태다.
supply_audit.all_levels_data_ready는 최소 MVP 데이터 범위만 뜻한다.
all_levels_complete/client_execution_verified는 아이폰/실계정 검증 전 false다.
자기보고 자세·작업 중량, 제한된 연구군 다양성, 외부 시연 접근성은 남은 한계다.
정확한 논문 성장 기울기와 사용자 결과를 같은 단위로 비교할 수 있다는 주장은 하지 않는다.
사용자 최신 순서: 데이터 및 흐름 준비 → 아이폰 설치/테스트 → 운영 배포.
운영 배포, main 병합, 실제 계정 실행을 이 데이터 변경만으로 완료 처리하지 않는다.
