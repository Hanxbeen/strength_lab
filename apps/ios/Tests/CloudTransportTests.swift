import Foundation

// Foundation-only URLProtocol mocks exercise HTTP auth and conflict handling without a device.
final class StubProtocol: URLProtocol {
    static var status = 200
    static var body = Data()
    static var lastRequest: URLRequest?
    override class func canInit(with request: URLRequest) -> Bool { true }
    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }
    override func startLoading() {
        Self.lastRequest = request
        client?.urlProtocol(self, didReceive: HTTPURLResponse(url: request.url!, statusCode: Self.status, httpVersion: nil, headerFields: nil)!, cacheStoragePolicy: .notAllowed)
        client?.urlProtocol(self, didLoad: Self.body)
        client?.urlProtocolDidFinishLoading(self)
    }
    override func stopLoading() {}
}

@main struct CloudTransportTests {
    static func main() async throws {
        let config = URLSessionConfiguration.ephemeral
        config.protocolClasses = [StubProtocol.self]
        let session = URLSession(configuration: config)
        let transport = CloudTransport(baseURL: URL(string: "https://example.test")!, publishableKey: "test-publishable", session: session)
        let user = UUID()
        StubProtocol.status = 200
        StubProtocol.body = Data("[]".utf8)
        let empty = try await transport.fetch(userID: user, accessToken: "test-jwt")
        precondition(empty == nil, "Empty response should be nil")
        precondition(StubProtocol.lastRequest?.value(forHTTPHeaderField: "apikey") == "test-publishable")
        precondition(StubProtocol.lastRequest?.value(forHTTPHeaderField: "Authorization") == "Bearer test-jwt")
        precondition(StubProtocol.lastRequest?.url?.absoluteString.contains("user_id=eq.") == true)
        let payload = CloudPayload(schemaVersion: 1, logs: [], active: nil, history: [], measuredMaxes: [])
        StubProtocol.status = 200
        StubProtocol.body = Data("1".utf8)
        let revision = try await transport.save(payload, expectedRevision: nil, accessToken: "test-jwt")
        precondition(revision == 1)
        precondition(StubProtocol.lastRequest?.httpMethod == "POST")
        StubProtocol.status = 409
        StubProtocol.body = Data(#"{"code":"40001","message":"conflict"}"#.utf8)
        do {
            _ = try await transport.save(payload, expectedRevision: 1, accessToken: "test-jwt")
            fatalError("Conflict must throw")
        } catch CloudTransportError.conflict {}
        StubProtocol.status = 401
        StubProtocol.body = Data("[]".utf8)
        do {
            _ = try await transport.fetch(userID: user, accessToken: "expired")
            fatalError("Unauthorized must throw")
        } catch CloudTransportError.unauthorized {}
        print("Cloud transport tests: 6 assertions passed")
    }
}
