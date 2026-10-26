import Foundation
final class RoutineStub:URLProtocol {
    static var status=200
    static var body=Data("{}".utf8)
    static var last:URLRequest?
    static var calls=0
    override class func canInit(with request:URLRequest)->Bool { true }
    override class func canonicalRequest(for request:URLRequest)->URLRequest { request }
    override func startLoading() {
        Self.calls+=1;Self.last=request
        client?.urlProtocol(self,didReceive:HTTPURLResponse(url:request.url!,statusCode:Self.status,httpVersion:nil,headerFields:nil)!,cacheStoragePolicy:.notAllowed)
        client?.urlProtocol(self,didLoad:Self.body);client?.urlProtocolDidFinishLoading(self)
    }
    override func stopLoading() {}
}
@main struct RoutineAPITests {
    static func main() async throws {
        let configuration=URLSessionConfiguration.ephemeral;configuration.protocolClasses=[RoutineStub.self]
        let api=RoutineAPI(baseURL:URL(string:"https://example.test")!,session:URLSession(configuration:configuration))
        RoutineStub.body=Data(#"{"revision":0,"actual":null,"pain":false}"#.utf8)
        let value=try await api.send("/v3/programme-instances/test/next-session?at=2026-10-26T09:00:00Z",token:"test-jwt")
        precondition(value["revision"].number==0 && value["actual"] == .null && value["pain"] == .bool(false))
        precondition(RoutineStub.last?.url?.path=="/v3/programme-instances/test/next-session")
        precondition(URLComponents(url:RoutineStub.last!.url!,resolvingAgainstBaseURL:false)?.queryItems?.first?.value=="2026-10-26T09:00:00Z")
        precondition(RoutineStub.last?.value(forHTTPHeaderField:"Authorization")=="Bearer test-jwt")
        let body:RoutineValue = .object(["expected_revision":.number(0),"event":.object(["id":.string("immutable-event")])])
        _ = try await api.send("/v2/workouts/a/events",token:"test-jwt",body:body)
        precondition(RoutineStub.last?.httpMethod=="POST")
        RoutineStub.status=409;let before=RoutineStub.calls
        do { _ = try await api.send("/v2/workouts/a/events",token:"test-jwt",body:body);fatalError("409 must fail") } catch RoutineAPIError.conflict {}
        precondition(RoutineStub.calls==before+1,"Never automatically retry mutations")
        RoutineStub.status=401
        do { _ = try await api.send("/v3/routines",token:"expired");fatalError("401 must fail") } catch RoutineAPIError.login {}
        do { _ = try await api.send("/v3/routines",token:"");fatalError("Missing token must fail") } catch RoutineAPIError.login {}
        let owner=UUID(),other=UUID()
        defer { try? FileManager.default.removeItem(at:RoutineOutbox.file(owner));try? FileManager.default.removeItem(at:RoutineOutbox.file(other)) }
        try RoutineOutbox.retain(owner,path:"/v2/workouts/a/events",body:body)
        try RoutineOutbox.retain(owner,path:"/v2/workouts/a/events",body:body)
        let saved=try RoutineOutbox.read(owner),isolated=try RoutineOutbox.read(other)
        precondition(saved.count==1 && saved[0].body==body && isolated.isEmpty)
        do { try RoutineOutbox.retain(owner,path:"/v2/workouts/a/events",body:.null);fatalError("Must preserve unresolved write") } catch RoutineAPIError.conflict {}
        try RoutineOutbox.acknowledge(owner,path:"/v2/workouts/a/events",body:body)
        let cleared=try RoutineOutbox.read(owner);precondition(cleared.isEmpty)
        print("Routine API transport: auth, nulls, query, revision and no blind retries passed")
    }
}
