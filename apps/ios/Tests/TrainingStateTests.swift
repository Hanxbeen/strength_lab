import Foundation

@main
struct TrainingStateTests {
    @MainActor static func main() {
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try! FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: directory) }
        let store = TrainingState(directory: directory)
        assert(store.start(protocolID: "demo", version: 1, sessionID: "session", title: "Test"))
        assert(!store.start(protocolID: "other", version: 1, sessionID: "session", title: "Cannot overlap"))
        let initialID = store.active!.id
        let setID = UUID()
        assert(store.attachSet(setID, restSeconds: 120))
        assert(store.active!.setIDs == [setID])
        assert(!store.recordMeasuredMax(exerciseID: "bench", weightKg: -5))
        assert(store.recordMeasuredMax(exerciseID: "bench", weightKg: 110))
        let restored = TrainingState(directory: directory)
        assert(restored.active!.id == initialID)
        assert(restored.active!.setIDs == [setID])
        assert(restored.measuredMaxes.count == 1)
        assert(restored.finish())
        let completed = TrainingState(directory: directory)
        assert(completed.active == nil)
        assert(completed.history.count == 1)
        assert(completed.history[0].protocolVersion == 1)
        print("TrainingState: 12 assertions passed")
    }
}
