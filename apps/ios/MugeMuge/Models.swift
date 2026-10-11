import Foundation

/// Display conversion never mutates canonical kg records or applies equipment rounding.
enum MassUnit: String, CaseIterable, Codable {
    case kg, lb
    static let kilogramsPerPound = 0.45359237
    var step: Double { self == .kg ? 2.5 : 5 }
    func display(_ kilograms: Double) -> Double {
        self == .kg ? kilograms : kilograms / Self.kilogramsPerPound
    }
    func kilograms(_ value: Double) -> Double {
        self == .kg ? value : value * Self.kilogramsPerPound
    }
    func number(_ kilograms: Double) -> String {
        display(kilograms).formatted(.number.precision(.fractionLength(0...1)))
    }
    func label(_ kilograms: Double) -> String { "\(number(kilograms)) \(rawValue)" }
    func parse(_ text: String, allowsZero: Bool = false) -> Double? {
        guard let value = Double(text.replacingOccurrences(of: ",", with: ".")), value.isFinite else { return nil }
        let kg = kilograms(value)
        guard kg <= 2000, (allowsZero ? kg >= 0 : kg > 0) else { return nil }
        return kg
    }
    func input(_ kilograms: Double) -> String {
        String(format: "%.8f", locale: Locale(identifier: "en_US_POSIX"), display(kilograms))
            .replacingOccurrences(of: #"\.?0+$"#, with: "", options: .regularExpression)
    }
}

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
