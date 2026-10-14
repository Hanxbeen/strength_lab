import Foundation

@main struct ReasonRecordTests {
    @MainActor static func main() throws {
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: directory) }
        let store = WorkoutStore(directory: directory)
        assert(store.start(protocolID: "demo", version: 1, sessionID: "d1", title: "test", initialWeights: ["squat": 80]))
        let change = store.recordChange(exerciseID: "squat", ordinal: 1, kind: "load", fromKg: 80, toKg: 75)!
        assert(store.recordChange(exerciseID: "squat", ordinal: 1, kind: "load", fromKg: 80, toKg: 75, requestID: change) == change)
        assert(store.recordChange(exerciseID: "squat", ordinal: 1, kind: "load", fromKg: 80, toKg: 70, requestID: change) == nil)
        let reportID = UUID()
        assert(store.recordReason(target: change, codes: [.effortInsufficient, .painDiscomfort],
                                  status: .answered, supersedes: nil, requestID: reportID))
        assert(store.active?.painPaused == true)
        assert(store.completeSet(exerciseID: "squat", weightKg: 75, reps: 4, protocolID: "demo",
                                 version: 1, sessionID: "d1", restSeconds: 180) == nil)
        assert(store.recordReason(target: change, codes: [.effortInsufficient, .painDiscomfort],
                                  status: .answered, supersedes: nil, requestID: reportID))
        assert(store.change(id: change)?.reports.count == 1)
        assert(!store.recordReason(target: change, codes: [.equipment], status: .answered, supersedes: nil))
        assert(store.resumeAfterPain())
        let token = UUID()
        let set = store.completeSet(exerciseID: "squat", weightKg: 75, reps: 0, protocolID: "demo",
                                   version: 1, sessionID: "d1", restSeconds: 180, requestID: token, targetReps: 5)!
        assert(set == token && store.logs.last?.targetWeightKg == 80)
        assert(store.endRest())
        assert(store.active?.restRecords?.count == 1)
        assert(store.finish())
        assert(store.recordReason(target: change, codes: [.equipment], status: .answered, supersedes: reportID))
        let reloaded = WorkoutStore(directory: directory)
        assert(reloaded.change(id: change)?.reports.count == 2)
        assert(reloaded.change(id: change)?.latestReport?.reasonCodes == [.equipment])
        assert(reloaded.previousWorkout(protocolID: "demo", version: 1, sessionID: "d1") != nil)
        assert(reloaded.previousWorkout(protocolID: "demo", version: 2, sessionID: "d1") == nil)
        let backup = try reloaded.exportBackup()
        let imported = WorkoutStore(filename: "copy.json", directory: directory)
        assert(imported.importBackup(backup))
        assert(imported.change(id: change)?.reports.count == 2)
        assert(imported.history.first?.restRecords?.count == 1)
        var invalid = try JSONSerialization.jsonObject(with: backup) as! [String: Any]
        var history = invalid["history"] as! [[String: Any]]
        var changes = history[0]["changes"] as! [[String: Any]]
        var reports = changes[0]["reports"] as! [[String: Any]]
        reports[1]["supersedesEventID"] = UUID().uuidString
        changes[0]["reports"] = reports; history[0]["changes"] = changes; invalid["history"] = history
        let invalidBackup = try JSONSerialization.data(withJSONObject: invalid)
        assert(!imported.importBackup(invalidBackup))
        assert(imported.change(id: change)?.reports.count == 2)
        print("Reason records: persistence, pause, zero reps, correction, backup, contextual history passed")
    }
}
