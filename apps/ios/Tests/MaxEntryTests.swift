import Foundation

@main struct MaxEntryTests {
    @MainActor static func main() throws {
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: directory) }
        let store = WorkoutStore(directory: directory)
        assert(!store.recordMeasuredMaxes([:]))
        assert(!store.recordMeasuredMaxes(["squat": 100, "bench": -1]))
        assert(store.measuredMaxes.isEmpty)
        assert(!store.recordMeasuredMaxes(["other": 100]))
        assert(!store.recordMeasuredMaxes(["squat": .nan]))
        assert(store.recordMeasuredMaxes(["squat": 100, "deadlift": 140]))
        let restored = WorkoutStore(directory: directory)
        assert(restored.measuredMaxes.count == 2)
        assert(Set(restored.measuredMaxes.map(\.exerciseID)) == Set(["squat", "deadlift"]))
        assert(restored.measuredMaxes[0].measuredAt == restored.measuredMaxes[1].measuredAt)
        assert(restored.recordMeasuredMaxes(["bench": 75]))
        assert(restored.measuredMaxes.count == 3)
        assert(restored.start(protocolID: "demo", version: 1, sessionID: "s", title: "기록 연습"))
        assert(restored.completeSet(exerciseID: "squat", weightKg: 40, reps: 5,
                                    protocolID: "demo", version: 1, sessionID: "s", restSeconds: 0) != nil)
        assert(restored.active?.restUntil == nil)
        assert(restored.active?.restPausedRemaining == nil)
        assert(WorkoutStore(directory: directory).active?.restUntil == nil)
        // An unreadable existing database must stay untouched, including batch writes.
        let corruptDirectory = directory.appendingPathComponent("corrupt")
        try FileManager.default.createDirectory(at: corruptDirectory, withIntermediateDirectories: true)
        let file = corruptDirectory.appendingPathComponent("workout-database.json")
        let original = Data("corrupt".utf8)
        try original.write(to: file)
        let blocked = WorkoutStore(directory: corruptDirectory)
        assert(!blocked.recordMeasuredMaxes(["squat": 100]))
        assert(blocked.measuredMaxes.isEmpty)
        let preserved = try Data(contentsOf: file)
        assert(preserved == original)
        print("MaxEntry: atomic batch, partial lifts, validation and zero-rest assertions passed")
    }
}
