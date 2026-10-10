import Foundation

struct ActiveWorkout: Codable, Identifiable {
    let id: UUID
    let protocolID: String
    let protocolVersion: Int
    let sessionID: String
    let title: String
    let startedAt: Date
    var finishedAt: Date?
    var setIDs: [UUID]
    var restUntil: Date?
    var restPausedRemaining: TimeInterval?

    init(protocolID: String, protocolVersion: Int, sessionID: String, title: String) {
        self.id = UUID()
        self.protocolID = protocolID
        self.protocolVersion = protocolVersion
        self.sessionID = sessionID
        self.title = title
        self.startedAt = Date()
        self.setIDs = []
    }
}

struct MeasuredMax: Codable, Identifiable {
    var id = UUID()
    let exerciseID: String
    let weightKg: Double
    let measuredAt: Date
}

