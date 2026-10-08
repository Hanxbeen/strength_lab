# 무게무게 클라우드 아키텍처 결정안 (미구현)

## 권장 선택: Supabase (managed PostgreSQL + Auth + RLS)
- iOS SwiftUI와 추후 Android Jetpack Compose가 **동일한 사용자 계정 및 운동 데이터**를 사용해야 하므로 CloudKit 단독 사용은 피한다.
- MVP에서는 오프라인 로컬 기록을 source of truth로 유지하고, 인증/동기화는 검증 후 단계적으로 도입한다.
- Supabase Auth: Apple 로그인 우선, Android 추가 시 Google 로그인. 익명 사용 후 계정 연동을 지원하도록 설계.
- Supabase Postgres: users / workout_sessions / workout_sets / measured_maxes / protocol_versions / sync_operations. 각 테이블 user_id와 RLS를 필수로 사용.
- 동기화: client-generated UUID, idempotency key, server revision, tombstones, last-write conflict UX, incremental sync cursor. 네트워크 실패 시 local queue 보존. 로그인·로그아웃 시 로컬 데이터 소유권 정책을 명시해야 한다.
- 연구 검증: 기존 GitHub Actions Python 파이프라인에서 검증된 protocol version만 FastAPI 관리 경로를 통해 게시. 앱에 service_role 키를 절대 포함하지 않는다.
- 서버 기능이 복잡해질 때 Python FastAPI를 별도 컨테이너 서비스로 배포한다. Supabase Edge Functions는 간단한 이벤트/웹훅에만 사용한다.
- 데이터 백업: 수동 JSON export/import는 유지. Cloud sync != backup. 서버 PITR/스냅샷, 데이터 삭제 정책, 복구 리허설이 필요하다.
- 비용: 무료 티어를 초기 검증에 사용할 수 있으나 제한, 휴면 정책, 트래픽 및 백업 요금은 도입 시점에 확인한다.

## 현재 상태
- Supabase 프로젝트/계정/DB/인증/동기화는 아직 생성하거나 연결하지 않았다.
- 실제로 동작하는 것은 기기 로컬 JSON 원자적 저장과 수동 JSON 백업/복원뿐이다.
- Android는 향후 별도 네이티브 UI 시스템으로 개발한다.
