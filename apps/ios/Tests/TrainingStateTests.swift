import Foundation

@main
struct TrainingStateTests {
    @MainActor static func main() {
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try! FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: directory) }
        let store = WorkoutStore(directory: directory)
        assert(store.start(protocolID: "demo", version: 1, sessionID: "session", title: "Test"))
        assert(!store.start(protocolID: "other", version: 1, sessionID: "session", title: "Cannot overlap"))
        let initialID = store.active!.id
        let setID = store.completeSet(exerciseID: "squat", weightKg: 100, reps: 5,
                                      protocolID: "demo", version: 1, sessionID: "session", restSeconds: 120)
        assert(setID != nil)
        assert(store.active!.setIDs == [setID!])
        assert(!store.recordMeasuredMax(exerciseID: "bench", weightKg: -5))
        assert(store.recordMeasuredMax(exerciseID: "bench", weightKg: 110))
        let restored = WorkoutStore(directory: directory)
        assert(restored.active!.id == initialID)
        assert(restored.active!.setIDs == [setID!])
        assert(restored.measuredMaxes.count == 1)
        assert(restored.finish())
        let completed = WorkoutStore(directory: directory)
        assert(completed.active == nil)
        assert(completed.history.count == 1)
        assert(completed.history[0].protocolVersion == 1)
        print("TrainingState: session and recovery assertions passed")
    }
}
