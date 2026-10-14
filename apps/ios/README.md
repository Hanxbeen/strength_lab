# 무게무게 iOS
현재 상태는 [CURRENT](../../docs/CURRENT.md)를 먼저 읽는다.
활성 화면은 ApprovedHomeView → GuidedWorkoutView다. 삭제된 HomeView는 사용하지 않는다.

## 빌드
Xcode와 XcodeGen이 필요하다.

```sh
cd apps/ios
xcodegen generate
xcodebuild -project MugeMuge.xcodeproj -scheme MugeMuge -sdk iphoneos -configuration Debug CODE_SIGNING_ALLOWED=NO build
```

실기기 설치에는 서명된 빌드가 필요하다. 서명 없는 빌드를 설치하지 않는다.
UI 테스트 대상은 MugeMugeUITests이며, 기기에 맞는 테스트 러너 프로파일도 필요하다.
DEBUG 테스트 실행은 MUGEMUGE_UI_TEST_FILE=ui-test-<고유값>.json으로 별도 기록을 사용한다.
일반 앱 데이터 파일과 테스트 데이터를 섞지 않는다.

## 기록과 연결
- 계정별 로컬 스냅샷에 세트, 시작 목표, 실제 휴식, 변경 및 사유 정정 이력을 저장한다.
- 기록은 원자적으로 저장하며 저장 실패 시 화면에 성공으로 반영하지 않는다.
- 0회 수행과 사유 미응답을 허용한다. 자기보고는 실패 원인 진단이 아니다.
- 정정은 직전 응답 ID를 참조하며 과거 응답을 유지한다.
- 백업은 JSON 수동 내보내기/복원이다. 복원은 현재 계정 기록을 교체하므로 확인이 필요하다.
- 기존 카탈로그 RPC와 번들 체험 루틴을 사용한다. 번들 체험은 연구 승인 루틴이 아니다.
- Python v3 실행 API와 iOS 기록은 아직 연결되지 않았다.
- API 주소 설정은 MugeMugeAPIURL이다. 서버 설정만으로 v3 연결이 완료되지는 않는다.
- 디자인 값은 design-tokens/tokens.json 및 생성된 BrandUI.swift를 따른다.

## 검증
저장소 루트에서 `bash scripts/test_ios_records.sh`를 실행한다.
원자적 기록, 계정 격리, 백업, 휴식, 사유 정정, 단위 변환 등의 Swift CLI 검증이다.
실기기 UI 검증은 별도이며 빌드 성공으로 대체하지 않는다.
최신 실행 결과와 막힌 조건은 CURRENT에 기록한다.
