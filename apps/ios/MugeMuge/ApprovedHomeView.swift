import SwiftUI
import Charts

/// Korean presentation is separate from API identifiers and source-paper titles.
enum TrainingCopy {
    static func exercise(_ id: String) -> String {
        switch id.lowercased() {
        case "squat": return "스쿼트"
        case "bench", "bench_press", "bench-press": return "벤치프레스"
        case "deadlift": return "데드리프트"
        default: return "기타 운동"
        }
    }
    static func routine(_ item: TrainingProtocol) -> String {
        item.status == "DEMO_ONLY" ? "기록 연습" : item.title
    }
    static func session(_ session: TrainingSession) -> String {
        "전신 운동 · \(session.exercises.count)종목"
    }
}

struct ApprovedHomeView: View {
    @EnvironmentObject private var catalog: CatalogStore
    @AppStorage("onboardingCompleted.v2") private var onboardingCompleted = false
    @State private var showIntroduction = false
    var body: some View {
        TabView {
            NavigationStack { TrainingHome() }
                .tabItem { Label("홈", image: "lucide-house") }
            NavigationStack { RoutineLibrary() }
                .tabItem { Label("루틴", image: "lucide-dumbbell") }
            NavigationStack { TrainingHistory() }
                .tabItem { Label("기록", image: "lucide-chart-no-axes-column-increasing") }
        }
        .tint(MugeStyle.accent)
        .onAppear { showIntroduction = !onboardingCompleted }
        .fullScreenCover(isPresented: $showIntroduction) { TrainingIntroduction() }
        .task { await catalog.refresh() }
    }
}

private struct TrainingHome: View {
    @State private var confirmsUnavailableFinish = false
    @State private var finishError: String?
    @AppStorage("homeHelpDismissed.v2") private var helpDismissed = false
    @AppStorage("displayUnit") private var unit: MassUnit = .kg
    @EnvironmentObject private var workouts: WorkoutStore
    @EnvironmentObject private var catalog: CatalogStore
    private var activeRoute: (TrainingProtocol, TrainingSession)? {
        guard let active = workouts.active,
              let item = (catalog.protocols + catalog.demo).first(where: {
                  $0.id == active.protocolID && $0.version == active.protocolVersion
              }), let session = item.sessions.first(where: { $0.id == active.sessionID }) else { return nil }
        return (item, session)
    }
    private func latest(_ id: String) -> MeasuredMax? {
        workouts.measuredMaxes.filter { $0.exerciseID == id }.max { $0.measuredAt < $1.measuredAt }
    }
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: MugeStyle.Space.section) {
                Text("내 운동").font(MugeStyle.TypeStyle.hero)
                if let active = workouts.active {
                    MugeCard {
                        Text("진행 중인 운동").font(MugeStyle.TypeStyle.section)
                        Text("\(active.setIDs.count)세트 기록").foregroundStyle(MugeStyle.muted)
                        if let route = activeRoute {
                            NavigationLink { GuidedWorkoutView(item: route.0, session: route.1) } label: {
                                Text("운동 이어하기")
                            }.buttonStyle(MugePrimaryButtonStyle())
                        } else {
                            Text("운동 구성을 불러오지 못했어요. 기록은 보존되어 있어요.")
                                .font(MugeStyle.TypeStyle.detail).foregroundStyle(MugeStyle.muted)
                            Button("다시 불러오기") { Task { await catalog.refresh() } }
                            Button("기록을 남기고 종료") { confirmsUnavailableFinish = true }
                            if let finishError { Text(finishError).foregroundStyle(.red) }
                        }
                    }
                }
                MugeCard {
                    HStack {
                        Text(workouts.measuredMaxes.isEmpty ? "최대 중량을 입력해 주세요" : "내 최대 중량")
                            .font(MugeStyle.TypeStyle.section)
                        Spacer()
                    }
                    if workouts.measuredMaxes.isEmpty {
                        Text("아는 종목만 입력해도 괜찮아요.")
                            .font(MugeStyle.TypeStyle.detail).foregroundStyle(MugeStyle.muted)
                        NavigationLink { StrengthSetupView() } label: {
                            MugeNavigationLabel(title: "입력하기", icon: "dumbbell")
                        }
                    } else {
                        ForEach(["squat", "bench", "deadlift"], id: \.self) { id in
                            VStack(alignment: .leading, spacing: MugeStyle.Space.xs) {
                                HStack {
                                    Text(TrainingCopy.exercise(id))
                                    Spacer()
                                    Text(latest(id).map { unit.label($0.weightKg) } ?? "미입력")
                                        .font(MugeStyle.TypeStyle.action).monospacedDigit()
                                }
                                if let current = latest(id) {
                                    Text(monthlyChange(id, latest: current))
                                        .font(MugeStyle.TypeStyle.note).foregroundStyle(MugeStyle.muted)
                                }
                            }.padding(.vertical, MugeStyle.Space.xs)
                        }
                        NavigationLink { StrengthSetupView() } label: {
                            MugeNavigationLabel(title: "최대 중량 수정", icon: "pencil")
                        }
                    }
                }
                if workouts.active == nil {
                    NavigationLink { RoutineLibrary() } label: { Text("루틴 보기") }
                        .buttonStyle(MugePrimaryButtonStyle())
                }
                if let recent = workouts.history.max(by: { $0.startedAt < $1.startedAt }) {
                    NavigationLink { WorkoutHistoryDetail(workout: recent) } label: {
                        MugeCard {
                            Text("최근 운동").font(MugeStyle.TypeStyle.card)
                            Text(recent.startedAt, format: .dateTime.month().day())
                                .foregroundStyle(MugeStyle.muted)
                            MugeNavigationLabel(title: "\(recent.setIDs.count)세트 · 기록 보기")
                        }
                    }.buttonStyle(.plain)
                }
                if let demo = catalog.demo.first {
                    NavigationLink { RoutineOverview(item: demo) } label: {
                        MugeCard {
                            MugeNavigationLabel(title: "운동이 처음이라면", icon: "dumbbell")
                            Text("기록 연습 · 논문 루틴 아님")
                                .font(MugeStyle.TypeStyle.detail).foregroundStyle(MugeStyle.muted)
                        }
                    }.buttonStyle(.plain)
                }
                if !helpDismissed {
                    MugeCard {
                        HStack {
                            Text("무게무게가 처음이신가요?").font(MugeStyle.TypeStyle.card)
                            Spacer()
                            Button { helpDismissed = true } label: { MugeIcon(name: "x") }
                                .frame(minWidth: MugeStyle.minimumTarget, minHeight: MugeStyle.minimumTarget)
                                .accessibilityLabel("도움말 닫기")
                        }
                        Text("최대 중량을 입력하고, 운동한 무게와 횟수를 기록해 보세요.")
                            .font(MugeStyle.TypeStyle.detail).foregroundStyle(MugeStyle.muted)
                        Button("확인했어요") { helpDismissed = true }
                    }
                }
            }.padding(MugeStyle.Space.page)
        }.background(MugeStyle.canvas)
        .navigationTitle("무게무게").navigationBarTitleDisplayMode(.inline)
        .toolbar { ToolbarItem(placement: .topBarTrailing) {
            NavigationLink { TrainingSettings() } label: {
                MugeIcon(name: "settings")
                    .frame(minWidth: MugeStyle.minimumTarget, minHeight: MugeStyle.minimumTarget)
            }.accessibilityLabel("설정")
        }}
        .refreshable { await catalog.refresh() }
        .confirmationDialog("진행 중인 운동을 종료할까요?", isPresented: $confirmsUnavailableFinish, titleVisibility: .visible) {
            Button("기록을 남기고 종료") {
                if !workouts.finish() { finishError = workouts.error ?? "저장하지 못했어요. 다시 시도해 주세요." }
            }
            Button("계속 유지", role: .cancel) {}
        }
    }
    private func monthlyChange(_ id: String, latest: MeasuredMax) -> String {
        let calendar = Calendar.current
        guard let monthStart = calendar.dateInterval(of: .month, for: Date())?.start,
              latest.measuredAt >= monthStart,
              let previous = workouts.measuredMaxes.filter({
                  $0.exerciseID == id && $0.measuredAt < monthStart && $0.weightKg > 0
              }).max(by: { $0.measuredAt < $1.measuredAt }) else {
            return "기록일 \(latest.measuredAt.formatted(date: .abbreviated, time: .omitted)) · 지난달 비교 자료 없음"
        }
        let change = (latest.weightKg - previous.weightKg) / previous.weightKg * 100
        return "지난달 대비 \(change > 0 ? "+" : "")\(change.formatted(.number.precision(.fractionLength(1))))% · \(previous.measuredAt.formatted(date: .abbreviated, time: .omitted)) → \(latest.measuredAt.formatted(date: .abbreviated, time: .omitted))"
    }
}

private struct MetricTile: View {
    let value: String
    let label: String
    var body: some View {
        VStack(alignment: .leading, spacing: MugeStyle.Space.sm) {
            Text(value).mugeNumber()
            Text(label).font(.caption).foregroundStyle(.secondary)
        }.frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .leading)
            .padding(MugeStyle.Space.page)
            .frame(minHeight: 118)
            .background(MugeStyle.surface, in: RoundedRectangle(cornerRadius: MugeStyle.Radius.card))
            .accessibilityElement(children: .combine)
    }
}

private struct ActionLabel: View {
    let title: String
    var symbol = "arrow.right"
    var body: some View {
        HStack { Text(title); Spacer(); MugeIcon(name: "chevron-right") }
            .font(MugeStyle.TypeStyle.action).padding(MugeStyle.Space.lg)
            .frame(minHeight: MugeStyle.actionHeight)
            .foregroundStyle(MugeStyle.onAccent)
            .background(MugeStyle.accent, in: RoundedRectangle(cornerRadius: MugeStyle.Radius.control))
    }
}

private struct RoutineLibrary: View {
    @EnvironmentObject private var catalog: CatalogStore
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: MugeStyle.Space.section) {
                if catalog.isLoading {
                    ProgressView("루틴을 불러오고 있어요").frame(maxWidth: .infinity)
                } else if let error = catalog.error {
                    MugeCard {
                        Text("루틴을 불러오지 못했어요").font(MugeStyle.TypeStyle.section)
                        Text(error).font(MugeStyle.TypeStyle.detail).foregroundStyle(MugeStyle.muted)
                        Button("다시 시도") { Task { await catalog.refresh() } }
                            .buttonStyle(MugePrimaryButtonStyle())
                    }
                } else if catalog.protocols.isEmpty {
                    MugeCard {
                        LilaRiveView(size: 88).frame(maxWidth: .infinity)
                        Text("공개할 루틴을 준비 중이에요").font(MugeStyle.TypeStyle.section)
                        Text("논문과 운동 구성을 검토한 루틴만 여기에 표시해요. 기록 연습은 홈에서 시작할 수 있어요.")
                            .font(MugeStyle.TypeStyle.detail).foregroundStyle(MugeStyle.muted)
                    }
                } else {
                    ForEach(catalog.protocols) { item in
                        NavigationLink { RoutineOverview(item: item) } label: { RoutineCard(item: item) }
                            .buttonStyle(.plain)
                    }
                }
            }.padding(MugeStyle.Space.page)
        }.background(MugeStyle.canvas).navigationTitle("루틴")
            .refreshable { await catalog.refresh() }
    }
}

private struct RoutineCard: View {
    let item: TrainingProtocol
    var body: some View {
        MugeCard {
            HStack {
                Text(item.status == "DEMO_ONLY" ? "체험 루틴" : "공개 루틴")
                    .font(.caption.bold()).padding(.horizontal, 10).padding(.vertical, 6)
                    .background(MugeStyle.ink.opacity(0.06), in: Capsule())
                Spacer()
                MugeIcon(name: "chevron-right")
            }
            Text(TrainingCopy.routine(item)).font(MugeStyle.TypeStyle.section)
            Text(item.status == "DEMO_ONLY"
                 ? "스쿼트부터 시작하는 오늘의 기록. 한 세트씩 운동 흐름을 익혀보세요."
                 : "운동 구성을 살펴보고 내 기록에 맞는 시작 중량을 확인해요.")
                .font(.subheadline).foregroundStyle(.secondary)
            HStack {
                Text("\(item.sessions.count)개 구성")
                Spacer()
                Text("구성 살펴보기").fontWeight(.semibold)
            }.font(.caption)
        }
    }
}

private struct RoutineOverview: View {
    let item: TrainingProtocol
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: MugeStyle.Space.section) {
                Text(TrainingCopy.routine(item)).font(MugeStyle.TypeStyle.hero)
                Text(item.status == "DEMO_ONLY" ? "실제 운동 기록으로 이어지는 체험용 구성" : "시작하기 전에 운동 구성을 확인하세요.")
                    .foregroundStyle(.secondary)
                MugeCard {
                    Text(item.status == "DEMO_ONLY" ? "기록 연습 · 논문 루틴 아님" : "운동 구성").font(.headline)
                    Text(item.status == "DEMO_ONLY"
                         ? "기록과 휴식 흐름을 확인하는 예시입니다. 외부 루틴을 논문 검증까지 마친 결과로 표시하지 않습니다."
                         : "공개 상태를 확인한 루틴입니다. 개인에게 최적이라는 의미는 아니며, 운동 경험과 당일 상태를 함께 고려하세요.")
                        .font(.subheadline).foregroundStyle(.secondary)
                }
                ForEach(item.sessions) { session in
                    MugeCard {
                        Text(TrainingCopy.session(session)).font(MugeStyle.TypeStyle.card)
                        ForEach(Array(session.exercises.enumerated()), id: \.element.id) { index, exercise in
                            HStack(spacing: MugeStyle.Space.lg) {
                                Text(String(format: "%02d", index + 1))
                                    .font(.title2.bold().monospacedDigit()).foregroundStyle(.tertiary)
                                VStack(alignment: .leading, spacing: MugeStyle.Space.xs) {
                                    Text(TrainingCopy.exercise(exercise.id)).font(.headline)
                                    Text("\(exercise.sets)세트 × \(exercise.reps)회 · 휴식 \(exercise.restSeconds)초")
                                        .font(.caption).foregroundStyle(.secondary)
                                }
                                Spacer()
                            }.padding(.vertical, 5)
                        }
                        NavigationLink { GuidedWorkoutView(item: item, session: session) } label: {
                            ActionLabel(title: "시작 무게 확인")
                        }.buttonStyle(.plain)
                    }
                }
                NavigationLink { ResearchNotes() } label: {
                    MugeCard {
                        Text("구성에 참고할 수 있는 연구").font(.headline)
                        Text("높은 중량과 여러 세트, 휴식 시간에 관한 연구를 읽어보세요. 이 구성 자체의 검증 결과와는 구분합니다.")
                            .font(.subheadline).foregroundStyle(.secondary)
                        Text("연구 요약과 원문 보기 →").font(.footnote.bold())
                    }
                }.buttonStyle(.plain)
            }.padding(MugeStyle.Space.page)
        }.background(MugeStyle.canvas).navigationTitle("루틴 살펴보기").navigationBarTitleDisplayMode(.inline)
    }
}

private struct ResearchNotes: View {
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: MugeStyle.Space.section) {
                Text("왜 이렇게\n운동할까요?").font(.system(size: 34, weight: .black)).tracking(-1)
                Text("연구는 선택의 근거예요. 한 사람에게 맞는 완성된 정답은 아니에요.")
                    .foregroundStyle(.secondary)
                MugeCard {
                    Text("01  무게와 세트").font(.caption.bold()).foregroundStyle(.secondary)
                    Text("힘을 키울 때와\n근육을 키울 때").font(MugeStyle.TypeStyle.section)
                    Text("2023년 체계적 문헌고찰과 네트워크 메타분석은 다양한 저항 운동 구성을 비교했어요. 높은 중량은 근력 향상에서, 여러 세트는 근비대에서 유리한 경향을 보였어요.")
                        .font(.subheadline)
                    Text("근력 연구 178편 · 근비대 연구 119편").font(.caption.bold())
                    Text("“높은 부하(1회 최대 중량의 80% 초과) 처방에서 근력 증가가 가장 컸다.”").font(.subheadline).italic()
                    Text("논문 초록의 한국어 번역 인용 · 모든 사람에게 최대 중량의 80% 이상을 권하는 의미는 아닙니다.").font(.caption).foregroundStyle(.secondary)
                    Text("다양한 참가자의 평균 결과입니다. 특정 세트 수나 중량 비율이 모든 사람에게 최적이라는 뜻은 아니에요.")
                        .font(.footnote).foregroundStyle(.secondary)
                    Link("논문 원문 열기", destination: URL(string: "https://pubmed.ncbi.nlm.nih.gov/37414459/")!)
                        .font(.subheadline.bold())
                }
                MugeCard {
                    Text("02  세트 사이 휴식").font(.caption.bold()).foregroundStyle(.secondary)
                    Text("조금 더 쉬면\n다음 세트가 달라질까요?").font(MugeStyle.TypeStyle.section)
                    Text("2024년 메타분석에서는 60초보다 긴 휴식에 작은 근비대 이점이 있을 가능성을 제시했어요. 90초를 넘겨 더 쉴 때의 추가 이점은 명확하지 않았어요.")
                        .font(.subheadline)
                    Text("“세트 사이 90초를 넘겨 쉴 때 근비대에서 뚜렷한 차이를 발견하지 못했다.”").font(.subheadline).italic()
                    Text("논문 초록의 한국어 번역 인용").font(.caption).foregroundStyle(.secondary)
                    Text("효과의 크기와 불확실성").font(.headline)
                    Chart {
                        RuleMark(xStart: .value("하한", -0.27), xEnd: .value("상한", 0.51), y: .value("부위", "팔"))
                        PointMark(x: .value("효과", 0.13), y: .value("부위", "팔")).symbolSize(70)
                        RuleMark(xStart: .value("하한", -0.13), xEnd: .value("상한", 0.43), y: .value("부위", "허벅지"))
                        PointMark(x: .value("효과", 0.17), y: .value("부위", "허벅지")).symbolSize(70)
                        RuleMark(x: .value("차이 없음", 0)).lineStyle(StrokeStyle(lineWidth: 1, dash: [4, 4])).foregroundStyle(.secondary)
                    }.chartXScale(domain: -0.35...0.6).frame(height: 130).foregroundStyle(MugeStyle.ink)
                        .accessibilityLabel("긴 휴식과 짧은 휴식의 표준화 효과. 팔 0.13, 구간 마이너스 0.27에서 0.51. 허벅지 0.17, 구간 마이너스 0.13에서 0.43. 두 구간 모두 0을 포함합니다.")
                    Text("점은 추정 효과, 선은 95% 신용구간입니다. 두 구간 모두 0을 포함해 차이가 없을 가능성도 남아 있어요. 오른쪽이 긴 휴식에 유리하며, 근육 증가율을 뜻하지 않습니다.")
                        .font(.footnote).foregroundStyle(.secondary)
                    Link("논문 원문 열기", destination: URL(string: "https://www.frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2024.1429789/full")!)
                        .font(.subheadline.bold())
                }
                MugeCard {
                    Text("앱에 적용할 때의 기준").font(.headline)
                    Text("연구 원칙 → 운동 구성 검토 → 개인 기록 확인 순서로 구분합니다. 현재 체험 루틴은 이 전체 검증을 통과한 논문 기반 처방이 아닙니다. 중량 제안도 시작점이며, 통증이나 자세 무너짐이 있으면 중단하세요.")
                        .font(.subheadline).foregroundStyle(.secondary)
                }
            }.padding(MugeStyle.Space.page)
        }.background(MugeStyle.canvas).navigationTitle("운동의 근거").navigationBarTitleDisplayMode(.inline)
    }
}

private struct TrainingHistory: View {
    @State private var selection = 0
    var body: some View {
        VStack(spacing: 0) {
            Picker("기록 종류", selection: $selection) {
                Text("운동 기록").tag(0)
                Text("성장").tag(1)
            }.pickerStyle(.segmented).padding(MugeStyle.Space.page)
            if selection == 0 { WorkoutHistoryList() }
            else { TrainingGrowth() }
        }.background(MugeStyle.canvas).navigationTitle("기록")
    }
}

private struct WorkoutHistoryList: View {
    @EnvironmentObject private var workouts: WorkoutStore
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: MugeStyle.Space.page) {
                if workouts.history.isEmpty {
                    ContentUnavailableView {
                        Label("아직 운동 기록이 없어요", image: "lucide-dumbbell")
                    } description: {
                        Text("운동을 마치면 세트별 기록을 볼 수 있어요.")
                    }
                }
                ForEach(workouts.history.reversed()) { workout in
                    NavigationLink { WorkoutHistoryDetail(workout: workout) } label: {
                        MugeCard {
                            HStack {
                                Text(workout.startedAt, format: .dateTime.month().day().weekday()).font(.headline)
                                Spacer()
                                MugeIcon(name: "chevron-right")
                            }
                            Text("운동 기록").font(MugeStyle.TypeStyle.card)
                            Text("\(workout.setIDs.count)세트 · 기록 살펴보기").font(.subheadline).foregroundStyle(.secondary)
                        }
                    }.buttonStyle(.plain)
                }
            }.padding(MugeStyle.Space.page)
        }.background(MugeStyle.canvas).navigationTitle("기록")
    }
}

private struct WorkoutHistoryDetail: View {
    @AppStorage("displayUnit") private var unit: MassUnit = .kg
    let workout: ActiveWorkout
    @EnvironmentObject private var workouts: WorkoutStore
    @State private var editing: LoggedSet?
    private var records: [LoggedSet] {
        workouts.logs.filter { workout.setIDs.contains($0.id) }
    }
    var body: some View {
        List {
            Section("운동 요약") {
                LabeledContent("날짜", value: workout.startedAt.formatted(date: .abbreviated, time: .shortened))
                LabeledContent("기록한 세트", value: "\(records.count)세트")
                LabeledContent("총중량", value: unit.label(StrengthMetrics.volume(records)))
                Text("이 기록에는 원래 계획·실제 휴식 비교 자료가 없어요.")
                    .font(MugeStyle.TypeStyle.note).foregroundStyle(MugeStyle.muted)
            }
            Section("세트 기록 · 눌러서 수정") {
                ForEach(records) { set in
                    Button { editing = set } label: {
                        HStack {
                            Text(TrainingCopy.exercise(set.exerciseID))
                            Spacer()
                            Text("\(unit.label(set.weightKg)) × \(set.reps)회").foregroundStyle(.secondary)
                        }
                    }.foregroundStyle(MugeStyle.ink)
                }
            }
        }.navigationTitle("운동 기록")
            .sheet(item: $editing) { EditSetSheet(set: $0) }
    }
}

private struct TrainingGrowth: View {
    @AppStorage("displayUnit") private var unit: MassUnit = .kg
    @EnvironmentObject private var workouts: WorkoutStore
    @State private var exercise = "squat"
    private var records: [LoggedSet] { workouts.records(for: exercise).sorted { $0.performedAt < $1.performedAt } }
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: MugeStyle.Space.section) {
                Picker("종목", selection: $exercise) {
                    Text("스쿼트").tag("squat")
                    Text("벤치프레스").tag("bench")
                    Text("데드리프트").tag("deadlift")
                }.pickerStyle(.segmented)
                MugeCard {
                    Text("실제 최대 중량").font(MugeStyle.TypeStyle.card)
                    let actual = workouts.measuredMaxes.filter { $0.exerciseID == exercise }
                        .sorted { $0.measuredAt < $1.measuredAt }
                    if let latest = actual.last {
                        Text(unit.label(latest.weightKg)).mugeNumber()
                        Chart(actual) { record in
                            PointMark(x: .value("날짜", record.measuredAt),
                                      y: .value("실측 (\(unit.rawValue))", unit.display(record.weightKg)))
                        }.frame(height: 180).foregroundStyle(MugeStyle.accent)
                        Text("실제로 한 번 들어 올린 기록만 표시해요.")
                            .font(MugeStyle.TypeStyle.note).foregroundStyle(MugeStyle.muted)
                    } else {
                        Text("실제 측정 기록이 없어요. 추정값으로 채우지 않아요.")
                            .font(MugeStyle.TypeStyle.detail).foregroundStyle(MugeStyle.muted)
                    }
                }
                MugeCard {
                    Text("반복 기록으로 본 추정 최대 중량").font(.headline)
                    if let value = StrengthMetrics.bestEstimatedOneRepMax(records) {
                        HStack(alignment: .firstTextBaseline, spacing: MugeStyle.Space.xs) {
                            Text(unit.number(value))
                                .mugeNumber(size: 44)
                            Text(unit.rawValue).foregroundStyle(.secondary)
                        }
                        Chart(records) { record in
                            if let estimate = StrengthMetrics.estimatedOneRepMax(weightKg: record.weightKg, reps: record.reps) {
                                PointMark(x: .value("날짜", record.performedAt), y: .value("추정 중량 (\(unit.rawValue))", unit.display(estimate)))
                            }
                        }.frame(height: 180).foregroundStyle(MugeStyle.ink)
                    } else {
                        Text("아직 추정할 기록이 없어요").font(MugeStyle.TypeStyle.card)
                    }
                    Text("1~10회 반복 기록으로 계산한 추정치예요. 실제로 한 번 들어 올린 최대 중량과 구분하세요.")
                        .font(.footnote).foregroundStyle(.secondary)
                }
                MugeMetricRow {
                    MetricTile(value: "\(records.count)", label: "이 종목의 세트")
                    MetricTile(value: unit.number(StrengthMetrics.volume(records)), label: "총중량 · \(unit.rawValue)")
                }
                NavigationLink { StrengthSetupView() } label: { ActionLabel(title: "실제 최대 중량 관리하기") }.buttonStyle(.plain)
            }.padding(MugeStyle.Space.page)
        }.background(MugeStyle.canvas).navigationTitle("성장")
    }
}

private struct TrainingSettings: View {
    @AppStorage("displayUnit") private var unit: MassUnit = .kg
    @State private var showsIntroduction = false
    var body: some View {
        List {
            Section("내 운동 기준") {
                Picker("중량 단위", selection: $unit) {
                    ForEach(MassUnit.allCases, id: \.self) { Text($0.rawValue).tag($0) }
                }
                Text("표시 단위만 바뀌며 저장된 중량은 유지돼요.")
                    .font(MugeStyle.TypeStyle.note).foregroundStyle(MugeStyle.muted)
            }
            Section("내 데이터") {
                NavigationLink("기록 백업과 복원") { BackupView() }
                NavigationLink("계정과 동기화") { CloudAccountView() }
            }
            Section("운동 안내") {
                NavigationLink("오픈소스 라이선스") {
                    ScrollView {
                        Text(MugeThirdPartyNotices.lucide)
                            .font(MugeStyle.TypeStyle.note).textSelection(.enabled)
                            .padding(MugeStyle.Space.page)
                    }.navigationTitle("Lucide")
                }
                Button("처음 안내 다시 보기") { showsIntroduction = true }
                NavigationLink("운동의 근거") { ResearchNotes() }
                Text("릴라는 시작과 준비, 운동을 마친 순간에 함께해요. 운동과 휴식 중에는 기록과 타이머에 집중할 수 있어요.")
                    .font(.subheadline).foregroundStyle(.secondary)
            }
        }.navigationTitle("설정")
            .fullScreenCover(isPresented: $showsIntroduction) { TrainingIntroduction() }
    }
}

private struct TrainingIntroduction: View {
    @Environment(\.dismiss) private var dismiss
    @AppStorage("onboardingCompleted.v2") private var completed = false
    @State private var page = 0
    private let titles = [
        "스쿼트·벤치·데드리프트를 기록해요.",
        "논문을 검토해 루틴을 준비해요.",
        "내 기록의 변화를 확인해요."
    ]
    private let descriptions = [
        "최대 중량을 입력하고, 실제 운동한 무게와 횟수를 남겨 보세요.",
        "공개된 루틴의 운동 구성과 출처를 확인할 수 있어요. 검토 중인 루틴은 공개하지 않아요.",
        "실제 측정과 추정값을 구분해 볼 수 있어요. 연구의 평균 결과는 나의 예상 성장률이 아니에요."
    ]
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: MugeStyle.Space.section) {
                    Text("\(page + 1) / 3").font(MugeStyle.TypeStyle.detail).foregroundStyle(MugeStyle.muted)
                    LilaRiveView(size: 144).frame(maxWidth: .infinity)
                    Text(titles[page]).font(MugeStyle.TypeStyle.hero).accessibilityAddTraits(.isHeader)
                    Text(descriptions[page]).font(MugeStyle.TypeStyle.body).foregroundStyle(MugeStyle.muted)
                }.padding(MugeStyle.Space.page)
            }
            .background(MugeStyle.canvas)
            .toolbar { ToolbarItem(placement: .topBarTrailing) {
                Button("건너뛰기") { close() }
            }}
            .safeAreaInset(edge: .bottom) {
                VStack(spacing: MugeStyle.Space.sm) {
                    Button(page == 2 ? "시작하기" : "다음") {
                        if page == 2 { close() } else { page += 1 }
                    }.buttonStyle(MugePrimaryButtonStyle())
                    if page > 0 {
                        Button("이전") { page -= 1 }.frame(minHeight: MugeStyle.minimumTarget)
                    }
                }.padding(MugeStyle.Space.page).background(.regularMaterial)
            }
        }.interactiveDismissDisabled()
    }
    private func close() { completed = true; dismiss() }
}
