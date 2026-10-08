import Foundation

/// Pure decision engine for eventual bidirectional sync. No network calls or destructive writes.
enum CloudSyncPlan {
    enum Action {
        case noChange
        case upload(CloudPayload, expectedRevision: Int64)
        case download(CloudPayload, revision: Int64)
        case conflict
    }

    /// Requires a trusted common ancestor from a prior successful sync.
    /// Without it, refuse to guess which records were deleted.
    static func decide(base: CloudPayload?, baseRevision: Int64?,
                       local: CloudPayload, remote: CloudSnapshot?) -> Action {
        guard let base, let baseRevision, let remote else { return .conflict }
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys]
        guard let baseBytes = try? encoder.encode(base),
              let localBytes = try? encoder.encode(local),
              let remoteBytes = try? encoder.encode(remote.payload) else { return .conflict }
        if localBytes == remoteBytes {
            return .noChange
        }
        if remote.revision == baseRevision {
            return .upload(local, expectedRevision: baseRevision)
        }
        if localBytes == baseBytes {
            return .download(remote.payload, revision: remote.revision)
        }
        guard let merged = try? CloudThreeWayMerge.merge(base: base, local: local, remote: remote.payload) else {
            return .conflict
        }
        return .upload(merged, expectedRevision: remote.revision)
    }
}
