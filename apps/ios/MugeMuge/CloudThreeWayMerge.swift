import Foundation

/// Three-way reconciliation. Deletions are represented by absence relative to the
/// common ancestor, so a deleted record cannot be resurrected by an unchanged peer.
enum CloudThreeWayMerge {
    enum Conflict: Error, Equatable {
        case schema, activeSession, set(UUID), session(UUID), max(UUID)
    }

    static func merge(base: CloudPayload, local: CloudPayload, remote: CloudPayload) throws -> CloudPayload {
        guard [base, local, remote].allSatisfy({ $0.schemaVersion == 1 }) else { throw Conflict.schema }
        guard base.active == nil, local.active == nil, remote.active == nil else { throw Conflict.activeSession }

        func reconcile<T: Codable & Identifiable>(_ baseline: [T], _ left: [T], _ right: [T],
                                                   conflict: (UUID) -> Conflict) throws -> [T] where T.ID == UUID {
            let encoder = JSONEncoder()
            encoder.outputFormatting = [.sortedKeys]
            func keyed(_ items: [T]) throws -> [UUID: Data] {
                var values: [UUID: Data] = [:]
                for item in items {
                    if values[item.id] != nil { throw conflict(item.id) }
                    values[item.id] = try encoder.encode(item)
                }
                return values
            }
            let old = try keyed(baseline), mine = try keyed(left), theirs = try keyed(right)
            let all = Set(old.keys).union(mine.keys).union(theirs.keys)
            var output: [T] = []
            for id in all.sorted(by: { $0.uuidString < $1.uuidString }) {
                let before = old[id], a = mine[id], b = theirs[id]
                let chosen: Data?
                if a == b { chosen = a }
                else if a == before { chosen = b }
                else if b == before { chosen = a }
                else { throw conflict(id) }
                if let chosen { output.append(try JSONDecoder().decode(T.self, from: chosen)) }
            }
            return output
        }

        let logs = try reconcile(base.logs, local.logs, remote.logs, conflict: Conflict.set)
        let history = try reconcile(base.history, local.history, remote.history, conflict: Conflict.session)
        let maxes = try reconcile(base.measuredMaxes, local.measuredMaxes, remote.measuredMaxes, conflict: Conflict.max)
        let valid = Set(logs.map(\.id))
        guard history.allSatisfy({ $0.setIDs.allSatisfy(valid.contains) }) else {
            throw Conflict.schema
        }
        return CloudPayload(schemaVersion: 1, logs: logs, active: nil, history: history, measuredMaxes: maxes)
    }
}
