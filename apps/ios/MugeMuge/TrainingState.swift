import Foundation
import Combine

struct ActiveWorkout: Codable, Identifiable {
    let id: UUID
    let protocolID: String
    let protocolVersion: Int
    let sessionID: String
    let title: String
    let startedAt: Date
    var finishedAt: Date?
    var setIDs: [UUID]
    var restUntil: Date?

    init(protocolID: String, protocolVersion: Int, sessionID: String, title: String) {
        self.id = UUID()
        self.protocolID = protocolID
        self.protocolVersion = protocolVersion
        self.sessionID = sessionID
        self.title = title
        self.startedAt = Date()
        self.setIDs = []
    }
}

struct MeasuredMax: Codable, Identifiable {
    var id = UUID()
    let exerciseID: String
    let weightKg: Double
    let measuredAt: Date
}

@MainActor
final class TrainingState: ObservableObject {
    @Published private(set) var active: ActiveWorkout?
    @Published private(set) var history: [ActiveWorkout] = []
    @Published private(set) var measuredMaxes: [MeasuredMax] = []
    @Published private(set) var error: String?
    private let url: URL

    private struct Snapshot: Codable {
        var active: ActiveWorkout?
        var history: [ActiveWorkout]
        var measuredMaxes: [MeasuredMax]
    }

    init(filename: String = "training-state.json", directory: URL? = nil) {
        let folder = directory ?? FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
        try? FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
        url = folder.appendingPathComponent(filename)
        if let data = try? Data(contentsOf: url),
           let snapshot = try? JSONDecoder().decode(Snapshot.self, from: data) {
            active = snapshot.active
            history = snapshot.history
            measuredMaxes = snapshot.measuredMaxes
        }
    }

    @discardableResult
    func start(protocolID: String, version: Int, sessionID: String, title: String) -> Bool {
        guard active == nil, !protocolID.isEmpty, version > 0, !sessionID.isEmpty else { return false }
        return persist(Snapshot(active: ActiveWorkout(protocolID: protocolID, protocolVersion: version,
                                                       sessionID: sessionID, title: title),
                                history: history, measuredMaxes: measuredMaxes))
    }

    @discardableResult
    func attachSet(_ id: UUID, restSeconds: Int) -> Bool {
        guard var workout = active, !workout.setIDs.contains(id) else { return false }
        workout.setIDs.append(id)
        workout.restUntil = Date().addingTimeInterval(TimeInterval(max(0, restSeconds)))
        return persist(Snapshot(active: workout, history: history, measuredMaxes: measuredMaxes))
    }

    @discardableResult
    func finish() -> Bool {
        guard var workout = active else { return false }
        workout.finishedAt = Date()
        return persist(Snapshot(active: nil, history: history + [workout], measuredMaxes: measuredMaxes))
    }

    @discardableResult
    func discard() -> Bool {
        guard active != nil else { return false }
        return persist(Snapshot(active: nil, history: history, measuredMaxes: measuredMaxes))
    }

    @discardableResult
    func recordMeasuredMax(exerciseID: String, weightKg: Double) -> Bool {
        guard ["squat", "bench", "deadlift"].contains(exerciseID),
              weightKg > 0, weightKg <= 2000, weightKg.isFinite else { return false }
        return persist(Snapshot(active: active, history: history,
                                measuredMaxes: measuredMaxes + [MeasuredMax(exerciseID: exerciseID,
                                                                            weightKg: weightKg, measuredAt: Date())]))
    }

    func removeSetReference(_ id: UUID) {
        guard var workout = active else { return }
        workout.setIDs.removeAll { $0 == id }
        _ = persist(Snapshot(active: workout, history: history, measuredMaxes: measuredMaxes))
    }

    @discardableResult
    private func persist(_ snapshot: Snapshot) -> Bool {
        do {
            try JSONEncoder().encode(snapshot).write(to: url, options: .atomic)
            active = snapshot.active
            history = snapshot.history
            measuredMaxes = snapshot.measuredMaxes
            error = nil
            return true
        } catch {
            self.error = "운동 상태를 저장하지 못했습니다."
            return false
        }
    }
}
