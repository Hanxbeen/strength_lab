import SwiftUI
import UniformTypeIdentifiers

struct EditSetSheet: View {
    @AppStorage("displayUnit") private var unit: MassUnit = .kg
    let set: LoggedSet
    @EnvironmentObject private var workouts: WorkoutStore
    @Environment(\.dismiss) private var dismiss
    @State private var weight = ""
    @State private var reps = ""
    @State private var showError = false
    @State private var editedWeight = false
    @State private var loaded = false
    private var canonicalWeight: Double? {
        editedWeight ? unit.parse(weight, allowsZero: true) : set.weightKg
    }

    var body: some View {
        NavigationStack {
            Form {
                MugeMassInput(title: "중량", text: Binding(get: { weight }, set: {
                    weight = $0; editedWeight = true
                }), unit: unit, allowsZero: true)
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
                        guard let kg = canonicalWeight,
                              let count = Int(reps),
                              workouts.updateSet(id: set.id, weightKg: kg, reps: count) else {
                            showError = true
                            return
                        }
                        dismiss()
                    }.disabled(canonicalWeight == nil || !(0...100).contains(Int(reps) ?? -1))
                }
            }
            .onAppear {
                guard !loaded else { return }
                loaded = true
                weight = unit.input(set.weightKg)
                reps = String(set.reps)
            }
        }
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
                Text("백업은 직접 보관하는 기록 파일입니다. 자동 클라우드 동기화는 아직 제공하지 않습니다.")
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
            Text("이 작업은 현재 세트, 세션, 실제 최대 중량 기록을 모두 교체합니다.")
        }
    }
}
