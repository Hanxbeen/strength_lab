import Foundation

/// Preserves the versioned API's source and actual-data fields without coercing null into zero.
enum RoutineValue: Codable, Equatable {
    case object([String: RoutineValue]), array([RoutineValue]), string(String), number(Double), bool(Bool), null
    init(from decoder: Decoder) throws {
        let c = try decoder.singleValueContainer()
        if c.decodeNil() { self = .null }
        else if let v = try? c.decode(Bool.self) { self = .bool(v) }
        else if let v = try? c.decode(Double.self) { self = .number(v) }
        else if let v = try? c.decode(String.self) { self = .string(v) }
        else if let v = try? c.decode([String: RoutineValue].self) { self = .object(v) }
        else { self = .array(try c.decode([RoutineValue].self)) }
    }
    func encode(to encoder: Encoder) throws {
        var c = encoder.singleValueContainer()
        switch self {
        case .object(let v): try c.encode(v)
        case .array(let v): try c.encode(v)
        case .string(let v): try c.encode(v)
        case .number(let v): try c.encode(v)
        case .bool(let v): try c.encode(v)
        case .null: try c.encodeNil()
        }
    }
    subscript(_ key: String) -> RoutineValue { object[key] ?? .null }
    var object: [String: RoutineValue] { if case .object(let v) = self { return v }; return [:] }
    var array: [RoutineValue] { if case .array(let v) = self { return v }; return [] }
    var text: String { if case .string(let v) = self { return v }; return "" }
    var number: Double? { if case .number(let v) = self { return v }; return nil }
    var flag: Bool { self == .bool(true) }
    var display: String { number.map { $0.formatted(.number.precision(.fractionLength(0...2))) } ?? text }
}

enum RoutineAPIError: LocalizedError {
    case configuration, login, conflict, server(Int, String), invalidResponse
    var errorDescription: String? {
        switch self {
        case .configuration: return "테스트 서버 주소가 설정되지 않았어요."
        case .login: return "다시 로그인해 주세요."
        case .conflict: return "기록이 변경됐어요. 최신 기록을 불러온 뒤 확인해 주세요."
        case .server(let status, let code):
            return status == 503 ? "운동 서버에 연결하지 못했어요. 입력은 유지했어요." :
                "입력이나 현재 운동 상태를 확인해 주세요. (\(code))"
        case .invalidResponse: return "운동 정보를 확인하지 못했어요."
        }
    }
}

struct RoutineAPI {
    let baseURL: URL
    var session: URLSession = .shared
    static func configured() throws -> RoutineAPI {
        guard let value = Bundle.main.object(forInfoDictionaryKey: "MugeMugeAPIURL") as? String,
              let url = URL(string: value), url.scheme == "https", url.host != nil,
              url.user == nil, url.password == nil, url.query == nil, url.fragment == nil else {
            throw RoutineAPIError.configuration
        }
        return RoutineAPI(baseURL: url)
    }
    func send(_ path: String, token: String, body: RoutineValue? = nil) async throws -> RoutineValue {
        guard !token.isEmpty else { throw RoutineAPIError.login }
        guard path.hasPrefix("/v2/") || path.hasPrefix("/v3/"),
              !path.contains(".."), !path.contains("://") else { throw RoutineAPIError.configuration }
        let parts = path.split(separator: "?", maxSplits: 1, omittingEmptySubsequences: false)
        guard var components = URLComponents(url: baseURL.appendingPathComponent(String(parts[0].dropFirst())), resolvingAgainstBaseURL: false) else { throw RoutineAPIError.configuration }
        if parts.count == 2 { components.percentEncodedQuery = String(parts[1]) }
        guard let url = components.url else { throw RoutineAPIError.configuration }
        var request = URLRequest(url: url)
        request.httpMethod = body == nil ? "GET" : "POST"
        request.timeoutInterval = 30
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let body { request.httpBody = try JSONEncoder().encode(body) }
        let (data, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse else { throw RoutineAPIError.invalidResponse }
        if http.statusCode == 401 { throw RoutineAPIError.login }
        if http.statusCode == 409 { throw RoutineAPIError.conflict }
        let value = try? JSONDecoder().decode(RoutineValue.self, from: data)
        guard (200...299).contains(http.statusCode) else {
            throw RoutineAPIError.server(http.statusCode, value?["detail"]["code"].text ?? "")
        }
        guard let value else { throw RoutineAPIError.invalidResponse }
        return value
    }
    static func timestamp() -> String { ISO8601DateFormatter().string(from: Date()) }
    static func component(_ id: String) -> String {
        id.addingPercentEncoding(withAllowedCharacters: .alphanumerics) ?? ""
    }
}

enum RoutinePresentation {
    static func exercise(_ id: String) -> String {
        ["barbell_back_squat":"스쿼트", "barbell_bench_press":"벤치프레스",
         "barbell_deadlift":"데드리프트", "barbell_overhead_press":"오버헤드프레스",
         "barbell_front_squat":"프런트스쿼트", "sit_to_stand":"의자에서 일어나기",
         "wall_press_up":"벽 밀기", "wall_hip_hinge":"엉덩이 뒤로 보내기"][id] ?? id
    }
    static func level(_ id: String) -> String {
        ["entry":"입문", "foundation":"초급", "trained":"중급", "experienced":"숙련"][id] ?? id
    }
    static let fieldLabels = [
        "age":"나이", "independent_sbd":"SBD 동작을 독립적으로 수행할 수 있나요?",
        "independent_ohp":"오버헤드프레스를 독립적으로 수행할 수 있나요?",
        "current_pain":"현재 통증이 있나요?", "exercise_restriction":"현재 운동 제한이 있나요?",
        "training_months":"근력훈련 경험 (개월)", "training_years":"근력훈련 경험 (년)",
        "powerlifting_years":"파워리프팅 경험 (년)", "rpe_training_years":"RPE 활용 경험 (년)",
        "sex":"연구 대상 비교용 성별", "body_mass_kg":"체중 (kg)", "healthy":"연구의 건강 조건에 해당하나요?",
        "lifts_weekly_last_6_months":"최근 6개월 매주 해당 운동을 했나요?",
        "raw_powerlifting":"장비 보조 없는 파워리프팅을 하나요?",
        "daily_max_training_last_12_weeks":"최근 12주 데일리 맥스 훈련을 했나요?",
        "independent_front_squat":"프런트스쿼트를 독립적으로 수행할 수 있나요?",
        "rpe_familiarized":"RPE를 이해하고 사용해 본 적이 있나요?",
        "prior_moderate_high_load_training":"중·고중량 훈련 경험이 있나요?",
        "rest_seconds":"세트 사이 휴식 (초)", "between_exercise_rest_seconds":"종목 사이 휴식 (초)",
        "equipment_step_kg":"사용 가능한 중량 간격 (kg)", "warmup":"준비운동 계획",
        "accept_scope_limits":"적용 조건과 한계를 확인했어요", "accept_adaptations":"연구와 달라진 구성을 확인했어요",
        "accept_source_discrepancy":"본문과 보충표의 종목 차이를 확인했어요"
    ]
    static let numeric = Set(["age","training_months","training_years","powerlifting_years",
        "rpe_training_years","body_mass_kg","rest_seconds","between_exercise_rest_seconds","equipment_step_kg"])
    static let hidden = Set(["mode","adaptation_id","exercise_mapping","starting_loads_kg","starting_load_origins"])
}


/// Account-scoped write-ahead requests. No tokens; exact IDs/revisions survive termination.
struct RoutinePendingWrite:Codable,Identifiable {
    let path:String
    let body:RoutineValue
    var id:String { path }
}
enum RoutineOutbox {
    static func file(_ owner:UUID) throws -> URL {
        let directory=try FileManager.default.url(for:.applicationSupportDirectory,in:.userDomainMask,appropriateFor:nil,create:true)
            .appendingPathComponent("RoutinePendingWrites",isDirectory:true)
        try FileManager.default.createDirectory(at:directory,withIntermediateDirectories:true)
        return directory.appendingPathComponent(owner.uuidString.lowercased()+".json")
    }
    static func read(_ owner:UUID) throws -> [RoutinePendingWrite] {
        let url=try file(owner)
        guard FileManager.default.fileExists(atPath:url.path) else{return []}
        return try JSONDecoder().decode([RoutinePendingWrite].self,from:Data(contentsOf:url))
    }
    static func retain(_ owner:UUID,path:String,body:RoutineValue) throws {
        var rows=try read(owner)
        if let old=rows.first(where:{$0.path==path}) {
            guard old.body==body else{throw RoutineAPIError.conflict}
            return
        }
        rows.append(RoutinePendingWrite(path:path,body:body))
        try JSONEncoder().encode(rows).write(to:file(owner),options:.atomic)
    }
    static func acknowledge(_ owner:UUID,path:String,body:RoutineValue) throws {
        let rows=try read(owner).filter { !($0.path==path && $0.body==body) }
        try JSONEncoder().encode(rows).write(to:file(owner),options:.atomic)
    }
    static func isMutation(_ path:String)->Bool {
        !path.contains("/preview") && !path.contains("readiness") && !path.hasSuffix("/reconcile")
    }
}
