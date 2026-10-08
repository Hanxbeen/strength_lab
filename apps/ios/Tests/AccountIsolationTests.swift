import Foundation

@main struct AccountIsolationTests {
    @MainActor static func main() throws {
        let dir = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: dir) }
        let store = WorkoutStore(directory: dir)
        let guestSet = store.append(exerciseID: "squat", weightKg: 100, reps: 5)!
        let alice = UUID(), bob = UUID()
        assert(store.switchAccount(alice))
        assert(store.logs.isEmpty)
        let aliceSet = store.append(exerciseID: "bench", weightKg: 70, reps: 5)!
        assert(store.switchAccount(bob))
        assert(store.logs.isEmpty)
        assert(store.switchAccount(alice))
        assert(store.logs.map(\.id) == [aliceSet])
        assert(store.switchAccount(nil))
        assert(store.logs.map(\.id) == [guestSet])
        // Corruption cannot replace currently loaded records.
        let corrupt = dir.appendingPathComponent("workout-account-\(bob.uuidString.lowercased()).json")
        try Data("bad".utf8).write(to: corrupt)
        assert(!store.switchAccount(bob))
        assert(store.logs.isEmpty)
        assert(store.append(exerciseID: "squat", weightKg: 10, reps: 5) == nil)
        assert(store.switchAccount(nil))
        assert(store.logs.map(\.id) == [guestSet])
        print("Account isolation: 11 assertions passed")
    }
}
