# 무게꾼 — 레퍼런스 기반 iOS 시각 시스템 v2 (검토용)

> **중요: 색상·크기·레이아웃 토큰은 아직 확정하지 않았다.** 이번 문서는 45개 인터랙티브 HTML 화면에 실제 적용한 **시각 개선안과 SwiftUI 이식 규칙의 후보**다. 실제 iOS 앱 구현 및 RealityKit은 이 시안에 대한 사용자 승인 이후 진행한다.

## 1. 실존하는 레퍼런스에서 가져온 원칙

### Dropset — *Workouts* (사용자가 첨부한 첫 번째 레퍼런스)

- 운동 지표가 카드를 장식하는 요소가 아니라 **화면의 정보 위계**를 결정한다.
- 같은 행의 카드 크기·숫자 위치·안쪽 여백이 정렬된다.
- 검정 계열이 우선이고 조형적 장식은 절제한다.
- 참고: https://www.producthunt.com/products/dropset

### Regimen — *Workout in progress*

- 운동 중 상태/볼륨/세트 진행은 짧고 밀도 있게 요약한다.
- 기록은 운동 종목과 세트 단위로 그룹화한다.
- 참조: https://dribbble.com/shots/24000982-Regimen-Fitness-and-Health-Tracker-Mobile-App

### Trainier / HALO LAB — *Daily activity*

- 일정과 세션 활동을 시각적으로 구분한다.
- 카드 숫자와 보조 텍스트의 시선 순서를 분명하게 한다.
- 참고: https://dribbble.com/shots/27221460-UX-UI-for-a-Fitness-App-Trainier

**저작권:** 레퍼런스는 시각 설계의 원칙만 참고했다. 레퍼런스의 UI 이미지, 일러스트, 에셋, 원본 레이어를 복사하여 포함하지 않았다. 무게꾼의 얼굴 이미지는 자체 릴라 이미지이고, 기존 기능 흐름을 유지한다.

## 2. Apple 공식 iOS 패턴이 기준

- Human Interface Guidelines — Typography: https://developer.apple.com/kr/design/human-interface-guidelines/typography
- Human Interface Guidelines — Layout: https://developer.apple.com/kr/design/human-interface-guidelines/layout
- Human Interface Guidelines — Tab bars: https://developer.apple.com/kr/design/human-interface-guidelines/tab-bars
- Human Interface Guidelines — Toolbars: https://developer.apple.com/design/human-interface-guidelines/toolbars
- SwiftUI ViewThatFits: https://developer.apple.com/documentation/swiftui/viewthatfits

표준 컴포넌트 중심 구성:

- 최상위 4탭: 네이티브 **TabView** (홈/루틴/기록/성장)
- 각 탭 안의 상세 흐름: **NavigationStack** + 네이티브 **Toolbar**
- 운동 세션: `fullScreenCover`로 전환 후 `safeAreaInset(edge: .bottom)`에 세트 완료 CTA 배치
- 일반 정보: `ScrollView` + `LazyVStack` (정렬/레이아웃)
- 지표 묶음: `Grid` + `GridRow`; 대형 글씨에서는 한 열로 바꾸는 적응형 규칙
- 입력: 네이티브 `TextField`, `Picker`, `Toggle` 우선. 불필요한 커스텀 폼 금지
- 릴라: 캐릭터 뷰만 커스텀. RealityKit의 `RealityView`는 디자인 승인 이후 장착

**HTML 목업의 둥근 내비게이션은 외형을 모사한 것뿐이다.** 실제 iOS에서는 시스템 TabView가 OS 버전에 맞는 동작·효과·접근성을 제공하도록 한다.

## 3. 타이포그래피 — 잠정 비교 기준

시스템 폰트(SF Pro + iOS 한국어 폰트 폴백)를 사용하며 브랜드 전용 폰트는 추가하지 않는다.

| 역할 | 현재 HTML 검토안 | SwiftUI 이식 방향 | 메모 |
|---|---:|---|---|
| 홈 큰 제목 | 32pt | `.largeTitle` 기반 | 한 화면당 큰 제목 하나 |
| 상세 큰 제목 | 31~35pt | `.largeTitle` / `.title` | 필요 시 두 줄 |
| 섹션 제목 | 19pt | `.title3` / `.headline` | 섹션 사이 간격 통일 |
| 일반 설명 | 15pt | `.body` (기본 17pt) | HTML 시안보다 앱에서는 시스템 본문 선호 |
| 카드 타이틀 | 17pt | `.headline` | 일정한 줄 높이 |
| 카드 설명 | 14pt | `.subheadline` (통상 15pt) | 한두 줄 |
| 보조·범례 | 12~13pt | `.footnote` / `.caption` | 10px 장문 지양 |
| KPI 숫자 | 32~37pt | `@ScaledMetric` + `.monospacedDigit()` | 숫자 기준선 통일 |
| 탭 레이블 | 11pt | 시스템 `TabView` | 실제 iOS가 관리 |

Apple Dynamic Type을 지원해야 하므로 **본문을 임의의 고정된 pt로만 배치하는 것은 금지**한다. 특히 `Text`의 기본 의미 스타일을 우선 사용한다. 다크 모드와 `Bold Text` 설정도 각각 확인한다.

## 4. 그리드 정렬 및 크기 — 잠정 비교 기준

- 홈 카드 그리드: 화면 가로 패딩 **22pt**, 카드 사이 **12pt**.
- 좌우 카드: 그리드 열은 1:1, 시작 Y는 정확히 일치, 높이는 같은 행의 최대 높이에 맞춤.
- 통계 카드: 일반 텍스트 크기에서 최소 높이 **153pt**.
- 내부 3단 기준선: **레이블 → KPI → 보조 정보**. 내부 패딩 **18~19pt**.
- 두 자리 이상 숫자와 단위는 **첫 텍스트 베이스라인**을 맞추고 `monospacedDigit()`을 사용한다.
- 대형 글씨: 같은 정보를 보존하고 필요하면 2열을 **세로 1열**로 전환. 글씨를 억지로 줄여 공간에 끼워넣지 않는다.
- 리스트 행은 메트릭 카드와 다르게 좌측 아이콘 + 제목 + 부제 + 네비게이션 화살표를 사용한다.
- 연구 설명은 별도의 `EvidenceNote`로 두고 운동 지표처럼 꾸미지 않는다.

### SwiftUI 카드 구현 제안 (참고용, 아직 앱 코드에 적용하지 않음)

```swift
struct MetricCard: View {
    let title: String
    let value: String
    let unit: String
    let caption: String

    @ScaledMetric(relativeTo: .largeTitle) private var metricSize: CGFloat = 34

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            Text(title)
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .frame(maxWidth: .infinity, alignment: .leading)

            Spacer(minLength: 12)

            HStack(alignment: .firstTextBaseline, spacing: 5) {
                Text(value)
                    .font(.system(size: metricSize, weight: .bold))
                    .monospacedDigit()
                Text(unit)
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }

            Spacer(minLength: 12)

            Text(caption)
                .font(.footnote)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .leading)
        .padding(18)
        .frame(minHeight: 153)
        .background(Color(uiColor: .secondarySystemGroupedBackground),
                    in: RoundedRectangle(cornerRadius: 20))
    }
}

struct MetricsRow: View {
    @Environment(\.dynamicTypeSize) private var typeSize

    var body: some View {
        Group {
            if typeSize.isAccessibilitySize {
                VStack(spacing: 12) {
                    sampleVolume
                    sampleSessions
                }
            } else {
                Grid(horizontalSpacing: 12, verticalSpacing: 12) {
                    GridRow {
                        sampleVolume
                        sampleSessions
                    }
                }
            }
        }
    }

    private var sampleVolume: some View {
        MetricCard(title: "누적 볼륨", value: "3,200", unit: "kg", caption: "최근 7일")
    }

    private var sampleSessions: some View {
        MetricCard(title: "운동 횟수", value: "3", unit: "회", caption: "최근 7일")
    }
}
```

위 값은 스크린샷 비교용이며, 실기기에서 텍스트 잘림·최대 다이나믹 타입·좁은 화면을 검증한 뒤 확정한다. `regularMaterial` 등 시각 처리는 실제 카드 구조와 대비를 고려해 조정할 수 있다.

## 5. 이번 시각 개선에서 의도적으로 바꾼 것

- 홈 첫 제목을 추상적인 격려 문구 대신 **“오늘의 운동”**으로 변경.
- 메인 히어로의 주인공을 “스쿼트 5 × 5”와 **운동 시작**으로 변경.
- 기존 공통 `.card + .card {margin-top: 10px}`가 그리드 두 번째 카드를 **10px 아래로 밀던 레이아웃 버그 제거**.
- 홈의 중복 “오늘의 루틴” 카드를 제거하고 “최근 운동”과 “근력 변화”를 구분.
- 카드 설명과 본문 폰트 확대, 가독성 개선, 불필요한 영문 라벨·뱃지 축소.
- 운동 세션 중에는 하단 4탭 대신 **고정된 세트 완료 CTA** 표시.
- Light / Dark 테마 외에 **A / A+ 타이포그래피 미리보기** 추가. 이는 Dynamic Type 테스트를 대신하지 않는다.
- 색상은 차콜/화이트 및 무채색 계열, 예외적으로 상태를 의미하는 Ant Design Green/Gold/Red/Blue만 사용.

## 6. 검수 기준

다음 조건이 모두 충족되지 않으면 토큰을 최종 확정하지 않는다.

1. iPhone 15 Pro 일반 크기에서 첫 카드 행의 좌우 시작점·높이 오차 **0~0.5px**.
2. 세션 페이지의 세트 완료 액션이 엄지로 누를 수 있도록 하단에 고정되고 일반 4탭이 보이지 않아야 함.
3. 375px 너비의 좁은 화면에서도 가로 오버플로우가 없어야 함.
4. 큰 글씨에서는 카드가 늘어나거나 세로로 재배치되고 수치를 생략하지 않아야 함.
5. 한 화면의 주요 CTA가 명확하고, 중복된 카드/레이블이 최소화되어야 함.
6. 실제 SwiftUI에서 TabView, NavigationStack, Toolbar, 안전 영역, Dynamic Type, 다크 모드, VoiceOver 검수 후 승인해야 함.
7. 목업의 가상 데이터와 실제 연구 검증·실제 PR을 혼동하는 표현이 없어야 함.

## 7. 실제 브라우저 자동 검수 결과 (2026-10-09)

- 45개 화면 모두 라우팅 및 렌더링 성공, 브라우저 런타임 예외 **0건**.
- 운동 흐름: 루틴 상세 → 시작 확인 → 세션 개요 → 세트 기록(82.5kg 입력) → 휴식으로 전환 성공.
- `home`, `growth`, `records`의 2열 통계 카드: 1580px / 430px / 375px 뷰포트에서 **같은 행 좌우 Y 시작점 오차 0px, 높이 오차 0px**.
- 위 세 가지 화면과 `routine-detail`, `session-exercise`, `settings`: 세 뷰포트 모두 가로 넘침 **0px**.
- `session-exercise`: 일반 4개 탭이 사라지고 `세트 완료` 고정 CTA만 표시됨.
- A+ 확대 모드: 375px 뷰포트에서 2열 그리드가 1열로 전환되고 오버플로우 **0px**.
- 이 검사는 **HTML/CSS 브라우저 시안**의 레이아웃/동작 검증이다. Apple iOS 실제 Dynamic Type, VoiceOver, SwiftUI Liquid Glass, iPhone 실기기 테스트를 대신하지 않는다.

## 8. 다음 진행 순서

**이번 v2 화면을 보고 수정 → 화면별 피드백 취합 → 디자인 토큰 최종 확정 → SwiftUI 네이티브 컴포넌트 구현 → RealityKit 릴라 모델.**

사용자 소유 `docs/UX_WIREFRAME.html`은 변경하거나 Git에 추가하지 않는다.
