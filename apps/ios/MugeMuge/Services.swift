import Foundation
import Combine

@MainActor
final class WorkoutStore: ObservableObject {
    @Published private(set) var logs: [LoggedSet] = []
    private let url: URL

    init(filename: String = "workout-logs.json") {
        let folder = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
        try? FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
        url = folder.appendingPathComponent(filename)
        if let data = try? Data(contentsOf: url),
           let saved = try? JSONDecoder().decode([LoggedSet].self, from: data) {
            logs = saved
        }
    }

    func append(exerciseID: String, weightKg: Double, reps: Int) {
        guard weightKg >= 0, weightKg.isFinite, reps > 0, reps <= 100 else { return }
        logs.append(LoggedSet(exerciseID: exerciseID, weightKg: weightKg, reps: reps))
        if let data = try? JSONEncoder().encode(logs) {
            try? data.write(to: url, options: .atomic)
        }
    }
}

@MainActor
final class CatalogStore: ObservableObject {
    @Published private(set) var protocols: [TrainingProtocol] = []
    @Published private(set) var demo: [TrainingProtocol] = []
    @Published private(set) var error: String?
    // Change to a deployed HTTPS endpoint at release time. Never use HTTP in production.
    var baseURL = URL(string: "http://127.0.0.1:8000")!

    func refresh() async {
        do {
            async let published = load("/v1/protocols")
            async let samples = load("/v1/demo-protocols")
            protocols = try await published.items.filter { $0.runnable && $0.status == "PUBLISHED_PROTOCOL" }
            demo = try await samples.items
            error = nil
        } catch {
            self.error = "서버 연결에 실패했습니다. 기존 운동 기록은 기기에 보관됩니다."
        }
    }

    private func load(_ path: String) async throws -> CatalogResponse {
        let (data, _) = try await URLSession.shared.data(from: baseURL.appendingPathComponent(path))
        let decoder = JSONDecoder()
        return try decoder.decode(CatalogResponse.self, from: data)
    }
}
