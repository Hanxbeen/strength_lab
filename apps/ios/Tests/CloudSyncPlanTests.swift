import Foundation

@main struct CloudSyncPlanTests {
    static func main() {
        func payload(_ logs: [LoggedSet]) -> CloudPayload {
            CloudPayload(schemaVersion: 1, logs: logs, active: nil, history: [], measuredMaxes: [])
        }
        let a = LoggedSet(exerciseID: "squat", weightKg: 100, reps: 5)
        let b = LoggedSet(exerciseID: "bench", weightKg: 70, reps: 5)
        let c = LoggedSet(exerciseID: "deadlift", weightKg: 140, reps: 3)
        let base = payload([a])
        let old = CloudSnapshot(revision: 1, payload: base)
        switch CloudSyncPlan.decide(base: base, baseRevision: 1, local: base, remote: old) {
        case .noChange: break
        default: fatalError("Equal snapshots must be no-op")
        }
        switch CloudSyncPlan.decide(base: base, baseRevision: 1, local: payload([a,b]), remote: old) {
        case .upload(_, let revision): assert(revision == 1)
        default: fatalError("Local edit should upload")
        }
        switch CloudSyncPlan.decide(base: base, baseRevision: 1, local: base, remote: CloudSnapshot(revision: 2, payload: payload([a,c]))) {
        case .download(let value, let revision): assert(revision == 2 && value.logs.count == 2)
        default: fatalError("Remote edit should download")
        }
        switch CloudSyncPlan.decide(base: base, baseRevision: 1, local: payload([a,b]), remote: CloudSnapshot(revision: 2, payload: payload([a,c]))) {
        case .upload(let value, let revision): assert(revision == 2 && value.logs.count == 3)
        default: fatalError("Independent edits should merge")
        }
        var edited = a
        edited.weightKg = 115
        switch CloudSyncPlan.decide(base: base, baseRevision: 1, local: payload([]), remote: CloudSnapshot(revision: 2, payload: payload([edited]))) {
        case .conflict: break
        default: fatalError("Deletion against edit must conflict")
        }
        switch CloudSyncPlan.decide(base: nil, baseRevision: nil, local: base, remote: old) {
        case .conflict: break
        default: fatalError("Missing common ancestor must conflict")
        }
        print("Cloud sync planner: 6 scenarios passed")
    }
}
