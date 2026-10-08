import Foundation

/// A conservative, deterministic merge planner. Never silently chooses between edits.
enum CloudMergeError: LocalizedError {
    case incompatibleSchema, conflictingSet(UUID), conflictingSession(UUID), conflictingMax(UUID), activeSession
    var errorDescription: String? {
        switch self {
        case .incompatibleSchema: return "지원하지 않는 기록 형식입니다."
        case .conflictingSet: return "같은 세트가 서로 다르게 수정됐습니다. 자동 병합하지 않습니다."
        case .conflictingSession: return "같은 운동 세션의 내용이 충돌합니다."
        case .conflictingMax: return "실측 최대 중량 기록이 충돌합니다."
        case .activeSession: return "진행 중인 운동 세션이 있어 병합을 보류합니다."
        }
    }
}

enum CloudMerge {
    /// Combines distinct UUID records only. Deletions, shared UUID edits, and active sessions
    /// require explicit resolution; union alone could resurrect deleted records.
    static func preview(local: CloudPayload, remote: CloudPayload) throws -> CloudPayload {
        guard local.schemaVersion == 1, remote.schemaVersion == 1 else {
            throw CloudMergeError.incompatibleSchema
        }
        guard local.active == nil, remote.active == nil else {
            throw CloudMergeError.activeSession
        }
        func combine<T: Encodable>(_ left: [T], _ right: [T],
                                   id: (T) -> UUID, conflict: (UUID) -> CloudMergeError) throws -> [T] {
            var seen: [UUID: Data] = [:]
            var output: [T] = []
            let encoder = JSONEncoder()
            encoder.outputFormatting = [.sortedKeys]
            for item in left + right {
                let key = id(item)
                let bytes = try encoder.encode(item)
                if let prior = seen[key] {
                    if prior != bytes { throw conflict(key) }
                } else {
                    seen[key] = bytes
                    output.append(item)
                }
            }
            return output
        }
        let logs = try combine(local.logs, remote.logs, id: { $0.id }, conflict: CloudMergeError.conflictingSet)
        let history = try combine(local.history, remote.history, id: { $0.id }, conflict: CloudMergeError.conflictingSession)
        let maxes = try combine(local.measuredMaxes, remote.measuredMaxes, id: { $0.id }, conflict: CloudMergeError.conflictingMax)
        return CloudPayload(schemaVersion: 1, logs: logs, active: nil, history: history, measuredMaxes: maxes)
    }
}
