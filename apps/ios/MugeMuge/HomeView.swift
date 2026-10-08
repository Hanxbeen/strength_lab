import SwiftUI
import Charts

struct HomeView: View {
    @EnvironmentObject private var catalog: CatalogStore
    @EnvironmentObject private var workouts: WorkoutStore
    @EnvironmentObject private var training: TrainingState

    var body: some View {
        TabView {
            NavigationStack {
                List {
                    Section {
                        Text("논문으로 고르고, 바벨로 검증한다.").font(.headline)
                        Text("연구 검증이 완료된 처방만 연구 루틴으로 표시합니다.")
                            .font(.caption).foregroundStyle(.secondary)
                    }
                    Section("검증된 연구 루틴") {
                        if catalog.protocols.isEmpty {
                            ContentUnavailableView("게시된 루틴이 없습니다", systemImage: "books.vertical",
                                                   description: Text("검증이 완료된 루틴만 이곳에 표시됩니다."))
                        }
                        ForEach(catalog.protocols) { item in
                            NavigationLink(item.title) { ProtocolView(item: item, isDemo: false) }
                        }
                    }
                    if let active = training.active {
                        Section("진행 중인 운동") {
                            Label(active.title, systemImage: "figure.strengthtraining.traditional")
                            Text("기록한 세트 \(active.setIDs.count)개 · 시작 \(active.startedAt.formatted(date: .abbreviated, time: .shortened))")
                                .font(.caption).foregroundStyle(.secondary)
                            Button("운동 종료") { _ = training.finish() }
                            Button("세션 폐기 (세트 기록은 유지)", role: .destructive) { _ = training.discard() }
                        }
                    }
                    Section("기록 체험 · 연구 처방 아님") {
                        ForEach(catalog.demo) { item in
                            NavigationLink(item.title) { ProtocolView(item: item, isDemo: true) }
                        }
                    }
                    if let error = catalog.error {
                        Text(error).font(.caption).foregroundStyle(.secondary)
                    }
                }
                .navigationTitle("무게무게")
                .refreshable { await catalog.refresh() }
            }
            .tabItem { Label("루틴", systemImage: "dumbbell") }

            NavigationStack {
                StrengthDashboard()
                    .navigationTitle("성장 기록")
            }
            .tabItem { Label("성장", systemImage: "chart.xyaxis.line") }
        }
        .task { await catalog.refresh() }
    }
}

struct ProtocolView: View {
    let item: TrainingProtocol
    let isDemo: Bool
    @EnvironmentObject private var training: TrainingState
    var body: some View {
        List {
            if isDemo {
                Label("기록 기능 체험 · 검증된 운동 처방이 아닙니다", systemImage: "exclamationmark.triangle")
                    .foregroundStyle(.orange)
            }
            Text(item.description)
            ForEach(item.sessions) { session in
                Section(session.title) {
                    if training.active == nil {
                        Button("이 세션 시작") {
                            _ = training.start(protocolID: item.id, version: item.version,
                                               sessionID: session.id, title: session.title)
                        }
                    } else if training.active?.sessionID == session.id &&
                                training.active?.protocolID == item.id &&
                                training.active?.protocolVersion == item.version {
                        Label("이 세션 진행 중", systemImage: "checkmark.circle")
                            .foregroundStyle(.green)
                    } else {
                        Text("다른 세션이 진행 중입니다. 먼저 종료해주세요.")
                            .font(.caption).foregroundStyle(.secondary)
                    }
                    ForEach(session.exercises) { exercise in
                        NavigationLink {
                            ExerciseView(exercise: exercise, protocolID: item.id,
                                         protocolVersion: item.version, sessionID: session.id)
                        } label: {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(exercise.name).font(.headline)
                                Text("\(exercise.sets)세트 × \(exercise.reps)회 · 휴식 \(exercise.restSeconds)초")
                                    .font(.caption).foregroundStyle(.secondary)
                            }
                        }
                    }
                }
            }
        }
        .navigationTitle(item.title)
    }
}

struct ExerciseView: View {
    let exercise: TrainingExercise
    let protocolID: String
    let protocolVersion: Int
    let sessionID: String
    @EnvironmentObject private var workouts: WorkoutStore
    @EnvironmentObject private var training: TrainingState
    @State private var weight = "20"
    @State private var reps = "5"
    private var isCurrentSession: Bool {
        training.active?.protocolID == protocolID &&
        training.active?.protocolVersion == protocolVersion &&
        training.active?.sessionID == sessionID
    }

    private var records: [LoggedSet] { workouts.records(for: exercise.id) }

    var body: some View {
        Form {
            Section(exercise.name) {
                TextField("중량 (kg)", text: $weight).keyboardType(.decimalPad)
                TextField("반복 횟수", text: $reps).keyboardType(.numberPad)
                Button("세트 완료 · 기기에 저장") {
                    let parsedWeight = Double(weight.replacingOccurrences(of: ",", with: "."))
                    guard let kg = parsedWeight, let count = Int(reps) else { return }
                    if let id = workouts.append(exerciseID: exercise.id, weightKg: kg, reps: count) {
                        _ = training.attachSet(id, restSeconds: exercise.restSeconds)
                    }
                }
                .disabled(!isCurrentSession)
                if !isCurrentSession {
                    Text("세션을 시작해야 기록할 수 있습니다.")
                        .font(.caption).foregroundStyle(.secondary)
                }
                if let error = workouts.lastError {
                    Text(error).foregroundStyle(.red).font(.caption)
                }
            }
            if isCurrentSession, let until = training.active?.restUntil {
                Section("휴식") {
                    TimelineView(.periodic(from: .now, by: 1)) { timeline in
                        Text("\(max(0, Int(ceil(until.timeIntervalSince(timeline.date)))))초 남음")
                            .font(.title2.monospacedDigit())
                    }
                    Text("앱을 닫아도 휴식 종료 시각은 유지됩니다.")
                        .font(.caption).foregroundStyle(.secondary)
                }
            }
            Section("완료한 세트") {
                ForEach(records.reversed()) { set in
                    Text("\(set.weightKg.formatted()) kg × \(set.reps)")
                }
                .onDelete { offsets in
                    let displayed = Array(records.reversed())
                    for offset in offsets {
                        let id = displayed[offset].id
                        workouts.delete(id: id)
                        training.removeSetReference(id)
                    }
                }
            }
        }
        .navigationTitle(exercise.name)
    }
}

struct StrengthDashboard: View {
    @EnvironmentObject private var workouts: WorkoutStore
    @EnvironmentObject private var training: TrainingState
    @State private var actualWeight = ""
    @State private var selected = "squat"
    private let exercises = [("squat", "Squat"), ("bench", "Bench"), ("deadlift", "Deadlift")]

    private var records: [LoggedSet] { workouts.records(for: selected) }
    private var estimates: [LoggedSet] {
        records.filter { StrengthMetrics.estimatedOneRepMax(weightKg: $0.weightKg, reps: $0.reps) != nil }
    }

    var body: some View {
        List {
            Section {
                Picker("운동", selection: $selected) {
                    ForEach(exercises, id: \.0) { item in
                        Text(item.1).tag(item.0)
                    }
                }.pickerStyle(.segmented)
            }
            Section("추정 1RM · e1RM") {
                if let best = StrengthMetrics.bestEstimatedOneRepMax(records) {
                    Text("\(best, specifier: "%.1f") kg")
                        .font(.largeTitle.bold().monospacedDigit())
                    Text("Epley 공식 · 1~10회 수행 기록 기준. 실제 측정 1RM이 아닙니다.")
                        .font(.caption).foregroundStyle(.secondary)
                } else {
                    Text("유효한 세트 기록이 없습니다.")
                        .foregroundStyle(.secondary)
                }
            }
            Section("추정 1RM 변화") {
                if estimates.isEmpty {
                    Text("기록을 추가하면 변화가 표시됩니다.").foregroundStyle(.secondary)
                } else {
                    Chart(estimates) { set in
                        if let value = StrengthMetrics.estimatedOneRepMax(weightKg: set.weightKg, reps: set.reps) {
                            PointMark(x: .value("날짜", set.performedAt),
                                      y: .value("e1RM (kg)", value))
                        }
                    }
                    .frame(height: 220)
                    Text("세트별 추정치이며 측정된 실제 1RM이나 연구 결과가 아닙니다.")
                        .font(.caption).foregroundStyle(.secondary)
                }
            }
            Section("누적 훈련량") {
                Text("\(StrengthMetrics.volume(records), specifier: "%.0f") kg · 세트 중량 × 반복")
            }
            Section("실제 측정 1RM · e1RM과 별도") {
                TextField("직접 측정한 1RM (kg)", text: $actualWeight)
                    .keyboardType(.decimalPad)
                Button("실제 1RM 기록") {
                    if let weight = Double(actualWeight.replacingOccurrences(of: ",", with: ".")),
                       training.recordMeasuredMax(exerciseID: selected, weightKg: weight) {
                        actualWeight = ""
                    }
                }
                ForEach(training.measuredMaxes.filter { $0.exerciseID == selected }.reversed()) { maxRecord in
                    Text("\(maxRecord.weightKg.formatted()) kg · \(maxRecord.measuredAt.formatted(date: .abbreviated, time: .omitted))")
                }
                Text("직접 수행한 최대 중량만 입력하세요. 추정값을 실제 1RM으로 기록하지 마세요.")
                    .font(.caption).foregroundStyle(.secondary)
            }
            Section("완료한 세션") {
                ForEach(training.history.reversed()) { workout in
                    Text("\(workout.title) · \(workout.setIDs.count)세트 · \(workout.startedAt.formatted(date: .abbreviated, time: .shortened))")
                }
            }
        }
    }
}
