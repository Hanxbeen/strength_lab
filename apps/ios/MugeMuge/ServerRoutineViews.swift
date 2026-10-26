import SwiftUI
import Combine
import Charts

@MainActor final class RoutineRequestState: ObservableObject {
    @Published var busy = false
    @Published var error: String?
    @Published var definitiveFailure = false
    func call(_ auth: CloudAuth, _ path: String, _ body: RoutineValue? = nil) async throws -> RoutineValue {
        guard let owner = auth.userID else { throw RoutineAPIError.login }
        let token = try await auth.accessToken()
        guard auth.userID == owner else { throw RoutineAPIError.login }
        let api = try RoutineAPI.configured()
        let mutation = body != nil && RoutineOutbox.isMutation(path)
        if mutation, let body { try RoutineOutbox.retain(owner,path:path,body:body) }
        let value:RoutineValue
        do { value = try await api.send(path, token: token, body: body) }
        catch {
            if let body, mutation {
                switch error {
                case RoutineAPIError.conflict:
                    try RoutineOutbox.acknowledge(owner,path:path,body:body)
                case RoutineAPIError.server(let status, _) where (400...499).contains(status):
                    try RoutineOutbox.acknowledge(owner,path:path,body:body)
                default: break
                }
            }
            throw error
        }
        if mutation, let body { try RoutineOutbox.acknowledge(owner,path:path,body:body) }
        guard auth.userID == owner else { throw RoutineAPIError.login }
        return value
    }
    func run(_ action: () async throws -> Void) async {
        guard !busy else { return };busy = true;error = nil;definitiveFailure = false
        defer { busy = false }
        do { try await action() } catch {
            self.error = error.localizedDescription
            switch error {
            case RoutineAPIError.conflict: definitiveFailure = true
            case RoutineAPIError.server(let status, _) where (400...499).contains(status): definitiveFailure = true
            default: break
            }
        }
    }
}

struct ServerRoutineLibrary: View {
    @EnvironmentObject private var auth: CloudAuth
    @StateObject private var request = RoutineRequestState()
    @State private var catalog: RoutineValue = .null
    @State private var instances: [RoutineValue] = []
    @State private var pendingWrites: [RoutinePendingWrite] = []
    @State private var learningSessions: [RoutineValue] = []
    @State private var level = "foundation"
    @State private var instanceCursor = ""
    @State private var learningCursor = ""
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: MugeStyle.Space.section) {
                if auth.userID == nil {
                    MugeCard {
                        Text("로그인하고 운동을 시작해요").font(MugeStyle.TypeStyle.section)
                        NavigationLink("로그인") { CloudAccountView() }.buttonStyle(MugePrimaryButtonStyle())
                    }
                } else {
                    if request.busy { ProgressView("운동 정보를 불러오고 있어요") }
                    if let error = request.error {
                        Text(error).foregroundStyle(MugeStyle.danger)
                        Button("다시 불러오기") { Task { await load() } }
                    }
                    if !pendingWrites.isEmpty {
                        MugeCard {
                            Text("저장을 확인할 기록이 있어요").font(MugeStyle.TypeStyle.card)
                            Text("이전에 보낸 내용 그대로 확인해요. 새 중량이나 횟수로 덮어쓰지 않아요.")
                            ForEach(pendingWrites) { row in
                                Button("미확인 저장 다시 확인") { Task { await request.run {
                                    _ = try await request.call(auth,row.path,row.body)
                                    if let owner = auth.userID { pendingWrites = try RoutineOutbox.read(owner) }
                                }} }.disabled(request.busy)
                            }
                        }
                    }
                    if !instances.isEmpty {
                        MugeCard {
                            Text("내 루틴").font(MugeStyle.TypeStyle.section)
                            ForEach(instances.indices, id: \.self) { i in
                                let item = instances[i]
                                NavigationLink {
                                    ServerProgrammeView(instanceID: item["instance_id"].text.isEmpty ? item["id"].text : item["instance_id"].text)
                                } label: {
                                    Text(catalog["routines"].array.first { $0["source_id"] == item["source_id"] }?["title"].text ?? "내 루틴 보기")
                                }
                            }
                        }
                    }
                    if !instanceCursor.isEmpty {
                        Button("내 루틴 더 보기") { Task { await request.run {
                            let page=try await request.call(auth,"/v3/programme-instances?after="+RoutineAPI.component(instanceCursor))
                            instances += page["items"].array;instanceCursor=page["next_cursor"].text
                        }} }.disabled(request.busy)
                    }
                    Picker("훈련 경험", selection: $level) {
                        ForEach(["entry","foundation","trained","experienced"], id: \.self) {
                            Text(RoutinePresentation.level($0)).tag($0)
                        }
                    }.pickerStyle(.segmented)
                    Text(level == "entry" ? "동작을 배우고 첫 중량을 기록해요" : "구성과 조건을 확인하고 선택해요")
                        .font(MugeStyle.TypeStyle.section)
                    if level == "entry" {
                        if let definition = catalog["learning_paths"].array.first {
                            ForEach(learningSessions.indices,id: \.self) { index in
                                let saved = learningSessions[index]
                                if saved["execution"]["programme_version"] == definition["version"] {
                                    NavigationLink("내 동작 연습 기록") { ServerEntryView(item:definition,existingID:saved["id"].text) }
                                }
                            }
                        }
                        ForEach(catalog["learning_paths"].array.indices, id: \.self) { i in
                            let item = catalog["learning_paths"].array[i]
                            NavigationLink { ServerEntryView(item: item) } label: {
                                MugeCard {
                                    Text(item["definition"]["title"].text).font(MugeStyle.TypeStyle.card)
                                    Text("동작 3종 · 자세 판정이나 1RM 측정은 아니에요")
                                        .font(MugeStyle.TypeStyle.detail).foregroundStyle(MugeStyle.muted)
                                }
                            }.buttonStyle(.plain)
                        }
                        if !learningCursor.isEmpty {
                            Button("학습 기록 더 보기") { Task { await request.run {
                                let page=try await request.call(auth,"/v3/entry/learning-sessions?after="+RoutineAPI.component(learningCursor))
                                learningSessions += page["items"].array;learningCursor=page["next_cursor"].text
                            }} }.disabled(request.busy)
                        }
                        if catalog["learning_paths"].array.isEmpty {
                            Text("입문 학습을 불러오지 못했어요. 다시 불러와 주세요.").foregroundStyle(MugeStyle.muted)
                        }
                    } else {
                        ForEach(options.indices, id: \.self) { i in
                            let item = options[i]
                            NavigationLink { ServerRoutineSetup(item: item) } label: {
                                MugeCard {
                                    Text(item["title"].text).font(MugeStyle.TypeStyle.card)
                                    Text("\(item["duration_weeks"].display)주 · \(item["training_sessions"].display)회")
                                    Text(item["exercise_ids"].array.map { RoutinePresentation.exercise($0.text) }.joined(separator: " · "))
                                        .font(MugeStyle.TypeStyle.detail).foregroundStyle(MugeStyle.muted)
                                    if item["prescription_basis"].text == "explicit_product_synthesis_not_trial_replication" {
                                        Text("논문 근거를 종합한 무게무게 구성").font(MugeStyle.TypeStyle.note)
                                    }
                                }
                            }.buttonStyle(.plain)
                        }
                    }
                }
            }.padding(MugeStyle.Space.page)
        }.background(MugeStyle.canvas).navigationTitle("루틴")
            .task(id: auth.userID) { await load() }.refreshable { await load() }
    }
    private var options: [RoutineValue] {
        catalog["routines"].array.filter { $0["availability"]["experience_context"].text == level }
    }
    private func load() async {
        guard auth.userID != nil else { catalog = .null;instances = [];return }
        await request.run {
            if let owner = auth.userID { pendingWrites = try RoutineOutbox.read(owner) }
            catalog = try await request.call(auth, "/v3/routines")
            let programmes=try await request.call(auth,"/v3/programme-instances")
            instances=programmes["items"].array;instanceCursor=programmes["next_cursor"].text
            let learning=try await request.call(auth,"/v3/entry/learning-sessions")
            learningSessions=learning["items"].array;learningCursor=learning["next_cursor"].text
        }
    }
}

struct RoutineInputField: View {
    let key: String
    @Binding var value: String
    var massUnit: MassUnit = .kg
    var body: some View {
        let title = (RoutinePresentation.fieldLabels[key] ?? key).replacingOccurrences(of:"(kg)",with:"(\(massUnit.rawValue))")
        if RoutinePresentation.numeric.contains(key) || key == "warmup" {
            VStack(alignment: .leading) {
                Text(title).font(MugeStyle.TypeStyle.detail)
                TextField(title, text: $value).keyboardType(key == "warmup" ? .default : .decimalPad)
                    .textFieldStyle(.roundedBorder)
            }
        } else if key == "sex" {
            Picker(title, selection: $value) {
                Text("선택해 주세요").tag("")
                Text("남성").tag("male");Text("여성").tag("female")
            }
        } else {
            Picker(title, selection: $value) {
                Text("선택해 주세요").tag("");Text("예").tag("true");Text("아니요").tag("false")
            }
        }
    }
}

struct ServerRoutineSetup: View {
    let item: RoutineValue
    @EnvironmentObject private var auth: CloudAuth
    @StateObject private var request = RoutineRequestState()
    @State private var inputs: [String: String] = [:]
    @State private var loads: [String: String] = [:]
    @State private var maxes: [RoutineValue] = []
    @State private var maxIDs: [String: String] = [:]
    @State private var preview: RoutineValue = .null
    @State private var acceptedBody: RoutineValue?
    @State private var instanceID = UUID().uuidString
    @State private var created = false
    @State private var showMax = false
    @State private var entryCandidates:[RoutineValue] = []
    @State private var entryRefs:[String:RoutineValue] = [:]
    @AppStorage("displayUnit") private var unit:MassUnit = .kg
    private var fields: [String] { item["input_contract"]["required_fields"].array.map(\.text) }
    private var manual: Bool { fields.contains("setup.starting_loads_kg") }
    private var loadRequired: Bool { manual || item["arm"].text == "RPEG" || ["MAX","MAX_BOFF"].contains(item["arm"].text) }
    private var loadExercises: [String] {
        if manual { return item["exercise_ids"].array.map(\.text) }
        let first = item["sessions"].array.first ?? .null
        return (first["exercise_ids"].array.isEmpty ? first["exercises"].array : first["exercise_ids"].array).map(\.text)
    }
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: MugeStyle.Space.section) {
                Text(item["title"].text).font(MugeStyle.TypeStyle.section)
                MugeCard {
                    ForEach(item["limits"].array.indices, id: \.self) { Text(item["limits"].array[$0].text).font(MugeStyle.TypeStyle.detail) }
                    if let url = URL(string: item["definition"]["evidence"]["url"].text), url.scheme == "https" {
                        Link("근거 원문 보기", destination: url)
                    }
                }
                MugeCard {
                    Text("시작 조건").font(MugeStyle.TypeStyle.card)
                    ForEach(fields.filter { !RoutinePresentation.hidden.contains($0.components(separatedBy: ".").last ?? "") }, id: \.self) { field in
                        RoutineInputField(key: field.components(separatedBy: ".").last ?? field,
                            value: Binding(get: { inputs[field] ?? "" }, set: { inputs[field] = $0;preview = .null;acceptedBody = nil }),massUnit:unit)
                    }
                }
                if item["input_contract"]["max_record_ids_required"].flag {
                    MugeCard {
                        Text("측정한 최대 중량").font(MugeStyle.TypeStyle.card)
                        ForEach(item["input_contract"]["max_record_exercise_ids"].array.map(\.text), id: \.self) { exercise in
                            Picker(RoutinePresentation.exercise(exercise), selection: Binding(get: { maxIDs[exercise] ?? "" }, set: { maxIDs[exercise] = $0;preview = .null;acceptedBody = nil })) {
                                Text("기록 선택").tag("")
                                ForEach(maxes.filter { $0["exercise_id"].text == exercise }.indices, id: \.self) { index in
                                    let row = maxes.filter { $0["exercise_id"].text == exercise }[index]
                                    Text("\(row["weight_kg"].number.map { unit.label($0) } ?? "미입력") · \(row["measured_at"].text.prefix(10))").tag(row["id"].text)
                                }
                            }
                        }
                        Button("최대 중량 등록") { showMax = true }
                    }
                }
                if loadRequired {
                    MugeCard {
                        Text(manual ? "알고 있는 작업 중량 (\(unit.rawValue))" : "첫 회차에서 사용할 중량 (\(unit.rawValue))").font(MugeStyle.TypeStyle.card)
                        Text("앱이 중량을 추정하지 않아요. 동작과 중량을 모르면 입문 학습부터 확인해 주세요.")
                            .font(MugeStyle.TypeStyle.detail).foregroundStyle(MugeStyle.muted)
                        ForEach(loadExercises, id: \.self) { exercise in
                            TextField(RoutinePresentation.exercise(exercise), text: Binding(get: { loads[exercise] ?? "" }, set: { loads[exercise] = $0;entryRefs.removeValue(forKey:exercise);preview = .null;acceptedBody = nil }))
                                .keyboardType(.decimalPad).textFieldStyle(.roundedBorder)
                        }
                    }
                }
                if manual && item["definition"]["adapter_version"].text == "sbd-evidence-synthesis-v1" {
                    MugeCard {
                        Text("입문에서 연습한 중량 가져오기").font(MugeStyle.TypeStyle.card)
                        Text("완료한 학습의 편하게 수행한 기록만 보여요. 자세 인증이나 적합성 판정은 아니에요.")
                            .font(MugeStyle.TypeStyle.detail).foregroundStyle(MugeStyle.muted)
                        if entryCandidates.isEmpty { Text("가져올 완료 학습 기록이 없어요.") }
                        ForEach(entryCandidates.indices,id: \.self) { index in
                            let candidate=entryCandidates[index]
                            Button {
                                let exercise=candidate["exercise_id"].text
                                entryRefs[exercise]=candidate
                                loads[exercise]=candidate["weight_kg"].number.map{String(unit.display($0))} ?? ""
                                preview = .null;acceptedBody=nil
                            } label: {
                                Text("\(RoutinePresentation.exercise(candidate["exercise_id"].text)) · \(candidate["weight_kg"].number.map{unit.label($0)} ?? "") · \(candidate["at"].text.prefix(10))")
                            }
                        }
                        if !entryRefs.isEmpty {
                            Text("선택한 원기록을 함께 저장해요. 중량을 직접 수정하면 원기록 선택이 해제돼요.")
                                .font(MugeStyle.TypeStyle.note)
                        }
                    }
                }
                if let error = request.error { Text(error).foregroundStyle(MugeStyle.danger) }
                if preview != .null {
                    MugeCard {
                        Text(preview["message"].text)
                        ForEach(preview["missing_inputs"].array.indices, id: \.self) { i in
                            let field = preview["missing_inputs"].array[i]["field"].text.components(separatedBy: ".").last ?? ""
                            Text("필요한 입력: \(RoutinePresentation.fieldLabels[field] ?? field)")
                        }
                        if preview["session_status"].text == "ready" {
                            Text("첫 운동 · \(preview["session_preview"]["session"]["sets"].array.count)세트")
                            ForEach(preview["session_preview"]["session"]["sets"].array.indices, id: \.self) { i in
                                let row = preview["session_preview"]["session"]["sets"].array[i]
                                Text("\(RoutinePresentation.exercise(row["exercise_id"].text)) · \(row["weight_kg"].number.map { unit.label($0) } ?? "직접 선택") · \(row["reps"]["min"].display)회")
                                    .font(MugeStyle.TypeStyle.detail)
                            }
                        } else if !preview["session_blocking_code"].text.isEmpty {
                            Text("중량과 입력 조건을 다시 확인해 주세요. (\(preview["session_blocking_code"].text))")
                        }
                    }
                }
                Button("첫 운동 확인") { Task { await check() } }.buttonStyle(MugeSecondaryButtonStyle()).disabled(request.busy)
                if acceptedBody != nil {
                    Button("이 루틴 선택") { Task { await create() } }.buttonStyle(MugePrimaryButtonStyle()).disabled(request.busy)
                }
            }.padding(MugeStyle.Space.page)
        }.background(MugeStyle.canvas).navigationTitle("루틴 시작")
            .task { await loadMaxes();await loadEntryCandidates() }
            .sheet(isPresented: $showMax, onDismiss: { Task { await loadMaxes() } }) { NavigationStack { ServerMaxRegistration() } }
            .navigationDestination(isPresented: $created) { ServerProgrammeView(instanceID: instanceID) }
    }
    private func loadMaxes() async { await request.run { maxes = try await request.call(auth, "/v2/max-records")["items"].array } }
    private func loadEntryCandidates() async {
        guard item["definition"]["adapter_version"].text=="sbd-evidence-synthesis-v1" else{return}
        await request.run {
            var cursor="",seen=Set<String>(),collected:[RoutineValue]=[]
            repeat {
                let path="/v3/entry/learning-sessions" + (cursor.isEmpty ? "" : "?after="+RoutineAPI.component(cursor))
                let page=try await request.call(auth,path)
                for session in page["items"].array where session["execution"]["state"].text=="completed" {
                    for candidate in session["execution"]["candidate_working_loads"].object.values {
                        var value=candidate.object;value["workout_id"]=session["id"];collected.append(.object(value))
                    }
                }
                cursor=page["next_cursor"].text
                if !cursor.isEmpty && !seen.insert(cursor).inserted { throw RoutineAPIError.invalidResponse }
            } while !cursor.isEmpty
            entryCandidates=collected.sorted{$0["at"].text>$1["at"].text}
        }
    }
    private func requestBody() throws -> RoutineValue {
        var profile: [String: RoutineValue] = [:], setup: [String: RoutineValue] = ["mode":.string("user_selected_source")]
        for field in fields {
            let parts = field.components(separatedBy: ".");guard parts.count == 2 else { continue }
            let key = parts[1];if RoutinePresentation.hidden.contains(key) { continue }
            let raw = inputs[field] ?? "";if raw.isEmpty { continue }
            let value: RoutineValue
            if RoutinePresentation.numeric.contains(key) {
                guard let n = Double(raw), n.isFinite else { throw RoutineAPIError.server(422,"INVALID_NUMBER") }
                value = .number(["body_mass_kg","equipment_step_kg"].contains(key) ? unit.kilograms(n) : n)
            } else if raw == "true" || raw == "false" { value = .bool(raw == "true") }
            else { value = .string(raw) }
            if parts[0] == "profile" { profile[key] = value } else { setup[key] = value }
        }
        let engine = item["definition"]["adapter_version"].text
        if fields.contains("setup.adaptation_id") {
            setup["adaptation_id"] = engine == "sbd-evidence-synthesis-v1" ? item["source_id"] : item["definition"]["adaptations"].array.first?["id"] ?? .null
        }
        if fields.contains("setup.exercise_mapping") { setup["exercise_mapping"] = .string("source_labels_verified_formula_v1") }
        var chosen: [String: RoutineValue] = [:]
        for exercise in loadExercises {
            guard let n = Double(loads[exercise] ?? ""), n.isFinite, n > 0 else { throw RoutineAPIError.server(422,"WORKING_LOAD_REQUIRED") }
            chosen[exercise] = entryRefs[exercise]?["weight_kg"] ?? .number(unit.kilograms(n))
        }
        if manual {
            setup["starting_loads_kg"] = .object(chosen)
            var origins=chosen.mapValues { _ in RoutineValue.string("known_working_load") }
            var references:[String:RoutineValue]=[:]
            for (exercise,reference) in entryRefs {
                origins[exercise] = .string("self_reported_intro_trial")
                references[exercise] = .object(["workout_id":reference["workout_id"],"event_id":reference["event_id"]])
            }
            setup["starting_load_origins"] = .object(origins)
            if !references.isEmpty { setup["entry_trial_references"] = .object(references) }
        }
        var value: [String: RoutineValue] = ["source_id":item["source_id"],"source_version":item["source_version"],"arm":item["arm"],
            "created_at":.string(RoutineAPI.timestamp()),"profile":.object(profile),"setup":.object(setup),
            "max_record_ids":.object(maxIDs.filter { !$0.value.isEmpty }.mapValues { .string($0) })]
        if loadRequired {
            var daily = chosen
            if manual, let first = item["sessions"].array.first {
                let names = Set(first["exercises"].array.map(\.text))
                daily = chosen.filter { names.contains($0.key) }
            }
            value[manual ? "initial_loads_kg" : "initial_rpe_loads_kg"] = .object(daily)
        }
        return .object(value)
    }
    private func check() async {
        await request.run {
            let input = try requestBody()
            preview = try await request.call(auth, "/v3/routines/preview", input)
            acceptedBody = preview["can_create_instance"].flag && preview["session_status"].text == "ready" ? input : nil
        }
    }
    private func create() async {
        await request.run {
            guard let acceptedBody else { return }
            var input = acceptedBody.object;input["id"] = .string(instanceID)
            _ = try await request.call(auth,"/v3/programme-instances",.object(input));created = true
        }
    }
}

struct ServerMaxRegistration: View {
    @EnvironmentObject private var auth: CloudAuth
    @Environment(\.dismiss) private var dismiss
    @StateObject private var request = RoutineRequestState()
    @State private var exercise = "barbell_back_squat"
    @State private var value = ""
    @State private var unit = "kg"
    @State private var measured = Date()
    @State private var pending: RoutineValue?
    var body: some View {
        Form {
            Picker("종목", selection: $exercise) {
                ForEach(["barbell_back_squat","barbell_bench_press","barbell_deadlift"],id: \.self) { Text(RoutinePresentation.exercise($0)).tag($0) }
            }
            TextField("실제로 한 번 든 최대 중량",text:$value).keyboardType(.decimalPad)
            Picker("단위",selection:$unit) { Text("kg").tag("kg");Text("lb").tag("lb") }.pickerStyle(.segmented)
            DatePicker("측정일",selection:$measured,in:...Date(),displayedComponents:.date)
            Text("직접 측정한 기록을 등록해요. 새 최대 중량 측정을 요구하는 안내가 아니에요.")
            if let error = request.error { Text(error).foregroundStyle(MugeStyle.danger) }
            if request.definitiveFailure && pending != nil {
                Button("입력 다시 확인") { pending=nil }
            }
            Button(pending == nil ? "저장" : "같은 기록 다시 저장") {
                Task { await request.run {
                    if pending == nil {
                        guard let n = Double(value), n > 0, n.isFinite else { throw RoutineAPIError.server(422,"INVALID_MASS") }
                        pending = .object(["id":.string(UUID().uuidString),"exercise_id":.string(exercise),
                            "value":.number(n),"unit":.string(unit),"kind":.string("measured"),
                            "measured_at":.string(ISO8601DateFormatter().string(from:measured))])
                    }
                    _ = try await request.call(auth,"/v2/max-records",pending);dismiss()
                }}
            }.disabled(request.busy)
        }.navigationTitle("최대 중량 등록")
    }
}
