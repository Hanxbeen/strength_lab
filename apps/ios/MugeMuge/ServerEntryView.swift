import SwiftUI

struct ServerEntryView:View {
    let item:RoutineValue
    var existingID:String? = nil
    @EnvironmentObject private var auth:CloudAuth
    @Environment(\.scenePhase) private var scenePhase
    @StateObject private var request=RoutineRequestState()
    @State private var sessionID=UUID().uuidString
    @State private var record:RoutineValue = .null
    @AppStorage("displayUnit") private var unit:MassUnit = .kg
    @State private var age=""
    @State private var pain=""
    @State private var restriction=""
    @State private var equipment=false
    @State private var limits=false
    @State private var lesson="squat"
    @State private var reps=""
    @State private var control=""
    @State private var effort=""
    @State private var observedPain=""
    @State private var load=""
    @State private var loadChecks=false
    @State private var pendingPath:String?
    @State private var pending:RoutineValue?
    private var definition:RoutineValue { item["definition"] }
    private var execution:RoutineValue { record["execution"] }
    private var base:String { "/v3/entry/learning-sessions/" + RoutineAPI.component(sessionID) }
    private var active:Bool { execution["state"].text=="active" }
    var body:some View {
        ScrollView {
            VStack(alignment:.leading,spacing:MugeStyle.Space.section) {
                Text(definition["title"].text).font(MugeStyle.TypeStyle.section)
                Text("가벼운 동작부터 익혀요. 앱이 자세를 판정하거나 최대 중량을 측정하지는 않아요.")
                    .foregroundStyle(MugeStyle.muted)
                if let error=request.error { Text(error).foregroundStyle(MugeStyle.danger) }
                if pending != nil {
                    if request.definitiveFailure {
                        Button("입력 다시 확인") { pending=nil }
                    }
                    Button("같은 요청 다시 확인") { Task{await retry()} }.buttonStyle(MugePrimaryButtonStyle()).disabled(request.busy)
                }
                if record == .null {
                    MugeCard {
                        RoutineInputField(key:"age",value:$age)
                        RoutineInputField(key:"current_pain",value:$pain)
                        RoutineInputField(key:"exercise_restriction",value:$restriction)
                        Toggle("장비와 주변 공간을 확인했어요",isOn:$equipment)
                        Toggle("자세가 불확실하면 도움을 요청할게요",isOn:$limits)
                        Button("동작 연습 시작") { start() }.buttonStyle(MugePrimaryButtonStyle())
                            .disabled(request.busy || pending != nil || age.isEmpty || pain.isEmpty || restriction.isEmpty || !equipment || !limits)
                    }
                } else if active {
                    Picker("동작",selection:$lesson) {
                        ForEach(definition["lessons"].array.indices,id: \.self) { i in
                            let row=definition["lessons"].array[i];Text(row["title"].text).tag(row["id"].text)
                        }
                    }
                    if let row=definition["lessons"].array.first(where:{$0["id"].text==lesson}) {
                        MugeCard {
                            ForEach(row["steps"].array.indices,id: \.self) { i in Text("\(i+1). \(row["steps"].array[i].text)") }
                            if let url=URL(string:row["demonstration"]["url"].text),url.scheme=="https" { Link("동작 설명·시연 보기",destination:url) }
                            Text("편한 범위에서 연습해요. 멈춰도 괜찮아요.").font(MugeStyle.TypeStyle.detail)
                        }
                        MugeCard {
                            TextField("실제로 한 횟수",text:$reps).keyboardType(.numberPad).textFieldStyle(.roundedBorder)
                            Picker("동작 조절",selection:$control) {
                                Text("선택해 주세요").tag("");Text("조절했어요").tag("controlled")
                                Text("잘 모르겠어요").tag("uncertain");Text("조절하지 못했어요").tag("lost")
                            }
                            Picker("힘든 정도",selection:$effort) {
                                Text("선택해 주세요").tag("");Text("쉬웠어요").tag("easy")
                                Text("보통").tag("moderate");Text("힘들었어요").tag("hard");Text("모르겠어요").tag("unknown")
                            }
                            RoutineInputField(key:"current_pain",value:$observedPain)
                            Button("맨몸 연습 기록") { observe(loaded:false) }.buttonStyle(MugePrimaryButtonStyle())
                            DisclosureGroup("첫 중량을 이미 연습할 준비가 됐다면") {
                                Text("동작을 모르면 중량을 들기 전에 도움을 요청해 주세요. 가벼운 도구를 직접 고르고, 5회가 편했는지 기록해요.")
                                if let url=URL(string:row["barbell_demonstration"].text),url.scheme=="https" { Link("바벨 동작과 장비 사용법",destination:url) }
                                TextField("직접 고른 가벼운 중량 (\(unit.rawValue))",text:$load).keyboardType(.decimalPad)
                                Toggle("동작 설명·장비·안전 지원을 확인했고 가벼운 도구를 골랐어요",isOn:$loadChecks)
                                Button("중량 연습 기록") { observe(loaded:true) }.disabled(!loadChecks)
                            }
                        }.disabled(request.busy || pending != nil || execution["active_rest"] != .null)
                    }
                    Button(execution["active_rest"] == .null ? "휴식 시작" : "휴식 끝") {
                        event(execution["active_rest"] == .null ? "rest_start" : "rest_end",[:])
                    }.disabled(request.busy || pending != nil)
                    Text("연습 기록 \(execution["observations"].array.count)개 · 휴식 \(execution["rests"].array.count)회")
                    Button("학습 마치기") { event("finish",["outcome":.string("completed")]) }
                        .buttonStyle(MugePrimaryButtonStyle()).disabled(request.busy || pending != nil)
                    Button("여기서 중단") { event("interrupt",["reason":.string("user_interruption")]) }.disabled(request.busy || pending != nil)
                } else {
                    Text(execution["state"].text=="completed" ? "연습 기록을 저장했어요" : "연습을 중단했어요").font(MugeStyle.TypeStyle.section)
                    Text("자세가 불확실하거나 통증이 있었다면 중량 훈련 전에 도움을 요청해 주세요.")
                    ForEach(execution["candidate_working_loads"].object.keys.sorted(),id: \.self) { exercise in
                        Text("\(RoutinePresentation.exercise(exercise)) · \(execution["candidate_working_loads"][exercise]["weight_kg"].number.map { unit.label($0) } ?? "미입력") 연습 기록")
                    }
                    Text("이 기록은 1RM이나 자세 인증이 아니에요. 초급 루틴은 독립 수행과 작업 중량 확인이 필요해요.")
                }
            }.padding(MugeStyle.Space.page)
        }.background(MugeStyle.canvas).navigationTitle("처음 시작하기")
            .task {
                if let existingID {
                    sessionID=existingID
                    await request.run { record=try await request.call(auth,base) }
                    if active { await reconcile() }
                }
                while !Task.isCancelled {
                    do { try await Task.sleep(for:.seconds(30)) } catch { break }
                    if active && pending == nil && scenePhase == .active { await reconcile() }
                }
            }
            .onChange(of:scenePhase) { _,phase in
                if phase == .active && active && pending == nil { Task { await reconcile() } }
            }
    }
    private func reconcile() async {
        await request.run {
            record = try await request.call(auth,base+"/reconcile",.object([:]))
        }
    }
    private func start() {
        guard let n=Double(age),n.isFinite else{return}
        pendingPath="/v3/entry/learning-sessions"
        pending = .object(["id":.string(sessionID),"source_id":item["source_id"],"source_version":item["version"],
            "started_at":.string(RoutineAPI.timestamp()),"profile":.object(["age":.number(n),"current_pain":.bool(pain=="true"),"exercise_restriction":.bool(restriction=="true")]),
            "setup":.object(["equipment_checked":.bool(equipment),"accept_self_report_limits":.bool(limits)])])
        Task{await retry()}
    }
    private func observe(loaded:Bool) {
        guard let n=Int(reps),!control.isEmpty,!effort.isEmpty,!observedPain.isEmpty else{return}
        var value:[String:RoutineValue] = ["lesson_id":.string(lesson),"reps":.number(Double(n)),
            "control":.string(control),"effort":.string(effort),"pain":.bool(observedPain=="true")]
        if loaded {
            guard let weight=Double(load),weight.isFinite,weight>0,loadChecks else{return}
            value.merge(["value":.number(weight),"unit":.string(unit.rawValue),"lift_instruction_reviewed":.bool(true),
                "equipment_checked":.bool(true),"safety_support_ready":.bool(true),"light_implement_selected":.bool(true)]) { _,new in new }
        }
        event(loaded ? "load_trial":"practice_observation",value)
    }
    private func event(_ type:String,_ data:[String:RoutineValue]) {
        guard pending==nil,!request.busy else{return}
        var value=data;value["id"] = .string(UUID().uuidString);value["type"] = .string(type);value["at"] = .string(RoutineAPI.timestamp())
        pendingPath=base+"/events";pending = .object(["expected_revision":execution["revision"],"event":.object(value)])
        Task{await retry()}
    }
    private func retry() async {
        await request.run {
            guard let path=pendingPath,let body=pending else{return}
            record=try await request.call(auth,path,body);pending=nil;pendingPath=nil
        }
    }
}
