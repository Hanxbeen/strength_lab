import SwiftUI
import Charts

struct ServerProgrammeView: View {
    let instanceID: String
    @EnvironmentObject private var auth: CloudAuth
    @StateObject private var request = RoutineRequestState()
    @State private var record: RoutineValue = .null
    @AppStorage("displayUnit") private var unit:MassUnit = .kg
    @State private var next: RoutineValue = .null
    @State private var loads: [String:String] = [:]
    @State private var showEvaluation=false
    @State private var pending: RoutineValue?
    @State private var workoutID: String?
    private var base: String { "/v3/programme-instances/" + RoutineAPI.component(instanceID) }
    private var instance: RoutineValue { record["instance"] }
    private var manual: Bool { ["petrizzo-2018-v1","sbd-evidence-synthesis-v1"].contains(instance["source"]["adapter_version"].text) }
    private var rpeLoads: Bool { instance["arm"].text == "RPEG" || ["MAX","MAX_BOFF"].contains(instance["arm"].text) }
    private var exercises: [String] {
        if manual { return next["session_inputs"]["exercise_ids"].array.map(\.text) }
        if !rpeLoads { return [] }
        if instance["source"]["adapter_version"].text == "helms-2018-v1" { return ["barbell_back_squat","barbell_bench_press"] }
        let target = next["next_session"]
        return instance["source"]["protocol"]["sessions"].array.first {
            $0["week"] == target["week"] && $0["day"] == target["day"]
        }?["exercises"].array.map(\.text) ?? []
    }
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: MugeStyle.Space.section) {
                Text(instance["source"]["title"].text).font(MugeStyle.TypeStyle.section)
                if let error = request.error { Text(error).foregroundStyle(MugeStyle.danger) }
                if request.definitiveFailure && pending != nil {
                    Button("입력 다시 확인") { pending=nil }
                }
                if request.busy { ProgressView() }
                if next["state"].text == "workout_open" {
                    NavigationLink("진행 중인 운동 확인") { ServerWorkoutView(workoutID: next["workout_id"].text) }
                        .buttonStyle(MugePrimaryButtonStyle())
                } else if next["next_session"] != .null {
                    MugeCard {
                        Text("\(next["next_session"]["week"].display)주차 · \(next["next_session"]["day"].display)번째 운동").font(MugeStyle.TypeStyle.card)
                        if next["state"].text == "waiting_for_schedule" {
                            Text("다음 운동 가능 시각: \(next["earliest_start_at"].text)")
                        }
                        ForEach(exercises,id: \.self) { exercise in
                            TextField("\(RoutinePresentation.exercise(exercise)) (\(unit.rawValue))",
                                      text: Binding(get:{loads[exercise] ?? ""},set:{loads[exercise]=$0}))
                                .keyboardType(.decimalPad).textFieldStyle(.roundedBorder).disabled(pending != nil)

                        }
                        ForEach(next["session_inputs"]["load_selection"].array.indices,id: \.self) { i in
                            Text(next["session_inputs"]["load_selection"].array[i]["message"].text)
                                .font(MugeStyle.TypeStyle.detail).foregroundStyle(MugeStyle.muted)
                        }
                        Button(pending == nil ? "운동 시작" : "시작 요청 다시 확인") { Task { await start() } }
                            .buttonStyle(MugePrimaryButtonStyle())
                            .disabled(request.busy || next["state"].text != "schedule_available")
                    }
                } else if next != .null {
                    Text("이 루틴의 운동 회차를 모두 확인했어요. 아래에서 기록을 볼 수 있어요.")
                }
                if !record["history"].array.isEmpty {
                    MugeCard {
                        Text("운동 기록").font(MugeStyle.TypeStyle.card)
                        ForEach(record["history"].array.indices,id: \.self) { i in
                            let row = record["history"].array[i]
                            NavigationLink("\(row["week"].display)주차 · \(row["day"].display)번째 운동") {
                                ServerWorkoutView(workoutID:row["workout_id"].text)
                            }
                        }
                    }
                }
                if !record["history"].array.isEmpty && next["state"].text != "workout_open" && next["state"].text != "programme_closed" {
                    Button(next["state"].text == "awaiting_evaluation" ? "루틴 마무리":"이 루틴 종료") { showEvaluation=true }
                        .disabled(request.busy || pending != nil)
                }
                if next["state"].text == "programme_closed" {
                    Button("측정 기록 추가·비교") { showEvaluation=true }.disabled(request.busy)
                }
                ForEach(record["evaluations"].array.indices,id: \.self) { index in
                    let evaluation=record["evaluations"].array[index]
                    Text("저장한 기록: \(evaluation["training"]["closed_sessions"].display)회차 · 변경 세트 \(evaluation["training"]["changed_sets"].display)개 · 휴식 \(evaluation["training"]["rest_count"].display)회")
                        .font(MugeStyle.TypeStyle.detail)
                }
                Button("새로 확인") { Task { await load() } }.disabled(request.busy)
            }.padding(MugeStyle.Space.page)
        }.background(MugeStyle.canvas).navigationTitle("내 루틴")
            .task { await load() }
            .sheet(isPresented:$showEvaluation,onDismiss:{ Task { await load() } }) {
                NavigationStack {
                    ServerProgrammeEvaluation(instanceID:instanceID,record:record,
                        outcome:next["state"].text == "awaiting_evaluation" ? "completed" : "stopped")
                }
            }
            .navigationDestination(isPresented:Binding(get:{workoutID != nil},set:{if !$0 { workoutID=nil;Task{await load()} }})) {
                if let workoutID { ServerWorkoutView(workoutID:workoutID) }
            }
    }
    private func load() async {
        await request.run {
            record = try await request.call(auth,base)
            next = try await request.call(auth,base + "/next-session?at=" + RoutineAPI.timestamp())
            if record["history"].array.isEmpty {
                for (exercise,value) in instance["setup"]["starting_loads_kg"].object where loads[exercise] == nil {
                    loads[exercise] = value.number.map { String(unit.display($0)) } ?? ""
                }
            }
        }
    }
    private func start() async {
        await request.run {
            if pending == nil {
                var values: [String:RoutineValue] = [:]
                for exercise in exercises {
                    guard let n=Double(loads[exercise] ?? ""),n>0,n.isFinite else { throw RoutineAPIError.server(422,"WORKING_LOAD_REQUIRED") }
                    values[exercise] = .number(unit.kilograms(n))
                }
                var body:[String:RoutineValue] = ["workout_id":.string(UUID().uuidString),
                    "week":next["next_session"]["week"],"day":next["next_session"]["day"],"started_at":.string(RoutineAPI.timestamp())]
                if manual || rpeLoads { body[manual ? "initial_loads_kg":"initial_rpe_loads_kg"] = .object(values) }

                pending = .object(body)
            }
            let result = try await request.call(auth,base + "/workouts",pending)
            workoutID = result["workout_id"].text;pending=nil
        }
    }
}

struct ServerWorkoutView: View {
    let workoutID: String
    @EnvironmentObject private var auth: CloudAuth
    @Environment(\.scenePhase) private var scenePhase
    @StateObject private var request = RoutineRequestState()
    @State private var record: RoutineValue = .null
    @State private var result: RoutineValue = .null
    @State private var reps = ""
    @State private var weight = ""
    @State private var rpe = ""
    @State private var reason = "fatigue"
    @State private var pending: RoutineValue?
    @State private var restTarget = ""
    @State private var confirmStop = false
    @AppStorage("displayUnit") private var unit: MassUnit = .kg
    private var base:String { "/v2/workouts/" + RoutineAPI.component(workoutID) }
    private var execution:RoutineValue { record["execution"] }
    private var current:RoutineValue {
        execution["sets"].array.first { $0["id"] == execution["next_set_id"] } ?? .null
    }
    private var closed:Bool { ["completed","stopped"].contains(execution["state"].text) }
    var body: some View {
        ScrollView {
            VStack(alignment:.leading,spacing:MugeStyle.Space.section) {
                if let error=request.error { Text(error).foregroundStyle(MugeStyle.danger) }
                if pending != nil {
                    if request.definitiveFailure {
                        Button("입력 다시 확인") { pending=nil }
                    }
                    Text("저장 응답을 확인하지 못했어요. 같은 기록으로 다시 확인해 주세요.")
                    Button("같은 기록 다시 저장") { Task { await retry() } }.buttonStyle(MugePrimaryButtonStyle()).disabled(request.busy)
                }
                if request.busy { ProgressView() }
                if closed {
                    Text(execution["state"].text == "completed" ? "오늘 운동을 마쳤어요" : "운동을 중단했어요").font(MugeStyle.TypeStyle.section)
                    Text("기록한 수행만 비교해요. 빈 기록은 실패로 계산하지 않아요.").foregroundStyle(MugeStyle.muted)
                    ServerResultCharts(result:result,unit:unit)
                } else if execution != .null {
                    ForEach(execution["guides"].array.indices,id: \.self) { i in
                        Text(execution["guides"].array[i]["text"].text).font(MugeStyle.TypeStyle.detail)
                    }
                    if execution["state"].text == "resting" {
                        MugeCard {
                            Text("휴식").font(MugeStyle.TypeStyle.section)
                            TimelineView(.periodic(from:.now,by:1)) { context in
                                let start=ISO8601DateFormatter().date(from:execution["active_rest"]["started_at"].text)
                                Text(start.map { "\(max(0,Int(context.date.timeIntervalSince($0))))초 쉬었어요" } ?? "휴식 시간을 확인하고 있어요")
                                    .font(MugeStyle.TypeStyle.hero).monospacedDigit()
                            }
                            Text("목표 \(execution["active_rest"]["target_seconds"].display)초")
                            TextField("변경할 휴식 (초)",text:$restTarget).keyboardType(.numberPad).textFieldStyle(.roundedBorder)
                            Button("휴식 목표 변경") {
                                guard let n=Int(restTarget),n>=0,n<=3600 else { return }
                                send("rest_adjust",["target_seconds":.number(Double(n))])
                            }
                            Button("휴식 끝내기") { send("rest_end",["outcome":.string("skipped")]) }.buttonStyle(MugePrimaryButtonStyle())
                        }.disabled(request.busy || pending != nil)
                    } else if execution["state"].text == "active" && current != .null {
                        MugeCard {
                            Text(RoutinePresentation.exercise(current["exercise_id"].text)).font(MugeStyle.TypeStyle.section)
                            Text("목표 \(current["weight_kg"].number.map { unit.label($0) } ?? "직접 선택") · \(current["reps"]["min"].display.isEmpty ? "가능한 반복" : current["reps"]["min"].display + "회")")
                            Text("현재 \(current["selected_weight_kg"].number.map { unit.label($0) } ?? "미선택")")
                            TextField("변경할 중량 (\(unit.rawValue))",text:$weight).keyboardType(.decimalPad).textFieldStyle(.roundedBorder)
                            Picker("변경·건너뛰기 사유",selection:$reason) {
                                Text("힘이 부족해요").tag("fatigue");Text("통증·불편함").tag("pain")
                                Text("시간 부족").tag("time");Text("장비").tag("equipment");Text("기타").tag("other")
                            }
                            Button("중량 변경") {
                                guard let n=Double(weight),n.isFinite,n>=0 else { return }
                                send("change_load",["set_id":current["id"],"value":.number(n),"unit":.string(unit.rawValue),"reason":.string(reason)])
                            }
                            TextField("실제로 한 횟수",text:$reps).keyboardType(.numberPad).textFieldStyle(.roundedBorder)
                            TextField("RPE 1–10 (모르면 비워 두세요)",text:$rpe).keyboardType(.decimalPad).textFieldStyle(.roundedBorder)
                            Button("세트 기록") {
                                guard let n=Int(reps),n>=0,n<=100 else { return }
                                var values:[String:RoutineValue] = ["set_id":current["id"],"reps":.number(Double(n))]
                                if !rpe.isEmpty { guard let effort=Double(rpe) else{return};values["rpe"] = .number(effort) }
                                send("set_result",values)
                            }.buttonStyle(MugePrimaryButtonStyle())
                            Button("이 세트 건너뛰기") { send("skip_set",["set_id":current["id"],"reason":.string(reason)]) }
                        }.disabled(request.busy || pending != nil)
                    } else if execution["state"].text == "active" {
                        Button("오늘 운동 완료") { send("finish",[:]) }.buttonStyle(MugePrimaryButtonStyle()).disabled(request.busy || pending != nil)
                    }
                    Button("운동 중단") { confirmStop=true }.disabled(request.busy || pending != nil)
                    Text("휴식 기록 \(execution["rests"].array.count)회").font(MugeStyle.TypeStyle.card)
                    ForEach(execution["rests"].array.indices,id: \.self) { i in
                        let rest=execution["rests"].array[i]
                        Text("\(i+1)번째 · 목표 \(rest["target_seconds"].display)초 / 기록 \(rest["elapsed_seconds"].display)초")
                            .font(MugeStyle.TypeStyle.detail)
                    }
                }
            }.padding(MugeStyle.Space.page)
        }.background(MugeStyle.canvas).navigationTitle("운동")
            .task {
                await reload()
                while !Task.isCancelled {
                    do { try await Task.sleep(for:.seconds(30)) } catch { break }
                    if scenePhase == .active && !closed && pending == nil { await reload() }
                }
            }
            .onChange(of:scenePhase) { _,phase in if phase == .active && pending == nil { Task { await reload() } } }
            .confirmationDialog("현재 기록을 남기고 중단할까요?",isPresented:$confirmStop) {
                Button("운동 중단",role:.destructive) { send("interrupt",["reason":.string("user_interruption")]) }
                Button("취소",role:.cancel) {}
            }
    }
    private func reload() async {
        guard pending == nil else { return }
        await request.run {
            _ = try await request.call(auth,base + "/reconcile",.object([:]))
            record = try await request.call(auth,base)
            if closed { result = try await request.call(auth,base + "/result") }
        }
    }
    private func send(_ type:String,_ values:[String:RoutineValue]) {
        guard pending == nil,!request.busy else{return}
        var event=values;event["id"] = .string(UUID().uuidString);event["at"] = .string(RoutineAPI.timestamp());event["type"] = .string(type)
        pending = .object(["expected_revision":execution["revision"],"event":.object(event)])
        Task { await retry() }
    }
    private func retry() async {
        await request.run {
            guard let pending else{return}
            record = try await request.call(auth,base + "/events",pending)
            self.pending=nil;reps="";weight="";rpe=""
            if closed { result=try await request.call(auth,base + "/result") }
        }
    }
}

struct ServerResultCharts:View {
    let result:RoutineValue
    let unit:MassUnit
    var body:some View {
        ForEach(result["charts"]["sets_by_exercise"].object.keys.sorted(),id: \.self) { exercise in
            let rows=result["charts"]["sets_by_exercise"][exercise].array
            MugeCard {
                Text(RoutinePresentation.exercise(exercise)).font(MugeStyle.TypeStyle.card)
                Chart {
                    ForEach(rows.indices,id: \.self) { i in
                        if let target=rows[i]["target_weight_kg"].number {
                            PointMark(x:.value("세트",i+1),y:.value(unit.rawValue,unit.display(target))).foregroundStyle(MugeStyle.muted).symbol(.circle)
                        }
                        if let actual=rows[i]["actual_weight_kg"].number {
                            PointMark(x:.value("세트",i+1),y:.value(unit.rawValue,unit.display(actual))).foregroundStyle(MugeStyle.accent).symbol(.square)
                        }
                    }
                }.frame(height:160)
                Text("원: 목표 · 사각형: 실제 · 차트 단위 \(unit.rawValue)").font(MugeStyle.TypeStyle.note)
                ForEach(rows.indices,id: \.self) { i in
                    let row=rows[i]
                    Text("\(i+1)세트 · \(row["actual_weight_kg"].number.map{unit.label($0)} ?? "미기록") · \(row["actual_reps"].number.map{String(Int($0))+"회"} ?? "횟수 미기록")")
                        .font(MugeStyle.TypeStyle.detail)
                }
            }
        }
        MugeCard {
            Text("휴식 기록").font(MugeStyle.TypeStyle.card)
            ForEach(result["charts"]["rests"].array.indices,id: \.self) { i in
                let rest=result["charts"]["rests"].array[i]
                Text("\(i+1)번째 · 목표 \(rest["planned_seconds"].display)초 · 실제 \(rest["actual_seconds"].number.map{String(Int($0))+"초"} ?? "확인 안 됨")")
            }
        }
    }
}
