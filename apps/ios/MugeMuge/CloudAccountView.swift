import SwiftUI
import AuthenticationServices
import CryptoKit

struct CloudAccountView: View {
    @EnvironmentObject private var auth: CloudAuth
    @EnvironmentObject private var workouts: WorkoutStore
    @State private var remote: CloudSnapshot?
    @State private var remoteChecked = false
    @State private var message: String?
    @State private var busy = false
    @State private var showUploadConfirmation = false
    @State private var showRestoreConfirmation = false
    @State private var showUpdateConfirmation = false
    @State private var cloudRevision: Int64?
    @State private var syncedLocalDigest: Data?
    @State private var cloudOwner: UUID?
    @State private var inspectedAccount: UUID?
    private let ownerKey = "strength_lab.cloud.local_owner"
    private let revisionKey = "strength_lab.cloud.last_revision"
    private let digestKey = "strength_lab.cloud.last_digest"

    private func digest() throws -> Data {
        let data = try workouts.exportBackup()
        return Data(SHA256.hash(data: data))
    }
    private func storedOwner() -> UUID? {
        UserDefaults.standard.string(forKey: ownerKey).flatMap(UUID.init(uuidString:))
    }
    private func bindOwner(_ id: UUID, revision: Int64) throws {
        let value = try digest()
        UserDefaults.standard.set(id.uuidString, forKey: ownerKey)
        UserDefaults.standard.set(String(revision), forKey: revisionKey)
        UserDefaults.standard.set(value, forKey: digestKey)
        cloudOwner = id
        cloudRevision = revision
        syncedLocalDigest = value
    }
    private func refreshBinding() {
        cloudOwner = storedOwner()
        cloudRevision = UserDefaults.standard.string(forKey: revisionKey).flatMap(Int64.init)
        syncedLocalDigest = UserDefaults.standard.data(forKey: digestKey)
    }
    private var accountMismatch: Bool {
        guard let owner = storedOwner(), let id = auth.userID else { return false }
        return owner != id
    }
    private var hasPendingLocalChanges: Bool {
        guard let baseline = UserDefaults.standard.data(forKey: digestKey),
              let current = try? digest() else { return false }
        return baseline != current
    }

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
                        remoteChecked = false
                        inspectedAccount = nil
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

            cloudSection
            Section("기기 백업") {
                NavigationLink("JSON 백업 내보내기 · 복원") { BackupView() }
            }
            if let message {
                Section("동기화 상태") { Text(message).font(.subheadline) }
            }
        }
        .onAppear { refreshBinding() }
        .confirmationDialog("기기 기록을 최초 업로드할까요?", isPresented: $showUploadConfirmation) {
            Button("업로드") { Task { await firstUpload() } }
            Button("취소", role: .cancel) {}
        } message: {
            Text("서버에 기록이 이미 있다면 업로드가 거절됩니다. 서버 기록을 덮어쓰지 않습니다.")
        }
        .confirmationDialog("변경된 기기 기록을 업로드할까요?", isPresented: $showUpdateConfirmation) {
            Button("서버 버전 검사 후 업로드") { Task { await uploadChanges() } }
            Button("취소", role: .cancel) {}
        } message: {
            Text("마지막 동기화 이후 서버에 변경이 있으면 덮어쓰지 않고 중단합니다.")
        }
        .confirmationDialog("서버 기록을 이 기기로 가져올까요?", isPresented: $showRestoreConfirmation) {
            Button("빈 기기에 복원") { restoreToEmptyDevice() }
            Button("취소", role: .cancel) {}
        } message: {
            Text("현재 기기 기록이 비어 있을 때만 가져옵니다. 기존 데이터는 자동으로 덮어쓰지 않습니다.")
        }
    }

    @ViewBuilder
    private var cloudSection: some View {
            if auth.userID != nil {
                Section("클라우드 기록") {
                    if accountMismatch {
                        Text("이 기기의 기록은 다른 클라우드 계정에 연결되어 있습니다. 계정 간 자동 이동과 업로드를 차단했습니다.")
                            .foregroundStyle(.red)
                    }
                    Button("서버 기록 확인") { Task { await refreshRemote() } }
                        .disabled(busy)
                    if let remote {
                        Text("서버 버전: \\(remote.revision)")
                        Text("서버 세트 \\(remote.payload.logs.count)개 · 완료 세션 \\(remote.payload.history.count)개")
                        if localIsEmpty && !accountMismatch {
                            Button("서버 기록을 이 기기로 가져오기") {
                                showRestoreConfirmation = true
                            }
                        } else {
                            Text("기기에 기록이 있어 자동 복원을 차단했습니다. 먼저 JSON 백업을 보관하고 충돌을 해결해야 합니다.")
                                .font(.caption).foregroundStyle(.orange)
                        }
                    } else {
                        Text(remoteChecked ? "서버에 저장된 기록이 없습니다." : "서버 기록을 아직 확인하지 않았습니다.")
                            .font(.caption).foregroundStyle(.secondary)
                    }
                    Button("기기 기록을 클라우드에 최초 업로드") {
                        showUploadConfirmation = true
                    }
                    .disabled(busy || accountMismatch || inspectedAccount != auth.userID || !remoteChecked || remote != nil || localIsEmpty)
                    Text("최초 업로드는 서버에 기록이 없을 때만 가능합니다.")
                        .font(.caption).foregroundStyle(.secondary)
                }
                Section("기록 변경 업로드") {
                    if cloudOwner == auth.userID, cloudRevision != nil, hasPendingLocalChanges {
                        Button("변경된 기록 업로드 (서버 버전 확인)") {
                            showUpdateConfirmation = true
                        }
                        .disabled(busy || accountMismatch || inspectedAccount != auth.userID || !remoteChecked || remote == nil)
                        Text("서버가 다른 기기에서 변경됐다면 업로드하지 않고 충돌을 표시합니다.")
                            .font(.caption).foregroundStyle(.secondary)
                    }
                }
            }
    }

    private func refreshRemote() async {
        guard let id = auth.userID, !busy else { return }
        remoteChecked = false
        remote = nil
        inspectedAccount = nil
        busy = true
        defer { busy = false }
        do {
            let token = try await auth.accessToken()
            let fetched = try await transport.fetch(userID: id, accessToken: token)
            guard auth.userID == id else { return }
            remote = fetched
            inspectedAccount = id
            remoteChecked = true
            if let bound = cloudRevision, cloudOwner == id,
               let fetched, fetched.revision != bound {
                message = "서버 기록이 다른 기기에서 변경됐습니다. 자동 덮어쓰기를 차단했습니다."
                return
            }
            message = fetched == nil ? "서버에 저장된 기록이 없습니다." : "서버 기록을 확인했습니다."
        } catch {
            remoteChecked = false
            remote = nil
            inspectedAccount = nil
            message = error.localizedDescription
        }
    }

    private func firstUpload() async {
        guard let id = auth.userID, !busy, !accountMismatch,
              inspectedAccount == id, remoteChecked, remote == nil, !localIsEmpty else { return }
        busy = true
        defer { busy = false }
        do {
            let data = try workouts.exportBackup()
            let payload = try JSONDecoder().decode(CloudPayload.self, from: data)
            let token = try await auth.accessToken()
            // Fetch again to detect account changes and stale preview before creating.
            let existing = try await transport.fetch(userID: id, accessToken: token)
            guard auth.userID == id else { return }
            guard existing == nil else {
                remote = existing
                message = "서버에 이미 기록이 있습니다. 덮어쓰지 않았습니다."
                return
            }
            let revision = try await transport.save(payload, expectedRevision: nil, accessToken: token)
            guard auth.userID == id else { return }
            try bindOwner(id, revision: revision)
            remote = try await transport.fetch(userID: id, accessToken: token)
            remoteChecked = true
            message = "최초 업로드 완료. 이후 변경은 자동 동기화되지 않습니다."
        } catch {
            remoteChecked = false
            remote = nil
            message = error.localizedDescription
        }
    }

    private func uploadChanges() async {
        guard let id = auth.userID, !busy, !accountMismatch,
              inspectedAccount == id, cloudOwner == id, let revision = cloudRevision,
              remoteChecked, remote?.revision == revision, hasPendingLocalChanges else { return }
        busy = true
        defer { busy = false }
        do {
            let before = try workouts.exportBackup()
            let payload = try JSONDecoder().decode(CloudPayload.self, from: before)
            let token = try await auth.accessToken()
            let current = try await transport.fetch(userID: id, accessToken: token)
            guard auth.userID == id else { return }
            guard current?.revision == revision else {
                remote = current
                message = "서버 버전 충돌. 기기 기록은 그대로 유지했습니다."
                return
            }
            // The server performs an atomic compare-and-swap to prevent races.
            let nextRevision = try await transport.save(payload, expectedRevision: revision, accessToken: token)
            guard auth.userID == id else { return }
            // If edits occurred during upload, do not mark the newer local state as synced.
            let after = try workouts.exportBackup()
            if before == after {
                try bindOwner(id, revision: nextRevision)
            } else {
                cloudRevision = nextRevision
                UserDefaults.standard.set(String(nextRevision), forKey: revisionKey)
            }
            remote = try await transport.fetch(userID: id, accessToken: token)
            message = "변경사항 업로드 완료."
        } catch {
            message = error.localizedDescription
        }
    }

    private func restoreToEmptyDevice() {
        guard localIsEmpty, !accountMismatch, let id = auth.userID,
              inspectedAccount == id, let remote else { return }
        do {
            let data = try JSONEncoder().encode(remote.payload)
            if workouts.importBackup(data) {
                try bindOwner(id, revision: remote.revision)
                message = "서버 기록을 빈 기기로 가져왔습니다."
            } else {
                message = workouts.lastError ?? "복원 실패"
            }
        } catch {
            message = error.localizedDescription
        }
    }
}
