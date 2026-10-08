import Foundation

@main
struct BackupTests {
    @MainActor static func main() throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: root) }
        let original = WorkoutStore(filename: "original.json", directory: root)
        assert(original.start(protocolID: "demo", version: 2, sessionID: "day1", title: "Day 1"))
        let id = original.completeSet(exerciseID: "squat", weightKg: 90, reps: 5,
                                      protocolID: "demo", version: 2, sessionID: "day1", restSeconds: 120)!
        let backup = try original.exportBackup()
        let restored = WorkoutStore(filename: "restored.json", directory: root)
        assert(restored.importBackup(backup))
        assert(restored.logs.first?.id == id)
        assert(restored.active?.setIDs == [id])
        assert(!restored.importBackup(Data("broken".utf8)))
        assert(restored.logs.first?.id == id)
        assert(restored.updateSet(id: id, weightKg: 92.5, reps: 4))
        assert(restored.logs[0].weightKg == 92.5)
        assert(!restored.updateSet(id: id, weightKg: .infinity, reps: 5))
        assert(restored.logs[0].weightKg == 92.5)
        print("Backup: 10 assertions passed")
    }
}
