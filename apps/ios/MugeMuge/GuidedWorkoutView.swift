import SwiftUI

/// Guided sessions only write through WorkoutStore's atomic operations.
struct GuidedWorkoutView: View {
    let item: TrainingProtocol
    let session: TrainingSession
    @EnvironmentObject private var workouts: WorkoutStore
    @Environment(\.dismiss) private var dismiss
    @State private var weights: [String: String] = [:]
    @State private var exerciseIndex = 0
    @State private var repetitions = ""
    @State private var showRest = false
    @State private var showStop = false
    @State private var editingSet: LoggedSet?
    @State private var error: String?
    @State private var completed: ActiveWorkout?
    @State private var stoppedEarly = false
    @State private var prepared = false

    private var matchesActive: Bool {
        guard let active = workouts.active else { return false }
        return active.protocolID == item.id && active.protocolVersion == item.version
            && active.sessionID == session.id
    }
    private var activeRecords: [LoggedSet] {
        let ids = Set((completed ?? (matchesActive ? workouts.active : nil))?.setIDs ?? [])
        return workouts.logs.filter { ids.contains($0.id) }
    }
    private var exercise: TrainingExercise? {
        session.exercises.indices.contains(exerciseIndex) ? session.exercises[exerciseIndex] : nil
    }
    private var allSetsCompleted: Bool {
        !session.exercises.isEmpty && session.exercises.allSatisfy {
            count(for: $0.id) >= $0.sets
        }
    }
    private var readyToStart: Bool {
        !session.exercises.isEmpty && session.exercises.allSatisfy {
            validWeight(weights[$0.id] ?? "") != nil
        }
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: MugeStyle.Space.section) {
                if let completed {
                    completion(completed)
                } else if matchesActive {
                    workout
                } else if workouts.active != nil {
                    MugeSectionTitle(title: "진행 중인 운동이 있어요", subtitle: "홈에서 이어 하거나 종료한 뒤 새 운동을 시작해주세요.")
                    Button("돌아가기") { dismiss() }.buttonStyle(MugePrimaryButtonStyle())
                } else {
                    preparation
                }
                if let error {
                    Text(error).font(.footnote).foregroundStyle(.red)
                        .accessibilityLabel("저장 오류. \(error)")
                }
            }
            .padding(MugeStyle.Space.page)
        }
        .background(MugeStyle.canvas)
        .navigationTitle(completed != nil ? "운동 마무리" : "오늘의 운동")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar(matchesActive && completed == nil ? .hidden : .automatic, for: .tabBar)
        .safeAreaInset(edge: .bottom, spacing: 0) {
            if matchesActive && completed == nil, let exercise {
                VStack(spacing: MugeStyle.Space.sm) {
                    if count(for: exercise.id) < exercise.sets {
                        Button("세트 완료 · 휴식하기") { saveSet(exercise) }
                            .buttonStyle(MugePrimaryButtonStyle())
                            .disabled(validWeight(weights[exercise.id] ?? "") == nil
                                      || !(1...100).contains(Int(repetitions) ?? 0))
                    } else if allSetsCompleted {
                        Button("오늘 운동 마무리") { finish(early: false) }
                            .buttonStyle(MugePrimaryButtonStyle())
                    } else {
                        Button("다음 운동으로") { moveToNextExercise() }
                            .buttonStyle(MugePrimaryButtonStyle())
                    }
                }
                .padding(MugeStyle.Space.page)
                .background(.regularMaterial)
            }
        }
        .onAppear(perform: prepare)
        .sheet(item: $editingSet) { EditSetSheet(set: $0) }
        .fullScreenCover(isPresented: $showRest) {
            WorkoutRestScreen(exerciseName: exercise.map { localName($0) } ?? "다음 운동")
                .environmentObject(workouts)
                .interactiveDismissDisabled()
        }
        .confirmationDialog("오늘 운동을 여기서 마칠까요?", isPresented: $showStop, titleVisibility: .visible) {
            Button("기록을 남기고 종료", role: .destructive) { finish(early: true) }
            Button("계속 운동하기", role: .cancel) {}
        } message: {
            Text("완료한 세트는 보존됩니다. 통증이나 어지러움이 있다면 운동을 멈추고 안전한 곳에서 쉬세요.")
        }
    }

    private var preparation: some View {
        VStack(alignment: .leading, spacing: MugeStyle.Space.page) {
            MugeAdaptiveRow {
                MugeSectionTitle(title: "오늘 들 무게를 정해요", subtitle: "각 운동의 시작 중량을 확인해주세요.")
                Spacer()
                LilaRiveView(size: 78)
            }
            if item.status == "DEMO_ONLY" {
                Text("체험 루틴 · 전체 구성이 논문으로 검증된 프로그램은 아니에요.")
                    .font(.footnote).foregroundStyle(MugeStyle.muted)
            }
            ForEach(session.exercises) { movement in
                MugeCard {
                    Text(localName(movement)).font(MugeStyle.TypeStyle.card)
                    Text("\(movement.sets)세트 · \(movement.reps)회 · 휴식 \(movement.restSeconds)초")
                        .font(.subheadline).foregroundStyle(MugeStyle.muted)
                    HStack {
                        Text("시작 중량")
                        Spacer()
                        TextField("직접 입력", text: weightBinding(movement.id))
                            .keyboardType(.decimalPad).multilineTextAlignment(.trailing)
                            .frame(minWidth: 80, maxWidth: 130)
                            .accessibilityLabel("\(localName(movement)) 시작 중량")
                        Text("킬로그램").font(.caption)
                    }
                    if latestMax(for: movement.id) != nil {
                        Text("최근 실제 최대 중량의 65%를 2.5킬로그램 단위로 내린 예시예요. 연구로 검증된 개인 처방이 아니므로 오늘 컨디션과 기구에 맞게 바꿔주세요.")
                            .font(.caption).foregroundStyle(MugeStyle.muted)
                    } else {
                        Text("이 운동의 최대 중량 기록이 없어요. 자세를 유지할 수 있는 가벼운 중량을 직접 입력해주세요.")
                            .font(.caption).foregroundStyle(MugeStyle.muted)
                    }
                }
            }
            Text("준비 운동을 마치고, 기구와 주변 공간을 확인하세요. 목표 횟수보다 안정적인 자세가 우선이에요.")
                .font(.subheadline).foregroundStyle(MugeStyle.muted)
            Button("이 중량으로 운동 시작") {
                guard readyToStart else { return }
                if workouts.start(protocolID: item.id, version: item.version, sessionID: session.id, title: session.title) {
                    exerciseIndex = 0
                    repetitions = String(session.exercises.first?.reps ?? 5)
                    error = nil
                } else { error = workouts.error ?? "운동을 시작하지 못했어요. 다시 확인해주세요." }
            }
            .buttonStyle(MugePrimaryButtonStyle()).disabled(!readyToStart)
        }
    }

    private var workout: some View {
        VStack(alignment: .leading, spacing: MugeStyle.Space.page) {
            HStack {
                Text("\(activeRecords.count) / \(session.exercises.reduce(0) { $0 + $1.sets })세트")
                    .font(.subheadline.bold())
                Spacer()
                Button("운동 종료") { showStop = true }
                    .frame(minHeight: MugeStyle.minimumTarget).foregroundStyle(MugeStyle.muted)
            }
            ProgressView(value: Double(activeRecords.count),
                         total: Double(max(1, session.exercises.reduce(0) { $0 + $1.sets })))
                .tint(MugeStyle.ink)
            if let exercise {
                MugeSectionTitle(title: localName(exercise),
                                 subtitle: "\(exerciseIndex + 1)번째 운동 · 목표 \(exercise.reps)회")
                MugeCard {
                    Text(count(for: exercise.id) >= exercise.sets
                         ? "이 운동의 세트를 마쳤어요"
                         : "\(count(for: exercise.id) + 1)번째 세트")
                        .font(MugeStyle.TypeStyle.card)
                    MugeAdaptiveRow(spacing: MugeStyle.Space.lg) {
                        VStack(alignment: .leading) {
                            Text("중량 · 킬로그램").font(.caption).foregroundStyle(MugeStyle.muted)
                            TextField("중량", text: weightBinding(exercise.id))
                                .keyboardType(.decimalPad).mugeNumber(size: 38)
                                .accessibilityLabel("이번 세트 중량, 킬로그램")
                        }
                        VStack(alignment: .leading) {
                            Text("반복 · 회").font(.caption).foregroundStyle(MugeStyle.muted)
                            TextField("횟수", text: $repetitions)
                                .keyboardType(.numberPad).mugeNumber(size: 38)
                                .accessibilityLabel("이번 세트 반복 횟수")
                        }
                    }
                }
                let records = activeRecords.filter { $0.exerciseID == exercise.id }
                if !records.isEmpty {
                    MugeCard {
                        Text("오늘 입력한 기록").font(.headline)
                        ForEach(Array(records.enumerated()), id: \.element.id) { index, record in
                            Button { editingSet = record } label: {
                                HStack {
                                    Text("\(index + 1)세트")
                                    Spacer()
                                    Text("\(number(record.weightKg))킬로그램 × \(record.reps)회")
                                    Image(systemName: "pencil").font(.caption)
                                }
                                .foregroundStyle(MugeStyle.ink).frame(minHeight: MugeStyle.minimumTarget).contentShape(Rectangle())
                            }
                            .buttonStyle(.plain)
                        }
                        Text("기록을 누르면 수정할 수 있어요.").font(.caption).foregroundStyle(MugeStyle.muted)
                    }
                }
                if workouts.active?.restUntil != nil || workouts.active?.restPausedRemaining != nil {
                    Button("휴식 화면 열기") { showRest = true }.frame(maxWidth: .infinity)
                }
                Text("통증이나 어지러움이 느껴지면 즉시 중단하세요.")
                    .font(.footnote).foregroundStyle(MugeStyle.muted)
            }
        }
    }

    private func completion(_ finished: ActiveWorkout) -> some View {
        VStack(alignment: .leading, spacing: MugeStyle.Space.section) {
            MugeAdaptiveRow {
                MugeSectionTitle(title: stoppedEarly ? "오늘은 여기까지" : "오늘도 해냈어요",
                                 subtitle: "완료한 기록을 안전하게 저장했어요.")
                Spacer()
                LilaRiveView(size: 96)
            }
            MugeCard {
                MugeAdaptiveRow {
                    metric("\(activeRecords.count)", label: "완료 세트")
                    Spacer()
                    metric(number(StrengthMetrics.volume(activeRecords)), label: "누적 중량 · 킬로그램")
                    Spacer()
                    metric("\(max(0, Int((finished.finishedAt ?? Date()).timeIntervalSince(finished.startedAt) / 60)))", label: "운동 시간 · 분")
                }
            }
            ForEach(session.exercises) { movement in
                let records = activeRecords.filter { $0.exerciseID == movement.id }
                if !records.isEmpty {
                    MugeCard {
                        Text(localName(movement)).font(.headline)
                        ForEach(records) { record in
                            HStack {
                                Text("\(number(record.weightKg))킬로그램 × \(record.reps)회")
                                Spacer()
                            }.font(.subheadline)
                        }
                    }
                }
            }
            Button("운동 화면 닫기") { dismiss() }.buttonStyle(MugePrimaryButtonStyle())
        }
    }

    private func metric(_ value: String, label: String) -> some View {
        VStack(alignment: .leading, spacing: 5) {
            Text(value).font(MugeStyle.TypeStyle.section).monospacedDigit()
            Text(label).font(.caption2).foregroundStyle(MugeStyle.muted)
        }
    }
    private func prepare() {
        guard !prepared else { return }
        prepared = true
        for movement in session.exercises {
            let recent = activeRecords.last { $0.exerciseID == movement.id }
            if let recent {
                weights[movement.id] = number(recent.weightKg)
            } else if let measured = latestMax(for: movement.id) {
                let proposed = floor(measured.weightKg * 0.65 / 2.5) * 2.5
                weights[movement.id] = proposed > 0 ? number(proposed) : ""
            } else { weights[movement.id] = "" }
        }
        if matchesActive {
            exerciseIndex = session.exercises.firstIndex { count(for: $0.id) < $0.sets }
                ?? max(0, session.exercises.count - 1)
            showRest = workouts.active?.restUntil != nil || workouts.active?.restPausedRemaining != nil
        }
        repetitions = String(exercise?.reps ?? 5)
    }
    private func latestMax(for id: String) -> MeasuredMax? {
        workouts.measuredMaxes.filter { $0.exerciseID == id }.max { $0.measuredAt < $1.measuredAt }
    }
    private func count(for id: String) -> Int { activeRecords.filter { $0.exerciseID == id }.count }
    private func weightBinding(_ id: String) -> Binding<String> {
        Binding(get: { weights[id] ?? "" }, set: { weights[id] = $0 })
    }
    private func validWeight(_ value: String) -> Double? {
        guard let result = Double(value.replacingOccurrences(of: ",", with: ".")),
              result.isFinite, (0...2000).contains(result) else { return nil }
        return result
    }
    private func saveSet(_ exercise: TrainingExercise) {
        guard matchesActive, count(for: exercise.id) < exercise.sets,
              let weight = validWeight(weights[exercise.id] ?? ""),
              let reps = Int(repetitions), (1...100).contains(reps) else { return }
        if workouts.completeSet(exerciseID: exercise.id, weightKg: weight, reps: reps,
                                protocolID: item.id, version: item.version, sessionID: session.id,
                                restSeconds: exercise.restSeconds) != nil {
            error = nil
            showRest = true
        } else { error = workouts.error ?? "세트를 저장하지 못했어요. 기록을 확인한 뒤 다시 시도해주세요." }
    }
    private func moveToNextExercise() {
        guard let next = session.exercises.firstIndex(where: { count(for: $0.id) < $0.sets }) else { return }
        exerciseIndex = next
        repetitions = String(session.exercises[next].reps)
    }
    private func finish(early: Bool) {
        guard matchesActive, let active = workouts.active else { return }
        if workouts.finish() {
            completed = workouts.history.first { $0.id == active.id }
            stoppedEarly = early
            error = nil
        } else { error = workouts.error ?? "운동 종료를 저장하지 못했어요. 다시 시도해주세요." }
    }
    private func number(_ value: Double) -> String { String(format: "%g", value) }
    private func localName(_ exercise: TrainingExercise) -> String {
        switch exercise.id {
        case "squat": return "스쿼트"
        case "bench": return "벤치프레스"
        case "deadlift": return "데드리프트"
        default: return exercise.name
        }
    }
}

/// A deadline, rather than a decrementing counter, survives app backgrounding.
private struct WorkoutRestScreen: View {
    let exerciseName: String
    @EnvironmentObject private var workouts: WorkoutStore
    @Environment(\.dismiss) private var dismiss
    @State private var error: String?
    private var paused: Bool { workouts.active?.restPausedRemaining != nil }

    var body: some View {
        TimelineView(.periodic(from: .now, by: 1)) { context in
            let remaining = max(0, workouts.active?.restPausedRemaining
                                ?? workouts.active?.restUntil?.timeIntervalSince(context.date) ?? 0)
            let seconds = Int(ceil(remaining))
            GeometryReader { geometry in
                ScrollView {
                    VStack(spacing: MugeStyle.Space.section) {
                Spacer(minLength: MugeStyle.Space.lg)
                Text(paused ? "휴식을 잠시 멈췄어요" : seconds > 0 ? "지금은 회복할 시간" : "다음 세트 준비됐나요?")
                    .font(MugeStyle.TypeStyle.section)
                Text(exerciseName).font(.subheadline).foregroundStyle(MugeStyle.muted)
                Text(String(format: "%02d:%02d", seconds / 60, seconds % 60))
                    .mugeNumber(size: 82)
                    .monospacedDigit().minimumScaleFactor(0.5).lineLimit(1)
                    .accessibilityLabel("남은 휴식 \(seconds / 60)분 \(seconds % 60)초")
                Text("호흡을 고르고, 준비가 되면 이어가세요.")
                    .font(.subheadline).foregroundStyle(MugeStyle.muted)
                HStack(spacing: 16) {
                    Button("+10초") { perform { workouts.adjustRest(by: 10) } }
                    Button("+1분") { perform { workouts.adjustRest(by: 60) } }
                }
                .buttonStyle(MugeSecondaryButtonStyle())
                Button(paused ? "휴식 다시 시작" : "잠시 멈춤") {
                    perform { paused ? workouts.resumeRest() : workouts.pauseRest() }
                }
                .buttonStyle(MugeSecondaryButtonStyle())
                .disabled(!paused && seconds == 0)
                Spacer(minLength: MugeStyle.Space.lg)
                if let error { Text(error).font(.footnote).foregroundStyle(.red) }
                Button(seconds > 0 ? "휴식 마치고 돌아가기" : "운동으로 돌아가기") {
                    if workouts.endRest() { dismiss() }
                    else { error = workouts.error ?? "휴식 종료를 저장하지 못했어요." }
                }.buttonStyle(MugePrimaryButtonStyle())
            }
                    .padding(MugeStyle.Space.page)
                    .frame(maxWidth: .infinity)
                    .frame(minHeight: geometry.size.height)
                }
                .background(MugeStyle.canvas).foregroundStyle(MugeStyle.ink)
            }
        }
    }
    private func perform(_ action: () -> Bool) {
        if action() { error = nil }
        else { error = workouts.error ?? "휴식 시간을 저장하지 못했어요. 다시 시도해주세요." }
    }
}
