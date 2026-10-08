import Foundation

@main
struct AtomicWorkoutTests {
    @MainActor static func main() {
        let folder = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try! FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: folder) }
        let store = WorkoutStore(directory: folder)
        assert(store.start(protocolID: "study", version: 3, sessionID: "day-1", title: "Session"))
        assert(store.completeSet(exerciseID: "squat", weightKg: 100, reps: 5,
                                 protocolID: "wrong", version: 3, sessionID: "day-1", restSeconds: 180) == nil)
        assert(store.logs.isEmpty)
        let id = store.completeSet(exerciseID: "squat", weightKg: 100, reps: 5,
                                   protocolID: "study", version: 3, sessionID: "day-1", restSeconds: 180)!
        let restored = WorkoutStore(directory: folder)
        assert(restored.logs.count == 1)
        assert(restored.active!.setIDs == [id])
        assert(restored.updateSet(id: id, weightKg: 105, reps: 4))
        assert(WorkoutStore(directory: folder).logs[0].weightKg == 105)
        assert(restored.finish())
        assert(restored.delete(id: id))
        let after = WorkoutStore(directory: folder)
        assert(after.logs.isEmpty)
        assert(after.history[0].setIDs.isEmpty)
        assert(after.history[0].protocolVersion == 3)

        let corruptFolder = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try! FileManager.default.createDirectory(at: corruptFolder, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: corruptFolder) }
        try! Data("corrupted".utf8).write(to: corruptFolder.appendingPathComponent("workout-database.json"))
        let corrupted = WorkoutStore(directory: corruptFolder)
        assert(corrupted.lastError != nil)
        assert(corrupted.append(exerciseID: "squat", weightKg: 100, reps: 5) == nil)
        assert(String(data: try! Data(contentsOf: corruptFolder.appendingPathComponent("workout-database.json")), encoding: .utf8) == "corrupted")

        let legacyFolder = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try! FileManager.default.createDirectory(at: legacyFolder, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: legacyFolder) }
        let legacySet = LoggedSet(exerciseID: "bench", weightKg: 70, reps: 5)
        try! JSONEncoder().encode([legacySet]).write(to: legacyFolder.appendingPathComponent("workout-logs.json"))
        let migrated = WorkoutStore(directory: legacyFolder)
        assert(migrated.logs.count == 1)
        assert(WorkoutStore(directory: legacyFolder).logs[0].id == legacySet.id)
        assert(FileManager.default.fileExists(atPath: legacyFolder.appendingPathComponent("workout-logs.json").path))
        print("AtomicWorkout: 17 reliability assertions passed")
    }
}
