import Foundation

@main struct CloudThreeWayMergeTests {
    static func main() throws {
        func payload(_ sets: [LoggedSet]) -> CloudPayload {
            CloudPayload(schemaVersion: 1, logs: sets, active: nil, history: [], measuredMaxes: [])
        }
        let a = LoggedSet(exerciseID: "squat", weightKg: 100, reps: 5)
        let b = LoggedSet(exerciseID: "bench", weightKg: 80, reps: 5)
        let c = LoggedSet(exerciseID: "deadlift", weightKg: 120, reps: 3)
        let base = payload([a])
        // A deletion on one side beats an unchanged copy on the other.
        assert(try! CloudThreeWayMerge.merge(base: base, local: payload([]), remote: base).logs.isEmpty)
        assert(try! CloudThreeWayMerge.merge(base: base, local: base, remote: payload([])).logs.isEmpty)
        // Independent additions are both retained.
        assert(try! CloudThreeWayMerge.merge(base: base, local: payload([a,b]), remote: payload([a,c])).logs.count == 3)
        var changed = a
        changed.weightKg = 105
        // A change on one side wins over unchanged baseline.
        assert(try! CloudThreeWayMerge.merge(base: base, local: payload([changed]), remote: base).logs[0].weightKg == 105)
        // Deletion against concurrent edit is a conflict, never a silent resurrection.
        do {
            _ = try CloudThreeWayMerge.merge(base: base, local: payload([]), remote: payload([changed]))
            fatalError("Expected delete/edit conflict")
        } catch CloudThreeWayMerge.Conflict.set {}
        var differentlyChanged = a
        differentlyChanged.weightKg = 110
        do {
            _ = try CloudThreeWayMerge.merge(base: base, local: payload([changed]), remote: payload([differentlyChanged]))
            fatalError("Expected edit/edit conflict")
        } catch CloudThreeWayMerge.Conflict.set {}
        print("Three-way merge: 6 cases passed")
    }
}
