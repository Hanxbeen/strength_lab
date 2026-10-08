import Foundation

/// A deliberately conservative cloud transport: no automatic overwrite and no credentials in source.
struct CloudSnapshot: Decodable {
    let revision: Int64
    let payload: CloudPayload
}
struct CloudPayload: Codable {
    let schemaVersion: Int
    let logs: [LoggedSet]
    let active: ActiveWorkout?
    let history: [ActiveWorkout]
    let measuredMaxes: [MeasuredMax]
}
enum CloudTransportError: LocalizedError {
    case unauthorized, conflict, invalidResponse, server(Int)
    var errorDescription: String? {
        switch self {
        case .unauthorized: return "로그인 세션이 만료됐습니다."
        case .conflict: return "다른 기기의 기록이 변경됐습니다. 덮어쓰지 않고 동기화를 중단했습니다."
        case .invalidResponse: return "서버 응답을 확인할 수 없습니다."
        case .server(let status): return "클라우드 요청 실패 (HTTP \(status))"
        }
    }
}
struct CloudTransport {
    let baseURL: URL
    let publishableKey: String
    let session: URLSession

    init(baseURL: URL, publishableKey: String, session: URLSession = .shared) {
        self.baseURL = baseURL
        self.publishableKey = publishableKey
        self.session = session
    }

    private func request(path: String, token: String, method: String) -> URLRequest {
        var req = URLRequest(url: baseURL.appendingPathComponent(path))
        req.httpMethod = method
        req.setValue(publishableKey, forHTTPHeaderField: "apikey")
        req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        return req
    }

    func fetch(userID: UUID, accessToken: String) async throws -> CloudSnapshot? {
        var req = request(path: "rest/v1/workout_snapshots", token: accessToken, method: "GET")
        var components = URLComponents(url: req.url!, resolvingAgainstBaseURL: false)!
        components.queryItems = [
            URLQueryItem(name: "select", value: "revision,payload"),
            URLQueryItem(name: "user_id", value: "eq.\(userID.uuidString.lowercased())"),
            URLQueryItem(name: "limit", value: "1")
        ]
        req.url = components.url
        let (data, response) = try await session.data(for: req)
        try check(response)
        return try JSONDecoder().decode([CloudSnapshot].self, from: data).first
    }

    /// expectedRevision=nil only creates a new snapshot; a non-nil revision uses CAS.
    /// HTTP 409/40001 conflict is NEVER retried blindly.
    func save(_ payload: CloudPayload, expectedRevision: Int64?,
              accessToken: String) async throws -> Int64 {
        var req = request(path: "rest/v1/rpc/save_workout_snapshot", token: accessToken, method: "POST")
        struct Body: Encodable {
            let expected_revision: Int64?
            let next_payload: CloudPayload
        }
        req.httpBody = try JSONEncoder().encode(Body(expected_revision: expectedRevision, next_payload: payload))
        let (data, response) = try await session.data(for: req)
        if let http = response as? HTTPURLResponse {
            if http.statusCode == 409 { throw CloudTransportError.conflict }
            if let text = String(data: data, encoding: .utf8), text.contains("40001") {
                throw CloudTransportError.conflict
            }
        }
        try check(response)
        guard let revision = try? JSONDecoder().decode(Int64.self, from: data) else {
            throw CloudTransportError.invalidResponse
        }
        return revision
    }

    private func check(_ response: URLResponse) throws {
        guard let http = response as? HTTPURLResponse else { throw CloudTransportError.invalidResponse }
        if http.statusCode == 401 || http.statusCode == 403 { throw CloudTransportError.unauthorized }
        guard (200...299).contains(http.statusCode) else {
            throw CloudTransportError.server(http.statusCode)
        }
    }
}
