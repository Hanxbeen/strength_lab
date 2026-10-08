import SwiftUI
import Charts
import UniformTypeIdentifiers

struct HomeView: View {
    @EnvironmentObject private var catalog: CatalogStore
    @EnvironmentObject private var workouts: WorkoutStore

    var body: some View {
        TabView {
            NavigationStack {
                ScrollView {
                    VStack(alignment: .leading, spacing: 26) {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("STRENGTH, WITH EVIDENCE")
                                .font(.caption.weight(.semibold))
                                .tracking(2)
                                .foregroundStyle(MugeStyle.accent)
                            Text("오늘의 무게를,\n내일의 근거로.")
                                .font(.system(size: 36, weight: .bold, design: .rounded))
                                .tracking(-1.4)
                                .foregroundStyle(MugeStyle.ink)
                                .fixedSize(horizontal: false, vertical: true)
                            Text("논문으로 고르고, 바벨로 검증한다.")
                                .font(.subheadline)
                                .foregroundStyle(MugeStyle.muted)
                        }
                        .padding(.top, 16)

                        if let active = workouts.active {
                            MugeCard {
                                Label("진행 중인 운동", systemImage: "figure.strengthtraining.traditional")
                                    .font(.caption.weight(.semibold))
                                    .foregroundStyle(MugeStyle.accent)
                                Text(active.title)
                                    .font(.title2.bold())
                                    .foregroundStyle(MugeStyle.ink)
                                Text("\\(active.setIDs.count)세트 기록 · \\(active.startedAt.formatted(date: .omitted, time: .shortened)) 시작")
                                    .font(.subheadline).foregroundStyle(MugeStyle.muted)
                                HStack {
                                    MugePrimaryButton(title: "세션 완료") { _ = workouts.finish() }
                                    Button("폐기") { _ = workouts.discard() }
                                        .font(.subheadline)
                                        .foregroundStyle(.red)
                                        .padding()
                                }
                            }
                        }

                        MugeSectionTitle(title: "연구 기반 루틴", subtitle: "검증된 처방만 이곳에 게시됩니다.")
                        if catalog.protocols.isEmpty {
                            MugeCard {
                                Image(systemName: "text.book.closed")
                                    .font(.title)
                                    .foregroundStyle(MugeStyle.accent)
                                Text("아직 게시된 연구 루틴이 없어요")
                                    .font(.headline).foregroundStyle(MugeStyle.ink)
                                Text("근거 검증이 완료되면 여기에 표시됩니다. 검증되지 않은 루틴을 연구 결과로 소개하지 않습니다.")
                                    .font(.subheadline).foregroundStyle(MugeStyle.muted)
                            }
                        } else {
                            ForEach(catalog.protocols) { item in
                                NavigationLink {
                                    ProtocolView(item: item, isDemo: false)
                                } label: {
                                    MugeCard {
                                        Label("검증된 연구 프로토콜", systemImage: "checkmark.seal")
                                            .font(.caption).foregroundStyle(MugeStyle.accent)
                                        Text(item.title).font(.headline).foregroundStyle(MugeStyle.ink)
                                        Image(systemName: "arrow.up.right")
                                            .foregroundStyle(MugeStyle.accent)
                                    }
                                }
                                .buttonStyle(.plain)
                            }
                        }

                        MugeSectionTitle(title: "먼저 기록해보기", subtitle: "연구 처방이 아닌 기능 체험용 루틴입니다.")
                        ForEach(catalog.demo) { item in
                            NavigationLink {
                                ProtocolView(item: item, isDemo: true)
                            } label: {
                                MugeCard {
                                    HStack {
                                        VStack(alignment: .leading, spacing: 8) {
                                            Text("DEMO · RECORDING ONLY")
                                                .font(.caption2.bold()).tracking(1)
                                                .foregroundStyle(MugeStyle.accent)
                                            Text(item.title).font(.title3.bold()).foregroundStyle(MugeStyle.ink)
                                            Text("스쿼트 · 벤치프레스 · 데드리프트")
                                                .font(.subheadline).foregroundStyle(MugeStyle.muted)
                                        }
                                        Spacer()
                                        Image(systemName: "arrow.up.right")
                                            .foregroundStyle(MugeStyle.accent)
                                    }
                                }
                            }
                            .buttonStyle(.plain)
                        }
                        if let error = catalog.error {
                            Text(error).font(.caption).foregroundStyle(MugeStyle.muted)
                        }
                    }
                    .padding(20)
                }
                .background(MugeStyle.canvas)
                .navigationTitle("무게무게")
                .navigationBarTitleDisplayMode(.inline)
                .refreshable { await catalog.refresh() }
            }
            .tabItem { Label("루틴", systemImage: "dumbbell") }

            NavigationStack {
                StrengthDashboard()
                    .navigationTitle("성장 기록")
            }
            .tabItem { Label("성장", systemImage: "chart.xyaxis.line") }

            NavigationStack {
                BackupView()
                    .navigationTitle("데이터 관리")
            }
            .tabItem { Label("데이터", systemImage: "externaldrive") }
        }
        .tint(MugeStyle.accent)
        .task { await catalog.refresh() }
    }
}

struct ProtocolView: View {
    let item: TrainingProtocol
    let isDemo: Bool
    @EnvironmentObject private var workouts: WorkoutStore
    var body: some View {
        List {
            if isDemo {
                Label("기록 기능 체험 · 검증된 운동 처방이 아닙니다", systemImage: "exclamationmark.triangle")
                    .foregroundStyle(.orange)
            }
            Text(item.description)
            ForEach(item.sessions) { session in
                Section(session.title) {
                    if workouts.active == nil {
                        Button("이 세션 시작") {
                            _ = workouts.start(protocolID: item.id, version: item.version,
                                               sessionID: session.id, title: session.title)
                        }
                    } else if workouts.active?.sessionID == session.id &&
                                workouts.active?.protocolID == item.id &&
                                workouts.active?.protocolVersion == item.version {
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
    @State private var weight = "20"
    @State private var reps = "5"
    @State private var editingSet: LoggedSet?
    @State private var isSaving = false
    private var isCurrentSession: Bool {
        workouts.active?.protocolID == protocolID &&
        workouts.active?.protocolVersion == protocolVersion &&
        workouts.active?.sessionID == sessionID
    }

    private var records: [LoggedSet] { workouts.records(for: exercise.id) }

    private var currentSessionSetCount: Int {
        guard let active = workouts.active, isCurrentSession else { return 0 }
        let sessionIDs = Set(active.setIDs)
        return records.filter { sessionIDs.contains($0.id) }.count
    }

    private var parsedWeight: Double? {
        Double(weight.replacingOccurrences(of: ",", with: "."))
    }
    private var canSave: Bool {
        guard let kg = parsedWeight, let count = Int(reps) else { return false }
        return isCurrentSession && !isSaving && kg.isFinite &&
            (0...2000).contains(kg) && (1...100).contains(count)
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 22) {
                VStack(alignment: .leading, spacing: 6) {
                    Text("TRAINING LOG")
                        .font(.caption.weight(.semibold)).tracking(2)
                        .foregroundStyle(MugeStyle.accent)
                    Text(exercise.name)
                        .font(.system(size: 32, weight: .bold, design: .rounded))
                        .foregroundStyle(MugeStyle.ink)
                    Text("\(exercise.sets)세트 · 목표 \(exercise.reps)회 · 휴식 \(exercise.restSeconds)초")
                        .font(.subheadline).foregroundStyle(MugeStyle.muted)
                }
                MugeCard {
                    HStack {
                        Label("오늘의 세트", systemImage: "checkmark.circle")
                            .font(.subheadline.weight(.semibold))
                        Spacer()
                        Text("\(currentSessionSetCount) / \(exercise.sets)")
                            .font(.title3.bold().monospacedDigit())
                            .foregroundStyle(MugeStyle.accent)
                    }
                    ProgressView(value: Double(min(currentSessionSetCount, exercise.sets)),
                                 total: Double(max(exercise.sets, 1)))
                        .tint(MugeStyle.accent)
                    if !isCurrentSession {
                        Label("먼저 루틴에서 이 세션을 시작해주세요.", systemImage: "info.circle")
                            .font(.caption).foregroundStyle(MugeStyle.muted)
                    }
                }
                MugeCard {
                    Text("다음 세트 기록")
                        .font(.headline).foregroundStyle(MugeStyle.ink)
                    HStack(spacing: 16) {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("중량 · kg").font(.caption).foregroundStyle(MugeStyle.muted)
                            TextField("20", text: $weight)
                                .keyboardType(.decimalPad)
                                .font(.system(size: 30, weight: .bold, design: .rounded))
                                .accessibilityLabel("중량 킬로그램")
                        }
                        Divider()
                        VStack(alignment: .leading, spacing: 8) {
                            Text("반복 · 회").font(.caption).foregroundStyle(MugeStyle.muted)
                            TextField("5", text: $reps)
                                .keyboardType(.numberPad)
                                .font(.system(size: 30, weight: .bold, design: .rounded))
                                .accessibilityLabel("반복 횟수")
                        }
                    }
                    .frame(height: 88)
                    MugePrimaryButton(title: isSaving ? "저장 중" : "세트 완료") {
                        guard canSave, let kg = parsedWeight, let count = Int(reps) else { return }
                        isSaving = true
                        defer { isSaving = false }
                        _ = workouts.completeSet(exerciseID: exercise.id, weightKg: kg, reps: count,
                                                 protocolID: protocolID, version: protocolVersion,
                                                 sessionID: sessionID, restSeconds: exercise.restSeconds)
                    }
                    .disabled(!canSave)
                    .opacity(canSave ? 1 : 0.45)
                    Text("세트와 진행 상태를 기기에 함께 저장합니다.")
                        .font(.caption).foregroundStyle(MugeStyle.muted)
                    if let error = workouts.lastError {
                        Label(error, systemImage: "exclamationmark.triangle")
                            .font(.caption).foregroundStyle(.red)
                    }
                }
                if isCurrentSession, let until = workouts.active?.restUntil {
                    NativeGlassPanel {
                        HStack {
                            VStack(alignment: .leading, spacing: 6) {
                                Label("세트 간 휴식", systemImage: "timer")
                                    .font(.subheadline.weight(.semibold))
                                Text("종료 시각은 앱을 닫아도 유지돼요.")
                                    .font(.caption).foregroundStyle(MugeStyle.muted)
                            }
                            Spacer()
                            TimelineView(.periodic(from: .now, by: 1)) { timeline in
                                Text("\(max(0, Int(ceil(until.timeIntervalSince(timeline.date)))))초")
                                    .font(.title2.bold().monospacedDigit())
                                    .foregroundStyle(MugeStyle.accent)
                            }
                        }
                    }
                }
                MugeSectionTitle(title: "기록한 세트", subtitle: "항목을 누르면 중량과 반복을 수정할 수 있어요.")
                if records.isEmpty {
                    MugeCard {
                        Text("아직 기록한 세트가 없어요.")
                            .foregroundStyle(MugeStyle.muted)
                    }
                } else {
                    ForEach(records.reversed()) { set in
                        MugeCard {
                            HStack {
                                VStack(alignment: .leading, spacing: 5) {
                                    Text("\(set.weightKg.formatted()) kg × \(set.reps)회")
                                        .font(.title3.bold()).foregroundStyle(MugeStyle.ink)
                                    Text(set.performedAt.formatted(date: .abbreviated, time: .shortened))
                                        .font(.caption).foregroundStyle(MugeStyle.muted)
                                }
                                Spacer()
                                Button {
                                    editingSet = set
                                } label: {
                                    Label("수정", systemImage: "pencil")
                                }
                                .font(.subheadline)
                                .accessibilityLabel("세트 수정")
                            }
                        }
                    }
                }
            }
            .padding(20)
        }
        .background(MugeStyle.canvas)
        .navigationTitle(exercise.name)
        .navigationBarTitleDisplayMode(.inline)
        .sheet(item: $editingSet) { set in
            EditSetSheet(set: set)
                .environmentObject(workouts)
        }
    }
}

struct EditSetSheet: View {
    let set: LoggedSet
    @EnvironmentObject private var workouts: WorkoutStore
    @Environment(\.dismiss) private var dismiss
    @State private var weight = ""
    @State private var reps = ""
    @State private var showError = false

    var body: some View {
        NavigationStack {
            Form {
                TextField("중량 (kg)", text: $weight).keyboardType(.decimalPad)
                TextField("반복 횟수", text: $reps).keyboardType(.numberPad)
                if showError {
                    Text("중량 또는 반복 횟수를 확인해주세요.")
                        .foregroundStyle(.red)
                }
            }
            .navigationTitle("세트 수정")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("취소") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("저장") {
                        guard let kg = Double(weight.replacingOccurrences(of: ",", with: ".")),
                              let count = Int(reps),
                              workouts.updateSet(id: set.id, weightKg: kg, reps: count) else {
                            showError = true
                            return
                        }
                        dismiss()
                    }
                }
            }
            .onAppear {
                weight = set.weightKg.formatted()
                reps = String(set.reps)
            }
        }
    }
}

struct StrengthDashboard: View {
    @EnvironmentObject private var workouts: WorkoutStore
    @State private var actualWeight = ""
    @State private var selected = "squat"
    private let exercises = [("squat", "Squat"), ("bench", "Bench"), ("deadlift", "Deadlift")]

    private var records: [LoggedSet] { workouts.records(for: selected) }
    private var estimates: [LoggedSet] {
        records.filter { StrengthMetrics.estimatedOneRepMax(weightKg: $0.weightKg, reps: $0.reps) != nil }
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 22) {
                MugeSectionTitle(title: "쌓이는 기록, 보이는 성장", subtitle: "실제 측정과 공식 기반 추정치를 구분해요.")
                    .padding(.top, 12)
                Picker("운동", selection: $selected) {
                    ForEach(exercises, id: \.0) { item in
                        Text(item.1).tag(item.0)
                    }
                }
                .pickerStyle(.segmented)

                MugeCard {
                    Text("추정 1RM · e1RM")
                        .font(.subheadline.weight(.semibold))
                        .foregroundStyle(MugeStyle.muted)
                    if let best = StrengthMetrics.bestEstimatedOneRepMax(records) {
                        HStack(alignment: .firstTextBaseline, spacing: 7) {
                            Text(best, format: .number.precision(.fractionLength(1)))
                                .font(.system(size: 44, weight: .bold, design: .rounded))
                                .monospacedDigit()
                            Text("kg").font(.title3.weight(.medium))
                        }
                        .foregroundStyle(MugeStyle.ink)
                    } else {
                        Text("아직 기록이 없어요")
                            .font(.title2.bold()).foregroundStyle(MugeStyle.ink)
                    }
                    Text("Epley 공식 · 1~10회 세트 기록 기준. 실제 측정한 1RM이 아닙니다.")
                        .font(.caption).foregroundStyle(MugeStyle.muted)
                }
                MugeCard {
                    Text("추정 1RM 변화")
                        .font(.headline).foregroundStyle(MugeStyle.ink)
                    if estimates.isEmpty {
                        Text("세트를 기록하면 추정치의 변화를 볼 수 있어요.")
                            .font(.subheadline).foregroundStyle(MugeStyle.muted)
                    } else {
                        Chart(estimates) { set in
                            if let value = StrengthMetrics.estimatedOneRepMax(weightKg: set.weightKg, reps: set.reps) {
                                PointMark(x: .value("날짜", set.performedAt),
                                          y: .value("e1RM (kg)", value))
                                    .foregroundStyle(MugeStyle.accent)
                            }
                        }
                        .frame(height: 210)
                    }
                    Text("세트별 추정치이며 연구 결과나 직접 측정한 1RM이 아닙니다.")
                        .font(.caption).foregroundStyle(MugeStyle.muted)
                }
                MugeCard {
                    Text("누적 훈련량")
                        .font(.subheadline).foregroundStyle(MugeStyle.muted)
                    Text("\(StrengthMetrics.volume(records), specifier: "%.0f") kg")
                        .font(.title2.bold().monospacedDigit()).foregroundStyle(MugeStyle.ink)
                    Text("세트 중량 × 반복 횟수의 합")
                        .font(.caption).foregroundStyle(MugeStyle.muted)
                }
                MugeCard {
                    Text("직접 측정한 1RM")
                        .font(.headline).foregroundStyle(MugeStyle.ink)
                    Text("추정치와 별도로 보관해요.")
                        .font(.caption).foregroundStyle(MugeStyle.muted)
                    TextField("직접 측정한 1RM (kg)", text: $actualWeight)
                        .keyboardType(.decimalPad)
                        .textFieldStyle(.roundedBorder)
                    MugePrimaryButton(title: "실제 1RM 기록") {
                        if let weight = Double(actualWeight.replacingOccurrences(of: ",", with: ".")),
                           workouts.recordMeasuredMax(exerciseID: selected, weightKg: weight) {
                            actualWeight = ""
                        }
                    }
                    ForEach(workouts.measuredMaxes.filter { $0.exerciseID == selected }.reversed()) { entry in
                        HStack {
                            Text("\(entry.weightKg.formatted()) kg").fontWeight(.semibold)
                            Spacer()
                            Text(entry.measuredAt.formatted(date: .abbreviated, time: .omitted))
                                .font(.caption).foregroundStyle(MugeStyle.muted)
                        }
                    }
                    Text("직접 수행한 최대 중량만 입력하세요.")
                        .font(.caption).foregroundStyle(MugeStyle.muted)
                }
                MugeSectionTitle(title: "완료한 운동", subtitle: "운동별 세션 기록")
                if workouts.history.isEmpty {
                    MugeCard { Text("완료한 세션이 아직 없어요.").foregroundStyle(MugeStyle.muted) }
                } else {
                    ForEach(workouts.history.reversed()) { session in
                        MugeCard {
                            Text(session.title).font(.headline).foregroundStyle(MugeStyle.ink)
                            Text("\(session.setIDs.count)세트 · \(session.startedAt.formatted(date: .abbreviated, time: .shortened))")
                                .font(.caption).foregroundStyle(MugeStyle.muted)
                        }
                    }
                }
            }
            .padding(20)
        }
        .background(MugeStyle.canvas)
    }
}


struct BackupView: View {
    @EnvironmentObject private var workouts: WorkoutStore
    @State private var exportURL: URL?
    @State private var importing = false
    @State private var pendingBackup: Data?
    @State private var confirmRestore = false
    @State private var message: String?

    var body: some View {
        Form {
            Section("내 운동 기록") {
                Text("세트 \(workouts.logs.count)개 · 완료 세션 \(workouts.history.count)개")
                Text("백업은 직접 보관하는 JSON 파일입니다. 자동 클라우드 동기화는 아직 제공하지 않습니다.")
                    .font(.caption).foregroundStyle(.secondary)
            }
            Section("백업") {
                Button("백업 파일 준비") {
                    do {
                        let data = try workouts.exportBackup()
                        let folder = FileManager.default.temporaryDirectory
                        let url = folder.appendingPathComponent("mugemuge-backup-\(UUID().uuidString).json")
                        try data.write(to: url, options: .atomic)
                        exportURL = url
                        message = nil
                    } catch {
                        message = "백업 파일을 만들지 못했습니다."
                    }
                }
                if let exportURL {
                    ShareLink(item: exportURL) {
                        Label("백업 파일 공유 또는 파일 앱에 저장", systemImage: "square.and.arrow.up")
                    }
                }
                Button("백업 파일에서 복원") { importing = true }
            }
            Section {
                Text("복원하면 현재 운동 기록 전체가 백업 파일 내용으로 교체됩니다. 먼저 현재 데이터를 백업하세요.")
                    .font(.caption).foregroundStyle(.secondary)
                if let message {
                    Text(message).foregroundStyle(.secondary)
                }
            }
        }
        .fileImporter(isPresented: $importing, allowedContentTypes: [.json]) { result in
            switch result {
            case .success(let url):
                let accessed = url.startAccessingSecurityScopedResource()
                defer { if accessed { url.stopAccessingSecurityScopedResource() } }
                guard let data = try? Data(contentsOf: url) else {
                    message = "파일을 읽지 못했습니다."
                    return
                }
                pendingBackup = data
                confirmRestore = true
            case .failure:
                message = "파일을 선택하지 못했습니다."
            }
        }
        .confirmationDialog("기존 기록을 모두 교체할까요?", isPresented: $confirmRestore) {
            Button("백업으로 전체 복원", role: .destructive) {
                guard let pendingBackup else { return }
                message = workouts.importBackup(pendingBackup)
                    ? "복원이 완료됐습니다."
                    : (workouts.lastError ?? "복원하지 못했습니다.")
                self.pendingBackup = nil
            }
            Button("취소", role: .cancel) { pendingBackup = nil }
        } message: {
            Text("이 작업은 현재 세트, 세션, 실제 1RM 기록을 모두 교체합니다.")
        }
    }
}
