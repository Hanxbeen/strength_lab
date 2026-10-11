# 자동 연구 판정과 반환

## 현재 구현 범위

수집 → 원문 추출/해시 저장 → 원문 동일성·앱 실행기 호환성 판정 → DB 트랜잭션 → API/앱 반환.
`python3 -m scripts.research_pipeline --directory data/research/current --persist`

`--persist`는 서버의 `RESEARCH_DATABASE_URL` 환경 변수와 `psql`이 필요하다. 비밀값을 앱에 넣지 않는다.
환경 변수가 없으면 실행이 실패하며 DB 저장 성공으로 보고하지 않는다. GitHub 워크플로는 동일 명령을 호출한다.
원문 XML은 로컬 캐시이며 git에 넣지 않는다. 논문 승인·과학적 타당성을 자동 검증했다고 주장하지 않는다.

## 기존 구현의 문제와 수정

기존 리뷰 큐는 모든 논문을 무조건 awaiting_human_review로 만들었다.
현재 판정은 source hash/PMID 일치, 측정 연구 여부, 보조 운동·가변 세트·클러스터 지원 여부를 검사한다.
결과는 auto_blocked 또는 source_fetch_failed로 저장하며 최신 자동 판정 배치의 awaiting_review는 0이다.
기존의 사람 서명 기반 공개 경로는 보존한다. 자동 판정이 서명이나 공개 승인을 위조하지 않는다.

## 명확한 미완료 범위

현재 자동 판정기는 출처 확인과 실행기 호환성 검사다. 완전한 주차/군/세션 처방 추출기나 자동 공개기는 아직 아니다.
임의 논문을 실행 가능한 루틴으로 자동 생성하는 기능은 미완료다. 미지원 필드를 지우고 단순 루틴으로 바꾸지 않는다.
수집 목표 20편은 보장 수량이 아니다. 거짓 승인이나 DEMO로 개수를 채우지 않는다.

## 응답 계약

- items: 원문 근거가 연결된 PUBLISHED_PROTOCOL만 실행 가능.
- studies: NOT_RUNNABLE 또는 SOURCE_ERROR, 항상 runnable=false. 논문 제목·원문 링크·사유만 반환.
- metadata.automatically_checked: 자동 판정한 수. metadata.awaiting_review: 사람 검토 대기 수.
- public.research_assessments: 배치별 불변 판정. 최신 배치만 research_catalog RPC에 표시.
- private 원문 추출 패킷은 anon/authenticated에 노출하지 않는다. 공개 판정 테이블도 SELECT만 허용한다.

## 배포 경계

DB migration과 이번 배치 import는 연결 도구로 실제 실행한다.
GitHub 워크플로 수정은 커밋/푸시와 서버 비밀 설정이 모두 완료되어야 예약 운영된다.
워크플로 파일 작성과 예약 배포 완료를 구분한다.

## 이번 실행 증거

2026-10-11T07:17:40Z 배치 `batch-a91456329fa237e0736c681b`: 요청20, 선택3, 자동 판정3, 사람 검토 대기0, 실행 가능0.
DB 저장과 재적재 후 public.research_assessments=3으로 중복이 없음을 확인했다.
Swift CatalogStore와 Python repository가 동일한 items0/studies3/awaiting0을 읽었다.
실행 Mac의 RESEARCH_DATABASE_URL 미설정: 이번 DB 적재는 생성된 트랜잭션을 연결 도구로 실행했다.
자동 예약 DB 쓰기는 아직 배포되지 않았다.
