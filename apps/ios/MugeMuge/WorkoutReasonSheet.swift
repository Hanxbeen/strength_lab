import SwiftUI

struct WorkoutReasonSheet: View {
    let target: WorkoutChange
    @EnvironmentObject private var workouts: WorkoutStore
    @Environment(\.dismiss) private var dismiss
    @State private var selected: Set<WorkoutReason> = []
    @State private var error: String?
    private var choices: [WorkoutReason] {
        if target.kind == "finish" { return [.time, .effortInsufficient, .painDiscomfort, .other] }
        if let from = target.fromKg, let to = target.toKg, to > from {
            return [.effortAvailable, .plannedProgression, .equipment, .painDiscomfort, .other]
        }
        return [.effortInsufficient, .painDiscomfort, .technique, .equipment, .planChange, .other]
    }
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: MugeStyle.Space.page) {
                    MugeSectionTitle(title: "이유를 남길까요?", subtitle: "기록은 이미 저장됐어요. 여러 개를 선택하거나 건너뛸 수 있어요.")
                    LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: MugeStyle.Space.sm) {
                        ForEach(choices) { reason in
                            Button {
                                if selected.contains(reason) { selected.remove(reason) } else { selected.insert(reason) }
                            } label: {
                                Text(reason.title).font(MugeStyle.TypeStyle.detail)
                                    .frame(maxWidth: .infinity, minHeight: MugeStyle.minimumTarget)
                                    .padding(.horizontal, MugeStyle.Space.sm)
                                    .background(selected.contains(reason) ? MugeStyle.accent : MugeStyle.canvas)
                                    .foregroundStyle(selected.contains(reason) ? MugeStyle.onAccent : MugeStyle.ink)
                                    .clipShape(RoundedRectangle(cornerRadius: MugeStyle.Radius.control))
                            }.accessibilityAddTraits(selected.contains(reason) ? [.isSelected] : [])
                        }
                    }
                    if selected.contains(.painDiscomfort) {
                        Text("통증 기록은 중량 조절의 근거로 쓰지 않아요. 진행 중인 운동은 일시정지해요.")
                            .font(MugeStyle.TypeStyle.note).foregroundStyle(MugeStyle.muted)
                    }
                    if let error { Text(error).foregroundStyle(MugeStyle.danger) }
                    Button("사유 저장") { save(.answered) }.buttonStyle(MugePrimaryButtonStyle()).disabled(selected.isEmpty)
                    Button("잘 모르겠어요") { selected = []; save(.unknown) }.buttonStyle(MugeSecondaryButtonStyle())
                    Button("건너뛰기") { selected = []; save(.declined) }
                        .frame(maxWidth: .infinity, minHeight: MugeStyle.minimumTarget)
                }.padding(MugeStyle.Space.page)
            }.background(MugeStyle.canvas)
                .navigationTitle("변경 사유").navigationBarTitleDisplayMode(.inline)
                .toolbar { ToolbarItem(placement: .cancellationAction) { Button("닫기") { if target.latestReport == nil { selected = []; save(.declined) } else { dismiss() } } } }
        }.interactiveDismissDisabled().onAppear { selected = Set(target.latestReport?.reasonCodes ?? []) }
    }
    private func save(_ status: ReasonResponseStatus) {
        let codes = selected.sorted { $0.rawValue < $1.rawValue }
        if workouts.recordReason(target: target.id, codes: codes, status: status,
                                 supersedes: target.latestReport?.id) { dismiss() }
        else { error = "저장하지 못했어요. 기록이 바뀌었다면 창을 닫고 다시 열어 주세요." }
    }
}
