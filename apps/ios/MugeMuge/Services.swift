import Foundation
import Combine

enum WorkoutStoreError: LocalizedError {
    case invalidSet
    case saveFailed
    var errorDescription: String? {
        switch self {
        case .invalidSet: return "중량과 반복 횟수를 확인해주세요."
        case .saveFailed: return "운동 기록 저장에 실패했습니다. 저장 공간을 확인해주세요."
        }
    }
}

@MainActor
final class WorkoutStore: ObservableObject {
    @Published private(set) var logs: [LoggedSet] = []
    @Published private(set) var lastError: String?
    private let url: URL

    init(filename: String = "workout-logs.json", directory: URL? = nil) {
        let folder = directory ?? FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
        try? FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
        url = folder.appendingPathComponent(filename)
        if let data = try? Data(contentsOf: url),
           let saved = try? JSONDecoder().decode([LoggedSet].self, from: data) {
            logs = saved
        }
    }

    @discardableResult
    func append(exerciseID: String, weightKg: Double, reps: Int) -> Bool {
        guard !exerciseID.isEmpty, weightKg >= 0, weightKg <= 2000, weightKg.isFinite,
              reps > 0, reps <= 100 else {
            lastError = WorkoutStoreError.invalidSet.localizedDescription
            return false
        }
        var next = logs
        next.append(LoggedSet(exerciseID: exerciseID, weightKg: weightKg, reps: reps))
        return persist(next)
    }

    func delete(id: UUID) {
        persist(logs.filter { $0.id != id })
    }

    func records(for exerciseID: String) -> [LoggedSet] {
        logs.filter { $0.exerciseID == exerciseID }.sorted { $0.performedAt < $1.performedAt }
    }

    @discardableResult
    private func persist(_ next: [LoggedSet]) -> Bool {
        do {
            let data = try JSONEncoder().encode(next)
            try data.write(to: url, options: .atomic)
            logs = next
            lastError = nil
            return true
        } catch {
            lastError = WorkoutStoreError.saveFailed.localizedDescription
            return false
        }
    }
}

@MainActor
final class CatalogStore: ObservableObject {
    @Published private(set) var protocols: [TrainingProtocol] = []
    @Published private(set) var demo: [TrainingProtocol] = []
    @Published private(set) var error: String?

    // The URL is configurable at build time; no localhost hardcoding for a shipped app.
    private let baseURL: URL?
    init() {
        baseURL = Bundle.main.object(forInfoDictionaryKey: "MugeMugeAPIURL")
            .flatMap { $0 as? String }.flatMap(URL.init(string:))
    }

    func refresh() async {
        guard let baseURL else {
            protocols = []
            demo = Self.bundledDemo()
            error = nil
            return
        }
        guard baseURL.scheme == "https" || (baseURL.host == "127.0.0.1" && baseURL.scheme == "http") else {
            error = "HTTPS API 주소가 필요합니다."
            return
        }
        do {
            async let published = load("/v1/protocols", baseURL: baseURL)
            async let samples = load("/v1/demo-protocols", baseURL: baseURL)
            let (catalog, preview) = try await (published, samples)
            protocols = catalog.items.filter { $0.runnable && $0.status == "PUBLISHED_PROTOCOL" }
            demo = preview.items.filter { $0.status == "DEMO_ONLY" && !$0.runnable }
            error = nil
        } catch {
            protocols = []
            demo = Self.bundledDemo()
            self.error = "서버 연결에 실패했습니다. 체험 루틴과 기존 기록은 오프라인에서 이용할 수 있습니다."
        }
    }

    private func load(_ path: String, baseURL: URL) async throws -> CatalogResponse {
        var request = URLRequest(url: baseURL.appendingPathComponent(String(path.dropFirst())))
        request.timeoutInterval = 12
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let response = response as? HTTPURLResponse, response.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }
        return try JSONDecoder().decode(CatalogResponse.self, from: data)
    }

    private static func bundledDemo() -> [TrainingProtocol] {
        guard let url = Bundle.main.url(forResource: "demo-catalog", withExtension: "json"),
              let data = try? Data(contentsOf: url),
              let response = try? JSONDecoder().decode(CatalogResponse.self, from: data) else {
            return []
        }
        return response.items.filter { $0.status == "DEMO_ONLY" && !$0.runnable }
    }
}
