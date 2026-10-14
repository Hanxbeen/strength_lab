import Foundation

enum WorkoutReason: String, Codable, CaseIterable, Identifiable {
    case effortInsufficient = "effort_insufficient"
    case painDiscomfort = "pain_discomfort"
    case technique, equipment
    case planChange = "plan_change"
    case time
    case effortAvailable = "effort_available"
    case plannedProgression = "planned_progression"
    case other
    var id: String { rawValue }
    var title: String {
        switch self {
        case .effortInsufficient: return "힘이 부족했어요"
        case .painDiscomfort: return "통증·불편함"
        case .technique: return "자세가 흐트러졌어요"
        case .equipment: return "장비 때문에"
        case .planChange: return "계획을 바꿨어요"
        case .time: return "시간이 부족했어요"
        case .effortAvailable: return "여유가 있었어요"
        case .plannedProgression: return "계획대로"
        case .other: return "기타"
        }
    }
}
enum ReasonResponseStatus: String, Codable {
    case answered, unknown, declined
    case notAsked = "not_asked"
}
struct WorkoutReasonReport: Codable, Identifiable {
    let id: UUID
    let schemaVersion: Int
    let targetEventID: UUID
    let supersedesEventID: UUID?
    let reasonCodes: [WorkoutReason]
    let responseStatus: ReasonResponseStatus
    let recordedAt: Date
    let reportedBy: String
    init(target: UUID, previous: UUID?, codes: [WorkoutReason], status: ReasonResponseStatus, id: UUID = UUID()) {
        self.id = id; schemaVersion = 1; targetEventID = target; supersedesEventID = previous
        reasonCodes = codes; responseStatus = status; recordedAt = Date(); reportedBy = "user"
    }
    var isValid: Bool {
        schemaVersion == 1 && reportedBy == "user" &&
        Set(reasonCodes).count == reasonCodes.count &&
        (responseStatus == .answered ? !reasonCodes.isEmpty : reasonCodes.isEmpty)
    }
}
struct WorkoutChange: Codable, Identifiable {
    let id: UUID
    let exerciseID: String?
    let setOrdinal: Int?
    let kind: String
    let fromKg: Double?
    let toKg: Double?
    let recordedAt: Date
    var reports: [WorkoutReasonReport]
    var latestReport: WorkoutReasonReport? { reports.last }
    var isValid: Bool {
        guard ["load", "finish", "shortfall"].contains(kind),
              fromKg.map({ $0.isFinite && (0...2000).contains($0) }) ?? true,
              toKg.map({ $0.isFinite && (0...2000).contains($0) }) ?? true,
              setOrdinal.map({ $0 > 0 }) ?? true,
              Set(reports.map(\.id)).count == reports.count else { return false }
        if kind == "load" && (fromKg == nil || toKg == nil || setOrdinal == nil || exerciseID?.isEmpty != false) { return false }
        var previous: UUID?
        for report in reports {
            guard report.isValid, report.targetEventID == id,
                  report.supersedesEventID == previous else { return false }
            previous = report.id
        }
        return true
    }
    var hasPain: Bool { latestReport?.reasonCodes.contains(.painDiscomfort) == true }
}
struct WorkoutRestRecord: Codable, Identifiable {
    let id: UUID
    let afterSetID: UUID
    let targetSeconds: Int
    let startedAt: Date
    let endedAt: Date
    let outcome: String
    var elapsedSeconds: Double { max(0, endedAt.timeIntervalSince(startedAt)) }
}
