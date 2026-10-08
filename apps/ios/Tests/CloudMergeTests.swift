import Foundation

@main struct CloudMergeTests {
    static func main() {
        let a = LoggedSet(exerciseID: "squat", weightKg: 100, reps: 5)
        let b = LoggedSet(exerciseID: "bench", weightKg: 80, reps: 5)
        let empty = CloudPayload(schemaVersion: 1, logs: [], active: nil, history: [], measuredMaxes: [])
        let local = CloudPayload(schemaVersion: 1, logs: [a], active: nil, history: [], measuredMaxes: [])
        let remote = CloudPayload(schemaVersion: 1, logs: [b], active: nil, history: [], measuredMaxes: [])
        let joined = try! CloudMerge.preview(local: local, remote: remote)
        assert(joined.logs.count == 2)
        assert(try! CloudMerge.preview(local: local, remote: local).logs.count == 1)
        assert(try! CloudMerge.preview(local: empty, remote: remote).logs.count == 1)
        var edited = a
        edited.weightKg = 120
        let conflicting = CloudPayload(schemaVersion: 1, logs: [edited], active: nil, history: [], measuredMaxes: [])
        do {
            _ = try CloudMerge.preview(local: local, remote: conflicting)
            fatalError("Same UUID edited differently must fail")
        } catch CloudMergeError.conflictingSet {} catch { fatalError("Unexpected error: \(error)") }
        let invalid = CloudPayload(schemaVersion: 2, logs: [], active: nil, history: [], measuredMaxes: [])
        do {
            _ = try CloudMerge.preview(local: invalid, remote: empty)
            fatalError("Invalid schema must fail")
        } catch CloudMergeError.incompatibleSchema {} catch { fatalError("Unexpected error: \(error)") }
        print("Cloud merge preview tests: 5 assertions passed")
    }
}
