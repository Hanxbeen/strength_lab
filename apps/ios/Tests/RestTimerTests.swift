import Foundation

@main
struct RestTimerTests {
    @MainActor static func main() throws {
        let folder = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: folder) }
        let store = WorkoutStore(directory: folder)
        assert(!store.pauseRest())
        assert(!store.adjustRest(by: 10))
        assert(store.start(protocolID: "demo", version: 1, sessionID: "a", title: "체험"))
        assert(store.completeSet(exerciseID: "bench", weightKg: 40, reps: 5,
                                 protocolID: "demo", version: 1, sessionID: "a", restSeconds: 120) != nil)
        assert(store.pauseRest())
        let paused = store.active!.restPausedRemaining!
        assert(paused > 118 && paused <= 120)
        assert(store.active!.restUntil == nil)
        assert(store.adjustRest(by: 10))
        let restored = WorkoutStore(directory: folder)
        assert(abs(restored.active!.restPausedRemaining! - paused - 10) < 0.01)
        assert(restored.resumeRest())
        assert(restored.active!.restPausedRemaining == nil)
        assert(restored.active!.restUntil!.timeIntervalSinceNow > 128)
        assert(!restored.adjustRest(by: .infinity))
        assert(!restored.adjustRest(by: -10))
        assert(restored.endRest())
        assert(WorkoutStore(directory: folder).active!.restUntil == nil)
        assert(restored.completeSet(exerciseID: "bench", weightKg: 40, reps: 5,
                                    protocolID: "demo", version: 1, sessionID: "a", restSeconds: 90) != nil)
        assert(restored.pauseRest())
        assert(restored.completeSet(exerciseID: "bench", weightKg: 40, reps: 5,
                                    protocolID: "demo", version: 1, sessionID: "a", restSeconds: 90) != nil)
        assert(restored.active!.restPausedRemaining == nil)
        // Old snapshots omit the new optional field.
        var json = try JSONSerialization.jsonObject(with: restored.exportBackup()) as! [String: Any]
        var active = json["active"] as! [String: Any]
        active.removeValue(forKey: "restPausedRemaining")
        json["active"] = active
        let legacyData = try JSONSerialization.data(withJSONObject: json)
        assert(restored.importBackup(legacyData))
        active["restPausedRemaining"] = -1
        json["active"] = active
        let invalidData = try JSONSerialization.data(withJSONObject: json)
        assert(!restored.importBackup(invalidData))
        assert(restored.logs.count == 3)
        print("RestTimer: persistence, resume, bounds and legacy compatibility passed")
    }
}
