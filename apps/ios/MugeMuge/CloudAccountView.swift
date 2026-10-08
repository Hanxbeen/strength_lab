import SwiftUI
import AuthenticationServices

struct CloudAccountView: View {
    @EnvironmentObject private var auth: CloudAuth
    @EnvironmentObject private var workouts: WorkoutStore
    @State private var remote: CloudSnapshot?
    @State private var message: String?
    @State private var busy = false
    @State private var showUploadConfirmation = false
    @State private var showRestoreConfirmation = false

    private var transport: CloudTransport {
        CloudTransport(baseURL: CloudConfiguration.url, publishableKey: CloudConfiguration.publishableKey)
    }
    private var localIsEmpty: Bool {
        workouts.logs.isEmpty && workouts.active == nil &&
        workouts.history.isEmpty && workouts.measuredMaxes.isEmpty
    }

    var body: some View {
        Form {
            Section("계정") {
                if let id = auth.userID {
                    Label("Apple 계정으로 로그인됨", systemImage: "person.crop.circle.badge.checkmark")
                    Text("계정 ID: \\(id.uuidString.prefix(8))…")
                        .font(.caption).foregroundStyle(.secondary)
                    Button("로그아웃 (기기 기록은 유지)") {
                        remote = nil
                        auth.signOut()
                        message = "로그아웃했습니다. 기기 기록은 그대로 남아 있습니다."
                    }
                } else {
                    SignInWithAppleButton(.signIn, onRequest: auth.makeAppleRequest) { result in
                        Task { await auth.finishAppleSignIn(result) }
                    }
                    .frame(height: 50)
                    Text("로그인만으로 기록을 업로드하지 않습니다.")
                        .font(.caption).foregroundStyle(.secondary)
                }
                if let error = auth.error { Text(error).foregroundStyle(.red) }
            }

            if auth.userID != nil {
                Section("클라우드 기록") {
                    Button("서버 기록 확인") { Task { await refreshRemote() } }
                        .disabled(busy)
                    if let remote {
                        Text("서버 버전: \\(remote.revision)")
                        Text("서버 세트 \\(remote.payload.logs.count)개 · 완료 세션 \\(remote.payload.history.count)개")
                        if localIsEmpty {
                            Button("서버 기록을 이 기기로 가져오기") {
                                showRestoreConfirmation = true
                            }
                        } else {
                            Text("기기에 기록이 있어 자동 복원을 차단했습니다. 먼저 JSON 백업을 보관하고 충돌을 해결해야 합니다.")
                                .font(.caption).foregroundStyle(.orange)
                        }
                    } else {
                        Text("서버 기록이 없거나 아직 확인되지 않았습니다.")
                            .font(.caption).foregroundStyle(.secondary)
                    }
                    Button("기기 기록을 클라우드에 최초 업로드") {
                        showUploadConfirmation = true
                    }
                    .disabled(busy || remote != nil || localIsEmpty)
                    Text("최초 업로드만 지원합니다. 이미 서버에 기록이 있다면 덮어쓰지 않습니다.")
                        .font(.caption).foregroundStyle(.secondary)
                }
            }
            Section("기기 백업") {
                NavigationLink("JSON 백업 내보내기 · 복원") { BackupView() }
            }
            if let message {
                Section("동기화 상태") { Text(message).font(.subheadline) }
            }
        }
        .confirmationDialog("기기 기록을 최초 업로드할까요?", isPresented: $showUploadConfirmation) {
            Button("업로드") { Task { await firstUpload() } }
            Button("취소", role: .cancel) {}
        } message: {
            Text("서버에 기록이 이미 있다면 업로드가 거절됩니다. 서버 기록을 덮어쓰지 않습니다.")
        }
        .confirmationDialog("서버 기록을 이 기기로 가져올까요?", isPresented: $showRestoreConfirmation) {
            Button("빈 기기에 복원") { restoreToEmptyDevice() }
            Button("취소", role: .cancel) {}
        } message: {
            Text("현재 기기 기록이 비어 있을 때만 가져옵니다. 기존 데이터는 자동으로 덮어쓰지 않습니다.")
        }
    }

    private func refreshRemote() async {
        guard let id = auth.userID else { return }
        busy = true
        defer { busy = false }
        do {
            let token = try await auth.accessToken()
            remote = try await transport.fetch(userID: id, accessToken: token)
            message = remote == nil ? "서버에 저장된 기록이 없습니다." : "서버 기록을 확인했습니다."
        } catch {
            message = error.localizedDescription
        }
    }

    private func firstUpload() async {
        guard auth.userID != nil, !localIsEmpty else { return }
        busy = true
        defer { busy = false }
        do {
            let data = try workouts.exportBackup()
            let payload = try JSONDecoder().decode(CloudPayload.self, from: data)
            let token = try await auth.accessToken()
            _ = try await transport.save(payload, expectedRevision: nil, accessToken: token)
            message = "최초 업로드 완료. 이후 변경은 자동 동기화되지 않습니다."
            await refreshRemote()
        } catch {
            message = error.localizedDescription
        }
    }

    private func restoreToEmptyDevice() {
        guard localIsEmpty, let remote else { return }
        do {
            let data = try JSONEncoder().encode(remote.payload)
            message = workouts.importBackup(data)
                ? "서버 기록을 빈 기기로 가져왔습니다."
                : (workouts.lastError ?? "복원 실패")
        } catch {
            message = error.localizedDescription
        }
    }
}
