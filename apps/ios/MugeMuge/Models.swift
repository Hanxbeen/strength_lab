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
    var studies: [ResearchStudy]? = nil
    var metadata: CatalogMetadata? = nil
    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version", items, metadata, studies
    }
}
struct ResearchStudy: Decodable, Identifiable {
    let pmid: String
    let title: String
    let sourceURL: URL
    let decision: String
    let runnable: Bool
    let reasons: [ResearchReason]
    var id: String { pmid }
    enum CodingKeys: String, CodingKey {
        case pmid, title, decision, runnable, reasons
        case sourceURL = "source_url"
    }
    var isReadOnly: Bool {
        !runnable && ["NOT_RUNNABLE", "SOURCE_ERROR"].contains(decision)
        && sourceURL.scheme == "https" && sourceURL.host == "pubmed.ncbi.nlm.nih.gov"
    }
}
struct ResearchReason: Decodable {
    let code: String
    let message: String
}
struct CatalogMetadata: Decodable {
    let candidates: Int
    let requested: Int
    let awaitingReview: Int
    var automaticallyChecked: Int? = nil
    let checkedAt: String
    enum CodingKeys: String, CodingKey {
        case candidates, requested
        case awaitingReview = "awaiting_review"
        case automaticallyChecked = "automatically_checked"
        case checkedAt = "checked_at"
    }
}
enum ResearchCatalogConfiguration {
    static let projectURL = URL(string: "https://gttvyfeyrnuspnnphuzk.supabase.co")!
    // Public client key; private candidate tables are not accessible to this role.
    static let publishableKey = "sb_publishable_ghbVxjHXJQDYh7CbvA-y5A_5qhNpSIv"
}
struct TrainingProtocol: Decodable, Identifiable {
    let id: String
    let version: Int
    let title: String
    let status: String
    let runnable: Bool
    let description: String
    let sessions: [TrainingSession]
    var sourceType: String? = nil
    var sourceDigest: String? = nil
    var releaseID: String? = nil
    enum CodingKeys: String, CodingKey {
        case id, version, title, status, runnable, description, sessions
        case sourceType = "source_type", sourceDigest = "source_sha256", releaseID = "release_id"
    }
    var isPublishedResearch: Bool {
        runnable && status == "PUBLISHED_PROTOCOL" && sourceType == "RESEARCH"
        && version > 0 && !(releaseID ?? "").isEmpty && !sessions.isEmpty
        && (sourceDigest?.range(of: "^[a-f0-9]{64}$", options: .regularExpression) != nil)
    }
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
    var targetWeightKg: Double?
    var targetReps: Int?
}
