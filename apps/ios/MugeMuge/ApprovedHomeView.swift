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
        item.status == "DEMO_ONLY" ? "전신 기초 · 기록 체험" : "맞춤 운동 루틴"
    }
    static func session(_ session: TrainingSession) -> String {
        "전신 운동 · \(session.exercises.count)종목"
    }
}

struct ApprovedHomeView: View {
    @EnvironmentObject private var catalog: CatalogStore
    var body: some View {
        TabView {
            NavigationStack { TrainingHome() }
                .tabItem { Label("홈", systemImage: "house.fill") }
            NavigationStack { RoutineLibrary() }
                .tabItem { Label("루틴", systemImage: "square.stack.3d.up.fill") }
            NavigationStack { TrainingHistory() }
                .tabItem { Label("기록", systemImage: "calendar") }
            NavigationStack { TrainingGrowth() }
                .tabItem { Label("성장", systemImage: "chart.xyaxis.line") }
        }
        .tint(MugeStyle.ink)
        .task { await catalog.refresh() }
    }
}

private struct TrainingHome: View {
    @State private var confirmsUnavailableFinish = false
    @State private var finishError: String?
    @EnvironmentObject private var workouts: WorkoutStore
    @EnvironmentObject private var catalog: CatalogStore
    private var activeRoute: (TrainingProtocol, TrainingSession)? {
        guard let active = workouts.active,
              let item = (catalog.protocols + catalog.demo).first(where: {
                  $0.id == active.protocolID && $0.version == active.protocolVersion
              }), let session = item.sessions.first(where: { $0.id == active.sessionID }) else { return nil }
        return (item, session)
    }
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: MugeStyle.Space.section) {
                MugeAdaptiveRow {
                    VStack(alignment: .leading, spacing: 10) {
                        Text(Date.now, format: .dateTime.month().day().weekday())
                            .font(.subheadline).foregroundStyle(.secondary)
                        Text("어제보다\n단단한 나.").font(MugeStyle.TypeStyle.hero)
                        Text("오늘의 한 세트가 쌓이는 곳").font(.subheadline).foregroundStyle(.secondary)
                    }
                    Spacer(minLength: 0)
                    LilaRiveView(level: 1, size: 120).padding(.top, 22)
                }
                if let active = workouts.active {
                    MugeCard {
                        Label("이어가는 운동", systemImage: "play.circle.fill").font(.caption.bold())
                        Text("멈춘 자리에서 다시").font(MugeStyle.TypeStyle.section)
                        Text("\(active.setIDs.count)세트를 기록했어요.").foregroundStyle(.secondary)
                        if let route = activeRoute {
                            NavigationLink { GuidedWorkoutView(item: route.0, session: route.1) } label: {
                                ActionLabel(title: "운동 이어 하기", symbol: "arrow.right")
                            }.buttonStyle(.plain)
                        } else {
                            Text("진행 중인 운동 구성을 찾을 수 없어요. 연결을 확인해 새로고침하거나, 지금까지의 기록을 남기고 종료할 수 있어요.")
                                .font(.footnote).foregroundStyle(.secondary)
                            Button("기록을 보존하고 운동 종료") { confirmsUnavailableFinish = true }
                                .font(.subheadline.bold())
                            if let finishError {
                                Text(finishError).font(.footnote).foregroundStyle(.red)
                            }
                        }
                    }
                }
                NavigationLink { StrengthSetupView() } label: {
                    MugeCard {
                        HStack {
                            Image(systemName: "scalemass").font(.title2)
                            Spacer()
                            Image(systemName: "arrow.up.right")
                        }
                        Text(workouts.measuredMaxes.isEmpty ? "내 힘의 기준부터." : "내 최대 중량 살펴보기")
                            .font(MugeStyle.TypeStyle.section)
                        Text(workouts.measuredMaxes.isEmpty
                             ? "최대 중량을 기록하거나, 반복 기록으로 추정하고 측정 안내를 받아보세요."
                             : "실제 측정과 추정치를 구분해 다음 운동의 기준을 확인해요.")
                            .font(.subheadline).foregroundStyle(.secondary)
                        Text("최대 중량 기록 · 측정 안내").font(.footnote.bold())
                    }
                }.buttonStyle(.plain)
                MugeMetricRow {
                    MetricTile(value: "\(workouts.history.count)", label: "완료한 운동")
                    MetricTile(value: "\(workouts.logs.count)", label: "쌓인 세트")
                }
                MugeSectionTitle(title: "이유를 알고 시작해요", subtitle: "운동 구성과 근거를 함께 읽는 루틴")
                if let item = (catalog.protocols + catalog.demo).first {
                    NavigationLink { RoutineOverview(item: item) } label: { RoutineCard(item: item) }
                        .buttonStyle(.plain)
                } else {
                    ContentUnavailableView("루틴을 불러오는 중", systemImage: "square.stack")
                }
                NavigationLink { ResearchNotes() } label: {
                    Label("운동을 설계하는 연구 살펴보기", systemImage: "text.book.closed")
                        .font(.subheadline.bold())
                }
                if let error = catalog.error { Text(error).font(.footnote).foregroundStyle(.secondary) }
            }.padding(MugeStyle.Space.page)
        }
        .background(MugeStyle.canvas)
        .navigationTitle("무게무게").navigationBarTitleDisplayMode(.inline)
        .toolbar { ToolbarItem(placement: .topBarTrailing) {
            NavigationLink { TrainingSettings() } label: {
                Image(systemName: "gearshape")
                    .frame(minWidth: MugeStyle.minimumTarget, minHeight: MugeStyle.minimumTarget)
            }
                .accessibilityLabel("설정")
        }}
        .refreshable { await catalog.refresh() }
        .confirmationDialog("진행 중인 운동을 종료할까요?", isPresented: $confirmsUnavailableFinish, titleVisibility: .visible) {
            Button("기록을 보존하고 종료") {
                finishError = nil
                if !workouts.finish() {
                    finishError = workouts.error ?? "종료 내용을 저장하지 못했어요. 다시 시도해주세요."
                }
            }
            Button("계속 유지", role: .cancel) {}
        } message: {
            Text("지금까지 입력한 세트를 운동 기록에 보존합니다. 종료하면 새로운 운동을 시작할 수 있어요.")
        }
    }
}

private struct MetricTile: View {
    let value: String
    let label: String
    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
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
        HStack { Text(title); Spacer(); Image(systemName: symbol) }
            .font(MugeStyle.TypeStyle.action).padding(MugeStyle.Space.lg)
            .frame(minHeight: MugeStyle.minimumTarget)
            .foregroundStyle(MugeStyle.onAccent)
            .background(MugeStyle.ink, in: RoundedRectangle(cornerRadius: MugeStyle.Radius.control))
    }
}

private struct RoutineLibrary: View {
    @EnvironmentObject private var catalog: CatalogStore
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: MugeStyle.Space.page) {
                Text("내 운동에는\n이유가 있으니까.")
                    .font(MugeStyle.TypeStyle.hero)
                MugeSectionTitle(title: "운동 루틴", subtitle: "구성, 시작 중량, 근거를 확인하고 시작해요.")
                if catalog.protocols.isEmpty {
                    MugeCard {
                        Label("검증을 마친 루틴을 준비 중이에요", systemImage: "checkmark.shield")
                            .font(.headline)
                        Text("아래 체험 루틴은 기록 기능을 둘러보는 예시예요. 논문으로 검증된 처방으로 제공하지 않아요.")
                            .font(.subheadline).foregroundStyle(.secondary)
                    }
                }
                ForEach(catalog.protocols) { item in
                    NavigationLink { RoutineOverview(item: item) } label: { RoutineCard(item: item) }.buttonStyle(.plain)
                }
                ForEach(catalog.demo) { item in
                    NavigationLink { RoutineOverview(item: item) } label: { RoutineCard(item: item) }.buttonStyle(.plain)
                }
                NavigationLink { ResearchNotes() } label: {
                    MugeCard {
                        Label("논문에서 배운 운동 원칙", systemImage: "text.book.closed.fill").font(.headline)
                        Text("무게 · 세트 · 휴식, 무엇이 달라질까요?").font(.subheadline).foregroundStyle(.secondary)
                        Text("근거와 한계 읽기 →").font(.footnote.bold())
                    }
                }.buttonStyle(.plain)
                if let error = catalog.error { Text(error).font(.footnote).foregroundStyle(.secondary) }
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
                Image(systemName: "arrow.up.right").font(.title3)
            }
            Text(TrainingCopy.routine(item)).font(MugeStyle.TypeStyle.section)
            Text(item.status == "DEMO_ONLY"
                 ? "스쿼트부터 시작하는 오늘의 기록. 한 세트씩 운동 흐름을 익혀보세요."
                 : "운동 구성을 살펴보고 내 기록에 맞는 시작 중량을 확인해요.")
                .font(.subheadline).foregroundStyle(.secondary)
            HStack {
                Label("\(item.sessions.count)개 구성", systemImage: "rectangle.stack")
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
                    Label("이 루틴을 읽는 방법", systemImage: "info.circle").font(.headline)
                    Text(item.status == "DEMO_ONLY"
                         ? "기록과 휴식 흐름을 확인하는 예시입니다. 외부 루틴을 논문 검증까지 마친 결과로 표시하지 않습니다."
                         : "공개 상태를 확인한 루틴입니다. 개인에게 최적이라는 의미는 아니며, 운동 경험과 당일 상태를 함께 고려하세요.")
                        .font(.subheadline).foregroundStyle(.secondary)
                }
                ForEach(item.sessions) { session in
                    MugeCard {
                        Text(TrainingCopy.session(session)).font(MugeStyle.TypeStyle.card)
                        ForEach(Array(session.exercises.enumerated()), id: \.element.id) { index, exercise in
                            HStack(spacing: 14) {
                                Text(String(format: "%02d", index + 1))
                                    .font(.title2.bold().monospacedDigit()).foregroundStyle(.tertiary)
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(TrainingCopy.exercise(exercise.id)).font(.headline)
                                    Text("\(exercise.sets)세트 × \(exercise.reps)회 · 휴식 \(exercise.restSeconds)초")
                                        .font(.caption).foregroundStyle(.secondary)
                                }
                                Spacer()
                            }.padding(.vertical, 5)
                        }
                        NavigationLink { GuidedWorkoutView(item: item, session: session) } label: {
                            ActionLabel(title: "시작 중량 확인하기")
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
    @EnvironmentObject private var workouts: WorkoutStore
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                Text("쌓인 기록이\n나를 말해줘요.").font(MugeStyle.TypeStyle.hero)
                if workouts.history.isEmpty {
                    ContentUnavailableView("첫 기록을 기다리고 있어요", systemImage: "calendar.badge.plus",
                                           description: Text("루틴에서 운동을 시작하고 완료하면 여기에 쌓여요."))
                }
                ForEach(workouts.history.reversed()) { workout in
                    NavigationLink { WorkoutHistoryDetail(workout: workout) } label: {
                        MugeCard {
                            HStack {
                                Text(workout.startedAt, format: .dateTime.month().day().weekday()).font(.headline)
                                Spacer()
                                Image(systemName: "chevron.right").font(.caption)
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
                LabeledContent("누적 중량", value: "\(StrengthMetrics.volume(records).formatted())킬로그램")
            }
            Section("세트 기록 · 눌러서 수정") {
                ForEach(records) { set in
                    Button { editing = set } label: {
                        HStack {
                            Text(TrainingCopy.exercise(set.exerciseID))
                            Spacer()
                            Text("\(set.weightKg.formatted())킬로그램 × \(set.reps)회").foregroundStyle(.secondary)
                        }
                    }.foregroundStyle(MugeStyle.ink)
                }
            }
        }.navigationTitle("운동 기록")
            .sheet(item: $editing) { EditSetSheet(set: $0) }
    }
}

private struct TrainingGrowth: View {
    @EnvironmentObject private var workouts: WorkoutStore
    @State private var exercise = "squat"
    private var records: [LoggedSet] { workouts.records(for: exercise).sorted { $0.performedAt < $1.performedAt } }
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: MugeStyle.Space.section) {
                Text("숫자보다 중요한 건,\n계속하고 있다는 것.")
                    .font(MugeStyle.TypeStyle.hero)
                Picker("종목", selection: $exercise) {
                    Text("스쿼트").tag("squat")
                    Text("벤치프레스").tag("bench")
                    Text("데드리프트").tag("deadlift")
                }.pickerStyle(.segmented)
                MugeCard {
                    Text("반복 기록으로 본 추정 최대 중량").font(.headline)
                    if let value = StrengthMetrics.bestEstimatedOneRepMax(records) {
                        HStack(alignment: .firstTextBaseline, spacing: 5) {
                            Text(value.formatted(.number.precision(.fractionLength(1))))
                                .mugeNumber(size: 44)
                            Text("킬로그램").foregroundStyle(.secondary)
                        }
                        Chart(records) { record in
                            if let estimate = StrengthMetrics.estimatedOneRepMax(weightKg: record.weightKg, reps: record.reps) {
                                PointMark(x: .value("날짜", record.performedAt), y: .value("추정 중량", estimate))
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
                    MetricTile(value: StrengthMetrics.volume(records).formatted(.number.precision(.fractionLength(0))), label: "누적 중량 · 킬로그램")
                }
                NavigationLink { StrengthSetupView() } label: { ActionLabel(title: "실제 최대 중량 관리하기") }.buttonStyle(.plain)
            }.padding(MugeStyle.Space.page)
        }.background(MugeStyle.canvas).navigationTitle("성장")
    }
}

private struct TrainingSettings: View {
    var body: some View {
        List {
            Section("내 운동 기준") {
                NavigationLink("최대 중량 기록 · 측정 안내") { StrengthSetupView() }
            }
            Section("내 데이터") {
                NavigationLink("기록 백업과 복원") { BackupView() }
                NavigationLink("계정과 동기화") { CloudAccountView() }
            }
            Section("운동 안내") {
                NavigationLink("운동의 근거") { ResearchNotes() }
                Text("릴라는 시작과 준비, 운동을 마친 순간에 함께해요. 운동과 휴식 중에는 기록과 타이머에 집중할 수 있어요.")
                    .font(.subheadline).foregroundStyle(.secondary)
            }
        }.navigationTitle("설정")
    }
}
