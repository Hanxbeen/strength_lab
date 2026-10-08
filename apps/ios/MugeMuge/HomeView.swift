import SwiftUI
import Charts

struct HomeView: View {
    @EnvironmentObject private var catalog: CatalogStore
    @EnvironmentObject private var workouts: WorkoutStore

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
    var body: some View {
        List {
            if isDemo {
                Label("기록 기능 체험 · 검증된 운동 처방이 아닙니다", systemImage: "exclamationmark.triangle")
                    .foregroundStyle(.orange)
            }
            Text(item.description)
            ForEach(item.sessions) { session in
                Section(session.title) {
                    ForEach(session.exercises) { exercise in
                        NavigationLink {
                            ExerciseView(exercise: exercise)
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
    @EnvironmentObject private var workouts: WorkoutStore
    @State private var weight = "20"
    @State private var reps = "5"
    @State private var restUntil: Date?

    private var records: [LoggedSet] { workouts.records(for: exercise.id) }

    var body: some View {
        Form {
            Section(exercise.name) {
                TextField("중량 (kg)", text: $weight).keyboardType(.decimalPad)
                TextField("반복 횟수", text: $reps).keyboardType(.numberPad)
                Button("세트 완료 · 기기에 저장") {
                    let parsedWeight = Double(weight.replacingOccurrences(of: ",", with: "."))
                    guard let kg = parsedWeight, let count = Int(reps) else { return }
                    if workouts.append(exerciseID: exercise.id, weightKg: kg, reps: count) {
                        restUntil = Date().addingTimeInterval(TimeInterval(exercise.restSeconds))
                    }
                }
                if let error = workouts.lastError {
                    Text(error).foregroundStyle(.red).font(.caption)
                }
            }
            if let until = restUntil {
                Section("휴식") {
                    TimelineView(.periodic(from: .now, by: 1)) { timeline in
                        Text("\(max(0, Int(ceil(until.timeIntervalSince(timeline.date)))))초 남음")
                            .font(.title2.monospacedDigit())
                    }
                    Button("휴식 종료") { restUntil = nil }
                }
            }
            Section("완료한 세트") {
                ForEach(records.reversed()) { set in
                    Text("\(set.weightKg.formatted()) kg × \(set.reps)")
                }
                .onDelete { offsets in
                    let displayed = Array(records.reversed())
                    for offset in offsets { workouts.delete(id: displayed[offset].id) }
                }
            }
        }
        .navigationTitle(exercise.name)
    }
}

struct StrengthDashboard: View {
    @EnvironmentObject private var workouts: WorkoutStore
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
            Section("실제 1RM") {
                Text("실제 1RM 테스트 기록 기능은 후속 구현 예정입니다.")
                    .foregroundStyle(.secondary)
            }
        }
    }
}
