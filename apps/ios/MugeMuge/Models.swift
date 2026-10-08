import Foundation

struct CatalogResponse: Decodable {
    let schemaVersion: Int
    let items: [TrainingProtocol]
    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version", items
    }
}
struct TrainingProtocol: Decodable, Identifiable {
    let id: String
    let version: Int
    let title: String
    let status: String
    let runnable: Bool
    let description: String
    let sessions: [TrainingSession]
}
struct TrainingSession: Decodable, Identifiable {
    let id: String
    let title: String
    let exercises: [TrainingExercise]
}
struct TrainingExercise: Decodable, Identifiable {
    let id: String
    let name: String
    let sets: Int
    let reps: Int
    let restSeconds: Int
    enum CodingKeys: String, CodingKey {
        case id, name, sets, reps
        case restSeconds = "rest_seconds"
    }
}
struct LoggedSet: Codable, Identifiable {
    var id: UUID = UUID()
    var exerciseID: String
    var weightKg: Double
    var reps: Int
    var performedAt: Date = Date()
}
