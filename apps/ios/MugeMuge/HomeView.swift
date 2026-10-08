import SwiftUI

struct HomeView: View {
    @EnvironmentObject private var catalog: CatalogStore
    @EnvironmentObject private var workouts: WorkoutStore

    var body: some View {
        NavigationStack {
            List {
                Section {
                    Text("논문으로 고르고, 바벨로 검증한다.")
                        .font(.headline)
                    Text("검증되지 않은 논문은 실행형 루틴으로 제공하지 않습니다.")
                        .font(.caption).foregroundStyle(.secondary)
                }
                Section("검증된 연구 루틴") {
                    if catalog.protocols.isEmpty {
                        ContentUnavailableView("게시된 루틴이 없습니다", systemImage: "books.vertical",
                                               description: Text("연구 검증이 완료된 루틴만 이곳에 표시됩니다."))
                    }
                    ForEach(catalog.protocols) { item in
                        NavigationLink(item.title) { ProtocolView(item: item, isDemo: false) }
                    }
                }
                Section("기록 기능 체험 · 연구 근거 아님") {
                    ForEach(catalog.demo) { item in
                        NavigationLink(item.title) { ProtocolView(item: item, isDemo: true) }
                    }
                }
                Section("내 운동 기록") {
                    Text("완료 세트 \(workouts.logs.count)개")
                    ForEach(workouts.logs.suffix(5).reversed()) { set in
                        Text("\(set.exerciseID) · \(set.weightKg.formatted()) kg × \(set.reps)")
                    }
                }
                if let error = catalog.error {
                    Text(error).foregroundStyle(.secondary)
                }
            }
            .navigationTitle("무게무게")
            .task { await catalog.refresh() }
            .refreshable { await catalog.refresh() }
        }
    }
}

struct ProtocolView: View {
    let item: TrainingProtocol
    let isDemo: Bool
    var body: some View {
        List {
            if isDemo {
                Label("체험용 데이터 · 연구에서 검증된 루틴이 아닙니다", systemImage: "exclamationmark.triangle")
                    .foregroundStyle(.orange)
            }
            Text(item.description)
            ForEach(item.sessions) { session in
                Section(session.title) {
                    ForEach(session.exercises) { exercise in
                        NavigationLink {
                            ExerciseView(exercise: exercise)
                        } label: {
                            VStack(alignment: .leading) {
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

    var body: some View {
        Form {
            Section(exercise.name) {
                TextField("중량 (kg)", text: $weight).keyboardType(.decimalPad)
                TextField("반복 횟수", text: $reps).keyboardType(.numberPad)
                Button("세트 완료 · 기기에 저장") {
                    guard let kg = Double(weight), let count = Int(reps), kg >= 0, count > 0 else { return }
                    workouts.append(exerciseID: exercise.id, weightKg: kg, reps: count)
                    restUntil = Date().addingTimeInterval(TimeInterval(exercise.restSeconds))
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
                ForEach(workouts.logs.filter { $0.exerciseID == exercise.id }) { set in
                    Text("\(set.weightKg.formatted()) kg × \(set.reps)")
                }
            }
        }
        .navigationTitle(exercise.name)
    }
}
