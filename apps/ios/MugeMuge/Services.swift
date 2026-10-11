import Foundation
import Combine

enum WorkoutStoreError: LocalizedError {
    case invalidSet
    case saveFailed
    var errorDescription: String? {
        switch self {
        case .invalidSet: return "중량과 반복 횟수를 확인해주세요."
        case .saveFailed: return "운동 기록 저장에 실패했습니다. 저장 공간을 확인해주세요."
        }
    }
}

/// One atomic on-disk snapshot is the transaction boundary for sets, sessions and measured maxes.
@MainActor
final class WorkoutStore: ObservableObject {
    @Published private(set) var logs: [LoggedSet] = []
    @Published private(set) var active: ActiveWorkout?
    @Published private(set) var history: [ActiveWorkout] = []
    @Published private(set) var measuredMaxes: [MeasuredMax] = []
    @Published private(set) var lastError: String?
    var error: String? { lastError }
    private var url: URL
    private var storageBlocked = false
    private var pendingSetToken: UUID?

    private struct Snapshot: Codable {
        var schemaVersion: Int = 1
        var logs: [LoggedSet]
        var active: ActiveWorkout?
        var history: [ActiveWorkout]
        var measuredMaxes: [MeasuredMax]
    }

    init(filename: String = "workout-database.json", directory: URL? = nil) {
        let folder = directory ?? FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
        try? FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
        url = folder.appendingPathComponent(filename)
        if FileManager.default.fileExists(atPath: url.path) {
            if let data = try? Data(contentsOf: url),
               let snapshot = try? JSONDecoder().decode(Snapshot.self, from: data),
               snapshot.schemaVersion == 1 {
                apply(snapshot)
            } else {
                storageBlocked = true
                lastError = "운동 데이터 파일을 읽지 못했습니다. 기존 파일을 보존했으며 새 기록을 차단합니다."
            }
        } else {
            // One-time migration from the two previous local JSON stores.
            let oldLogs = folder.appendingPathComponent("workout-logs.json")
            let oldState = folder.appendingPathComponent("training-state.json")
            if FileManager.default.fileExists(atPath: oldLogs.path) ||
               FileManager.default.fileExists(atPath: oldState.path) {
                struct LegacyState: Decodable {
                    let active: ActiveWorkout?
                    let history: [ActiveWorkout]
                    let measuredMaxes: [MeasuredMax]
                }
                let logsExist = FileManager.default.fileExists(atPath: oldLogs.path)
                let stateExists = FileManager.default.fileExists(atPath: oldState.path)
                let oldLogData = try? Data(contentsOf: oldLogs)
                let oldStateData = try? Data(contentsOf: oldState)
                let recoveredLogs = oldLogData.flatMap { try? JSONDecoder().decode([LoggedSet].self, from: $0) }
                let recoveredState = oldStateData.flatMap { try? JSONDecoder().decode(LegacyState.self, from: $0) }
                if (logsExist && recoveredLogs == nil) ||
                   (stateExists && recoveredState == nil) {
                    storageBlocked = true
                    lastError = "이전 기록 변환에 실패했습니다. 원본을 보존했으며 저장을 차단합니다."
                } else {
                    // Reconcile dangling set references from prior two-file writes.
                    let validIDs = Set((recoveredLogs ?? []).map(\.id))
                    var active = recoveredState?.active
                    if var existing = active {
                        existing.setIDs = existing.setIDs.filter { validIDs.contains($0) }
                        active = existing
                    }
                    let history = (recoveredState?.history ?? []).map { workout -> ActiveWorkout in
                        var fixed = workout
                        fixed.setIDs = fixed.setIDs.filter { validIDs.contains($0) }
                        return fixed
                    }
                    _ = persist(Snapshot(logs: recoveredLogs ?? [], active: active,
                                         history: history, measuredMaxes: recoveredState?.measuredMaxes ?? []))
                }
            }
        }
    }

    /// Account-specific local databases. The guest file is never moved or overwritten.
    /// A corrupt target file blocks switching and leaves the current database untouched.
    @discardableResult
    func switchAccount(_ userID: UUID?) -> Bool {
        let folder = url.deletingLastPathComponent()
        let filename = userID.map { "workout-account-\($0.uuidString.lowercased()).json" }
            ?? "workout-database.json"
        let destination = folder.appendingPathComponent(filename)
        if destination == url { return !storageBlocked }
        let next: Snapshot
        if FileManager.default.fileExists(atPath: destination.path) {
            guard let data = try? Data(contentsOf: destination),
                  let decoded = try? JSONDecoder().decode(Snapshot.self, from: data),
                  decoded.schemaVersion == 1, Self.isConsistent(decoded) else {
                // Fail closed: never display a prior account's records under the new login.
                url = destination
                storageBlocked = true
                apply(Snapshot(logs: [], active: nil, history: [], measuredMaxes: []))
                lastError = "계정 기록 파일이 손상되어 표시와 저장을 차단했습니다. 원본 파일은 보존했습니다."
                return false
            }
            next = decoded
        } else {
            next = Snapshot(logs: [], active: nil, history: [], measuredMaxes: [])
        }
        url = destination
        storageBlocked = false
        apply(next)
        lastError = nil
        return true
    }

    private var snapshot: Snapshot {
        Snapshot(logs: logs, active: active, history: history, measuredMaxes: measuredMaxes)
    }

    private func apply(_ next: Snapshot) {
        logs = next.logs
        active = next.active
        history = next.history
        measuredMaxes = next.measuredMaxes
    }

    @discardableResult
    private func persist(_ next: Snapshot) -> Bool {
        guard !storageBlocked else { return false }
        do {
            try JSONEncoder().encode(next).write(to: url, options: .atomic)
            apply(next)
            lastError = nil
            return true
        } catch {
            lastError = WorkoutStoreError.saveFailed.localizedDescription
            return false
        }
    }

    @discardableResult
    func append(exerciseID: String, weightKg: Double, reps: Int) -> UUID? {
        guard !exerciseID.isEmpty, weightKg >= 0, weightKg <= 2000,
              weightKg.isFinite, (1...100).contains(reps) else {
            lastError = WorkoutStoreError.invalidSet.localizedDescription
            return nil
        }
        let entry = LoggedSet(exerciseID: exerciseID, weightKg: weightKg, reps: reps)
        var next = snapshot
        next.logs.append(entry)
        return persist(next) ? entry.id : nil
    }

    /// A set and its session reference are committed together or not at all.
    /// Export a portable snapshot. Never export the mutable database file directly.
    func exportBackup() throws -> Data {
        guard !storageBlocked else { throw WorkoutStoreError.saveFailed }
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys]
        return try encoder.encode(snapshot)
    }

    /// Import is a full replacement; UI must ask for explicit confirmation.
    @discardableResult
    func importBackup(_ data: Data) -> Bool {
        guard !storageBlocked, data.count <= 20_000_000,
              let decoded = try? JSONDecoder().decode(Snapshot.self, from: data),
              decoded.schemaVersion == 1, Self.isConsistent(decoded) else {
            lastError = "백업 파일 형식 또는 데이터 무결성을 확인해주세요."
            return false
        }
        return persist(decoded)
    }

    private static func isConsistent(_ value: Snapshot) -> Bool {
        let ids = value.logs.map(\.id)
        guard Set(ids).count == ids.count,
              value.logs.allSatisfy({ !$0.exerciseID.isEmpty && $0.weightKg.isFinite &&
                  (0...2000).contains($0.weightKg) && (1...100).contains($0.reps) }),
              value.measuredMaxes.allSatisfy({ $0.weightKg.isFinite && (0...2000).contains($0.weightKg) }),
              value.history.allSatisfy({ $0.finishedAt != nil }) else { return false }
        let validIDs = Set(ids)
        let allWorkouts = value.history + (value.active.map { [$0] } ?? [])
        return allWorkouts.allSatisfy {
            $0.protocolVersion > 0 && !$0.protocolID.isEmpty &&
            ($0.restPausedRemaining.map { $0.isFinite && (0...3600).contains($0) } ?? true) &&
            !($0.restUntil != nil && $0.restPausedRemaining != nil) &&
            $0.setIDs.allSatisfy { validIDs.contains($0) }
        }
    }

    @discardableResult
    func completeSet(exerciseID: String, weightKg: Double, reps: Int,
                     protocolID: String, version: Int, sessionID: String,
                     restSeconds: Int, requestID: UUID = UUID()) -> UUID? {
        guard pendingSetToken == nil else { return nil }
        pendingSetToken = requestID
        defer { pendingSetToken = nil }
        guard var workout = active, workout.protocolID == protocolID,
              workout.protocolVersion == version, workout.sessionID == sessionID,
              !exerciseID.isEmpty, weightKg >= 0, weightKg <= 2000,
              weightKg.isFinite, (1...100).contains(reps),
              (0...3600).contains(restSeconds) else { return nil }
        let entry = LoggedSet(exerciseID: exerciseID, weightKg: weightKg, reps: reps)
        workout.setIDs.append(entry.id)
        workout.restUntil = restSeconds > 0 ? Date().addingTimeInterval(TimeInterval(restSeconds)) : nil
        workout.restPausedRemaining = nil
        var next = snapshot
        next.logs.append(entry)
        next.active = workout
        return persist(next) ? entry.id : nil
    }

    /// Persist timer transitions atomically; wall-clock deadlines survive suspension.
    @discardableResult
    func adjustRest(by seconds: TimeInterval) -> Bool {
        guard seconds.isFinite, (0...3600).contains(seconds), var workout = active,
              workout.restUntil != nil || workout.restPausedRemaining != nil else { return false }
        if let paused = workout.restPausedRemaining {
            workout.restPausedRemaining = min(3600, max(0, paused) + seconds)
        } else {
            workout.restUntil = Date().addingTimeInterval(min(3600, max(0, workout.restUntil!.timeIntervalSinceNow) + seconds))
        }
        var next = snapshot
        next.active = workout
        return persist(next)
    }

    @discardableResult
    func pauseRest() -> Bool {
        guard var workout = active, let deadline = workout.restUntil else { return false }
        workout.restPausedRemaining = min(3600, max(0, deadline.timeIntervalSinceNow))
        workout.restUntil = nil
        var next = snapshot
        next.active = workout
        return persist(next)
    }

    @discardableResult
    func resumeRest() -> Bool {
        guard var workout = active, let remaining = workout.restPausedRemaining,
              remaining.isFinite, (0...3600).contains(remaining) else { return false }
        workout.restUntil = Date().addingTimeInterval(remaining)
        workout.restPausedRemaining = nil
        var next = snapshot
        next.active = workout
        return persist(next)
    }

    @discardableResult
    func endRest() -> Bool {
        guard var workout = active else { return false }
        workout.restUntil = nil
        workout.restPausedRemaining = nil
        var next = snapshot
        next.active = workout
        return persist(next)
    }

    @discardableResult
    func updateSet(id: UUID, weightKg: Double, reps: Int) -> Bool {
        guard weightKg >= 0, weightKg <= 2000, weightKg.isFinite,
              (1...100).contains(reps) else { return false }
        var next = snapshot
        guard let index = next.logs.firstIndex(where: { $0.id == id }) else { return false }
        next.logs[index].weightKg = weightKg
        next.logs[index].reps = reps
        return persist(next)
    }

    @discardableResult
    func delete(id: UUID) -> Bool {
        var next = snapshot
        guard next.logs.contains(where: { $0.id == id }) else { return false }
        next.logs.removeAll { $0.id == id }
        next.active?.setIDs.removeAll { $0 == id }
        for index in next.history.indices {
            next.history[index].setIDs.removeAll { $0 == id }
        }
        return persist(next)
    }

    func records(for exerciseID: String) -> [LoggedSet] {
        logs.filter { $0.exerciseID == exerciseID }.sorted { $0.performedAt < $1.performedAt }
    }

    @discardableResult
    func start(protocolID: String, version: Int, sessionID: String, title: String) -> Bool {
        guard active == nil, !protocolID.isEmpty, version > 0, !sessionID.isEmpty else { return false }
        var next = snapshot
        next.active = ActiveWorkout(protocolID: protocolID, protocolVersion: version,
                                    sessionID: sessionID, title: title)
        return persist(next)
    }

    @discardableResult
    func finish() -> Bool {
        guard var workout = active else { return false }
        workout.finishedAt = Date()
        var next = snapshot
        next.active = nil
        next.history.append(workout)
        return persist(next)
    }

    @discardableResult
    func discard() -> Bool {
        guard active != nil else { return false }
        var next = snapshot
        next.active = nil
        return persist(next)
    }

    @discardableResult
    func recordMeasuredMax(exerciseID: String, weightKg: Double) -> Bool {
        guard ["squat", "bench", "deadlift"].contains(exerciseID),
              weightKg > 0, weightKg <= 2000, weightKg.isFinite else { return false }
        var next = snapshot
        next.measuredMaxes.append(MeasuredMax(exerciseID: exerciseID, weightKg: weightKg, measuredAt: Date()))
        return persist(next)
    }

    /// A review screen saves all entered lifts in one transaction, never a partial success.
    @discardableResult
    func recordMeasuredMaxes(_ values: [String: Double]) -> Bool {
        guard !values.isEmpty, values.allSatisfy({
            ["squat", "bench", "deadlift"].contains($0.key) &&
                $0.value.isFinite && $0.value > 0 && $0.value <= 2000
        }) else {
            lastError = WorkoutStoreError.invalidSet.localizedDescription
            return false
        }
        var next = snapshot
        let now = Date()
        for id in ["squat", "bench", "deadlift"] {
            if let value = values[id] {
                next.measuredMaxes.append(MeasuredMax(exerciseID: id, weightKg: value, measuredAt: now))
            }
        }
        return persist(next)
    }
}

@MainActor
final class CatalogStore: ObservableObject {
    @Published private(set) var metadata: CatalogMetadata?
    @Published private(set) var isLoading = false
    @Published private(set) var studies: [ResearchStudy] = []
    @Published private(set) var protocols: [TrainingProtocol] = []
    @Published private(set) var demo: [TrainingProtocol] = []
    @Published private(set) var error: String?

    // The URL is configurable at build time; no localhost hardcoding for a shipped app.
    private let baseURL: URL?
    init() {
        baseURL = Bundle.main.object(forInfoDictionaryKey: "MugeMugeAPIURL")
            .flatMap { $0 as? String }.flatMap(URL.init(string:))
    }

    func refresh() async {
        guard !isLoading else { return }
        isLoading = true
        defer { isLoading = false }
        demo = Self.bundledDemo()
        if let baseURL, !(baseURL.scheme == "https" || (baseURL.host == "127.0.0.1" && baseURL.scheme == "http")) {
            protocols = []
            studies = []
            metadata = nil
            error = "HTTPS API 주소가 필요합니다."
            return
        }
        do {
            let catalog: CatalogResponse
            if let baseURL {
                catalog = try await load("/v1/protocols", baseURL: baseURL)
            } else {
                catalog = try await loadDatabaseCatalog()
            }
            protocols = catalog.items.filter(\.isPublishedResearch)
            studies = (catalog.studies ?? []).filter(\.isReadOnly)
            metadata = catalog.metadata
            error = nil
        } catch {
            protocols = []
            studies = []
            metadata = nil
            demo = Self.bundledDemo()
            self.error = "서버 연결에 실패했습니다. 체험 루틴과 기존 기록은 오프라인에서 이용할 수 있습니다."
        }
    }

    private func loadDatabaseCatalog() async throws -> CatalogResponse {
        let url = ResearchCatalogConfiguration.projectURL.appendingPathComponent("rest/v1/rpc/research_catalog")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.httpBody = Data("{}".utf8)
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue(ResearchCatalogConfiguration.publishableKey, forHTTPHeaderField: "apikey")
        request.timeoutInterval = 12
        let (data, response) = try await URLSession.shared.data(for: request)
        guard (response as? HTTPURLResponse)?.statusCode == 200 else { throw URLError(.badServerResponse) }
        let catalog = try JSONDecoder().decode(CatalogResponse.self, from: data)
        guard catalog.schemaVersion == 1 else { throw URLError(.cannotParseResponse) }
        return catalog
    }

    private func load(_ path: String, baseURL: URL) async throws -> CatalogResponse {
        var request = URLRequest(url: baseURL.appendingPathComponent(String(path.dropFirst())))
        request.timeoutInterval = 12
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let response = response as? HTTPURLResponse, response.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }
        let catalog = try JSONDecoder().decode(CatalogResponse.self, from: data)
        guard catalog.schemaVersion == 1 else { throw URLError(.cannotParseResponse) }
        return catalog
    }

    private static func bundledDemo() -> [TrainingProtocol] {
        guard let url = Bundle.main.url(forResource: "demo-catalog", withExtension: "json"),
              let data = try? Data(contentsOf: url),
              let response = try? JSONDecoder().decode(CatalogResponse.self, from: data) else {
            return []
        }
        return response.items.filter { $0.status == "DEMO_ONLY" && !$0.runnable }
    }
}
