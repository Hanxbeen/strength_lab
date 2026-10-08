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
    private let url: URL
    private var storageBlocked = false

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
    @discardableResult
    func completeSet(exerciseID: String, weightKg: Double, reps: Int,
                     protocolID: String, version: Int, sessionID: String,
                     restSeconds: Int) -> UUID? {
        guard var workout = active, workout.protocolID == protocolID,
              workout.protocolVersion == version, workout.sessionID == sessionID,
              !exerciseID.isEmpty, weightKg >= 0, weightKg <= 2000,
              weightKg.isFinite, (1...100).contains(reps),
              (0...3600).contains(restSeconds) else { return nil }
        let entry = LoggedSet(exerciseID: exerciseID, weightKg: weightKg, reps: reps)
        workout.setIDs.append(entry.id)
        workout.restUntil = Date().addingTimeInterval(TimeInterval(restSeconds))
        var next = snapshot
        next.logs.append(entry)
        next.active = workout
        return persist(next) ? entry.id : nil
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
}

@MainActor
final class CatalogStore: ObservableObject {
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
        guard let baseURL else {
            protocols = []
            demo = Self.bundledDemo()
            error = nil
            return
        }
        guard baseURL.scheme == "https" || (baseURL.host == "127.0.0.1" && baseURL.scheme == "http") else {
            error = "HTTPS API 주소가 필요합니다."
            return
        }
        do {
            async let published = load("/v1/protocols", baseURL: baseURL)
            async let samples = load("/v1/demo-protocols", baseURL: baseURL)
            let (catalog, preview) = try await (published, samples)
            protocols = catalog.items.filter { $0.runnable && $0.status == "PUBLISHED_PROTOCOL" }
            demo = preview.items.filter { $0.status == "DEMO_ONLY" && !$0.runnable }
            error = nil
        } catch {
            protocols = []
            demo = Self.bundledDemo()
            self.error = "서버 연결에 실패했습니다. 체험 루틴과 기존 기록은 오프라인에서 이용할 수 있습니다."
        }
    }

    private func load(_ path: String, baseURL: URL) async throws -> CatalogResponse {
        var request = URLRequest(url: baseURL.appendingPathComponent(String(path.dropFirst())))
        request.timeoutInterval = 12
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let response = response as? HTTPURLResponse, response.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }
        return try JSONDecoder().decode(CatalogResponse.self, from: data)
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
