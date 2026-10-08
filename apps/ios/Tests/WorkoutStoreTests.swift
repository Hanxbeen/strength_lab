import Foundation

@main
struct WorkoutStoreTests {
    @MainActor static func main() {
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try! FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: directory) }
        let store = WorkoutStore(directory: directory)
        assert(store.append(exerciseID: "squat", weightKg: -1, reps: 5) == nil)
        assert(store.append(exerciseID: "squat", weightKg: 100, reps: 0) == nil)
        let id = store.append(exerciseID: "squat", weightKg: 100, reps: 5)
        assert(id != nil)
        assert(store.logs.count == 1)
        let restored = WorkoutStore(directory: directory)
        assert(restored.logs.count == 1)
        assert(restored.logs[0].id == id!)
        restored.delete(id: id!)
        assert(WorkoutStore(directory: directory).logs.isEmpty)
        print("WorkoutStore: 7 assertions passed")
    }
}
