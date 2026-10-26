import SwiftUI

/// Optional measurements are descriptive; only the server decides comparability.
struct ServerProgrammeEvaluation: View {
    let instanceID: String
    let record: RoutineValue
    let outcome: String
    @EnvironmentObject private var auth: CloudAuth
    @Environment(\.dismiss) private var dismiss
    @StateObject private var request = RoutineRequestState()
    @State private var maxes: [RoutineValue] = []
    @State private var selected: [String:String] = [:]
    @State private var conditions: [String:String] = [:]
    @State private var pending: RoutineValue?
    @State private var result: RoutineValue = .null
    @State private var showMax = false
    @State private var confirmSave = false
    @AppStorage("displayUnit") private var unit: MassUnit = .kg
    private var exercises: [String] { record["evaluation_exercise_ids"].array.map(\.text) }
    private var previous: RoutineValue { record["evaluations"].array.last ?? .null }
    private var frozen: Bool { request.busy || pending != nil || result != .null }
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: MugeStyle.Space.section) {
                Text(previous == .null ? "루틴 마무리" : "측정 기록 추가").font(MugeStyle.TypeStyle.section)
                Text("측정 기록이 없어도 마무리할 수 있어요. 최대 중량을 새로 측정하라는 안내는 아니에요.")
                    .font(MugeStyle.TypeStyle.detail).foregroundStyle(MugeStyle.muted)
                if let error = request.error { Text(error).foregroundStyle(MugeStyle.danger) }
                if result == .null {
                    ForEach(exercises, id: \.self) { exercise in
                        MugeCard {
                            Text(RoutinePresentation.exercise(exercise)).font(MugeStyle.TypeStyle.card)
                            Picker("마지막 운동 이후 측정 기록", selection: Binding(
                                get: { selected[exercise] ?? "" }, set: { selected[exercise]=$0; conditions[exercise]=nil })) {
                                Text("측정 기록 없음").tag("")
                                ForEach(maxes.indices, id: \.self) { index in
                                    let row=maxes[index]
                                    if row["exercise_id"].text == exercise && row["kind"].text == "measured" {
                                    Text("\(row["measured_at"].text.prefix(10)) · \(row["weight_kg"].number.map { unit.label($0) } ?? "")").tag(row["id"].text)
                                    }
                                }
                            }
                            if !(selected[exercise] ?? "").isEmpty {
                                Text("시작 전과 동작·장비·측정 방법이 같았나요?")
                                Picker("비교 조건", selection: Binding(get:{conditions[exercise] ?? ""},set:{conditions[exercise]=$0})) {
                                    Text("선택해 주세요").tag("")
                                    Text("같아요").tag("same")
                                    Text("달라요").tag("different")
                                    Text("모르겠어요").tag("unknown")
                                }
                            }
                        }.disabled(frozen)
                    }
                    Text("마지막 운동 이전 기록은 서버에서 거절해요. 기준 기록이 없거나 조건이 다르면 변화율을 계산하지 않아요.")
                        .font(MugeStyle.TypeStyle.detail).foregroundStyle(MugeStyle.muted)
                    Button("측정한 최대 중량 등록") { showMax=true }.disabled(frozen)
                    if request.definitiveFailure && pending != nil {
                        Button("입력 다시 확인") { pending=nil }
                    }
                    Button(pending == nil ? "기록 저장" : "같은 기록 다시 확인") {
                        if pending != nil { Task { await save() } } else { confirmSave=true }
                    }.buttonStyle(MugePrimaryButtonStyle()).disabled(request.busy || exercises.isEmpty)
                } else {
                    Text("기록을 저장했어요").font(MugeStyle.TypeStyle.card)
                    ForEach(result["lifts"].array.indices, id: \.self) { index in
                        let lift=result["lifts"].array[index]
                        MugeCard {
                            Text(RoutinePresentation.exercise(lift["exercise_id"].text)).font(MugeStyle.TypeStyle.card)
                            Text("시작 전: \(lift["baseline"]["weight_kg"].number.map { unit.label($0) } ?? "기록 없음")")
                            Text("종료 후: \(lift["post"]["weight_kg"].number.map { unit.label($0) } ?? "미측정")")
                            if let delta=lift["delta_kg"].number {
                                Text("변화 \(unit.label(delta)) · \(lift["change_percent"].display)%")
                            } else {
                                Text("비교 가능한 측정 기록이 없어 변화율을 표시하지 않아요.")
                                    .foregroundStyle(MugeStyle.muted)
                            }
                        }
                    }
                    Text("관찰된 중량 변화예요. 이 루틴이 변화를 일으켰다는 뜻은 아니에요.")
                        .font(MugeStyle.TypeStyle.detail).foregroundStyle(MugeStyle.muted)
                    Button("확인") { dismiss() }.buttonStyle(MugePrimaryButtonStyle())
                }
            }.padding(MugeStyle.Space.page)
        }.background(MugeStyle.canvas).navigationTitle("루틴 기록")
            .task {
                // Preserve the previous selection when appending a corrected evaluation.
                for lift in previous["lifts"].array where lift["post"] != .null {
                    selected[lift["exercise_id"].text]=lift["post"]["id"].text
                    conditions[lift["exercise_id"].text]=lift["comparison_conditions"].text
                }
                await loadMaxes()
            }
            .sheet(isPresented:$showMax,onDismiss:{ Task { await loadMaxes() } }) {
                NavigationStack { ServerMaxRegistration() }
            }
            .confirmationDialog("수행 기록과 선택한 측정 기록을 저장할까요?",isPresented:$confirmSave) {
                Button("저장") { Task { await save() } }
                Button("취소",role:.cancel) {}
            }
    }
    private func loadMaxes() async {
        await request.run { maxes=try await request.call(auth,"/v2/max-records")["items"].array }
    }
    private func save() async {
        await request.run {
            if pending == nil {
                var ids:[String:RoutineValue]=[:],checks:[String:RoutineValue]=[:]
                for exercise in exercises {
                    guard let id=selected[exercise],!id.isEmpty else { continue }
                    guard let condition=conditions[exercise],["same","different","unknown"].contains(condition) else {
                        throw RoutineAPIError.server(422,"COMPARISON_CONDITIONS_REQUIRED")
                    }
                    ids[exercise] = .string(id); checks[exercise] = .string(condition)
                }
                var body:[String:RoutineValue]=["id":.string(UUID().uuidString),"at":.string(RoutineAPI.timestamp()),
                    "outcome":previous == .null ? .string(outcome) : previous["outcome"],
                    "post_max_record_ids":.object(ids),"comparison_conditions":.object(checks)]
                if previous != .null { body["supersedes_id"]=previous["id"] }
                pending = .object(body)
            }
            result=try await request.call(auth,"/v3/programme-instances/"+RoutineAPI.component(instanceID)+"/evaluations",pending)
            pending=nil
        }
    }
}
