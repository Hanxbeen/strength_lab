# 무게무게 아키텍처 결정 (2026-10)
- One Brand, One Product, Two Native Experiences.
- iOS SwiftUI 먼저 출시, 사용자 반응 검증 후 Android Kotlin/Jetpack Compose.
- 브랜드 파운데이션과 API 계약 공유, UI 컴포넌트·내비게이션은 OS별 독립.
- Python 연구 파이프라인 → 독립 검증 → fail-closed release → FastAPI → 모바일.
- 원본 연구 루틴, 사용자 수정형, DEMO_ONLY는 서로 다른 데이터 유형.
- 승인된 게시물도 소스 진위/필드 의미/출시 권한을 검증하기 전에는 프로덕션 배포 불가.
- 운동 기록은 iOS 기기에 우선 저장; 서버 동기화는 후속 구현.
- iOS 26 Liquid Glass는 지원 SDK 및 OS 확인 후 네이티브 컴포넌트로 단계적 도입.
- 현재 개발 Mac Xcode 16.2: iOS 26 SDK 없음. 네이티브 glass 빌드 검증 불가.
