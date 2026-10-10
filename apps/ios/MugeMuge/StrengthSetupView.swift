import SwiftUI

/// Actual measurements and calculated estimates deliberately follow separate paths.
struct StrengthSetupView: View {
    @EnvironmentObject private var workouts: WorkoutStore
    @State private var exercise = "bench"
    @State private var mode = 0
    @State private var weight = ""
    @State private var repetitions = "5"
    @State private var message: String?
    @State private var stage: AssessmentStage = .preparation
    @State private var experienced = false
    @State private var comfortable = false
    @State private var protected = false
    @State private var referenceWeight = ""
    @State private var warmupIndex = 0
    @State private var restUntil: Date?
    @State private var attemptWeight = ""
    @State private var successfulWeights: [Double] = []
    @State private var attemptNotes: [String] = []
    @State private var endingReason = ""

    private enum AssessmentStage { case preparation, technique, warmup, attempt, result }
    private let exercises = [("bench", "벤치프레스"), ("squat", "스쿼트"), ("deadlift", "데드리프트")]
    private let warmupFractions = [0.20, 0.50, 0.70, 0.80, 0.875]
    private let warmupRepetitions = [5, 3, 2, 1, 1]
    private let warmupRest = [60, 90, 120, 240, 360]

    private var exerciseName: String { exercises.first(where: { $0.0 == exercise })?.1 ?? "벤치프레스" }
    private var bestSuccess: Double? { successfulWeights.max() }
    private var estimated: Double? {
        guard let value = number(weight), let count = Int(repetitions), (3...10).contains(count) else { return nil }
        return StrengthMetrics.estimatedOneRepMax(weightKg: value, reps: count)
    }
    private var guideStarted: Bool { mode == 2 && stage != .preparation }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: MugeStyle.Space.section) {
                if !guideStarted {
                    MugeAdaptiveRow {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("내 힘의 기준을\n차근차근").font(MugeStyle.TypeStyle.hero)
                            Text("기록이 있으면 입력하고, 없다면 추정부터 시작해요.")
                                .font(.subheadline).foregroundStyle(MugeStyle.muted)
                        }
                        Spacer(minLength: 0)
                        LilaRiveView(size: 90)
                    }
                    Picker("운동", selection: $exercise) {
                        ForEach(exercises, id: \.0) { item in Text(item.1).tag(item.0) }
                    }.pickerStyle(.segmented)
                    Picker("기록 방법", selection: $mode) {
                        Text("직접 기록").tag(0)
                        Text("기록으로 추정").tag(1)
                        Text("측정 가이드").tag(2)
                    }.pickerStyle(.segmented)
                }
                if mode == 0 { directRecord }
                else if mode == 1 { estimateCard }
                else { assessment }
                if let message {
                    Text(message).font(.subheadline).foregroundStyle(MugeStyle.ink)
                        .accessibilityIdentifier("strength.feedback")
                }
            }.padding(MugeStyle.Space.page)
        }
        .background(MugeStyle.canvas)
        .navigationTitle("최대 중량 관리")
        .navigationBarTitleDisplayMode(.inline)
        .onChange(of: mode) { _, _ in message = nil }
        .onChange(of: exercise) { _, _ in message = nil; weight = "" }
    }

    private var directRecord: some View {
        MugeCard {
            Text("실제로 성공한 한 번의 무게").font(MugeStyle.TypeStyle.card)
            Text("보조자의 도움 없이 바른 자세로 한 번 들어 올린 기록을 입력해요. 추정치는 이곳에 저장하지 않아요.")
                .font(.subheadline).foregroundStyle(MugeStyle.muted)
            weightField("성공한 무게", text: $weight)
            MugePrimaryButton(title: "최대 중량 저장하기") {
                guard let value = number(weight) else { return }
                if workouts.recordMeasuredMax(exerciseID: exercise, weightKg: value) {
                    message = "\(exerciseName) \(formatted(value))킬로그램을 저장했어요."
                    weight = ""
                } else { message = workouts.error ?? "저장하지 못했어요. 다시 시도해 주세요." }
            }.disabled(number(weight) == nil)
            if let latest = workouts.measuredMaxes.filter({ $0.exerciseID == exercise }).max(by: { $0.measuredAt < $1.measuredAt }) {
                Text("최근 기록 · \(formatted(latest.weightKg))킬로그램")
                    .font(.footnote).foregroundStyle(MugeStyle.muted)
            }
        }
    }

    private var estimateCard: some View {
        MugeCard {
            Text("이미 해 본 세트로 추정하기").font(MugeStyle.TypeStyle.card)
            Text("정확한 자세로 수행한 3~10회 기록을 입력하세요. 추정을 위해 새로 한계까지 운동할 필요는 없어요.")
                .font(.subheadline).foregroundStyle(MugeStyle.muted)
            weightField("사용한 무게", text: $weight)
            HStack {
                Text("반복 횟수")
                TextField("3~10회", text: $repetitions).keyboardType(.numberPad).multilineTextAlignment(.trailing)
                    .accessibilityLabel("반복 횟수, 3회부터 10회")
            }.frame(minHeight: MugeStyle.minimumTarget).padding(MugeStyle.Space.md).background(MugeStyle.canvas, in: RoundedRectangle(cornerRadius: MugeStyle.Radius.field))
            if let estimated {
                Text("추정 최대 중량").font(.subheadline)
                Text("\(formatted(estimated))킬로그램").font(MugeStyle.TypeStyle.hero).monospacedDigit()
                Text("계산식: 무게 × (1 + 반복 횟수 ÷ 30)")
                    .font(.caption).foregroundStyle(MugeStyle.muted)
            }
            Text("추정값은 실제 측정 기록과 달라요. 이 화면에서만 계산하며 실제 최대 중량이나 운동 세트로 저장하지 않아요. 이 숫자를 바로 들어 올리라는 뜻이 아니에요.")
                .font(.footnote).foregroundStyle(MugeStyle.muted)
        }
    }

    @ViewBuilder private var assessment: some View {
        switch stage {
        case .preparation: preparation
        case .technique: technique
        case .warmup: warmup
        case .attempt: attempt
        case .result: result
        }
    }

    private var preparation: some View {
        MugeCard {
            Text("측정 전에, 안전부터").font(MugeStyle.TypeStyle.card)
            Text("처음 배우는 동작이거나 혼자 안전하게 실패할 수 없는 환경이라면 오늘은 측정하지 마세요. 지도자와 함께 준비하거나 기존 기록으로 추정할 수 있어요.")
                .font(.subheadline).foregroundStyle(MugeStyle.muted)
            Toggle("이 동작을 익혔고 자세를 유지할 수 있어요", isOn: $experienced)
            Toggle("통증·어지럼증이 없고 컨디션이 괜찮아요", isOn: $comfortable)
            Toggle("보조자와 안전 장비 등 실패에 대비했어요", isOn: $protected)
            weightField("이미 익숙한 예상 기준 무게", text: $referenceWeight)
            Text("이 무게는 준비 세트 예시를 계산하는 기준일 뿐, 오늘 성공해야 하는 목표가 아니에요.")
                .font(.caption).foregroundStyle(MugeStyle.muted)
            MugePrimaryButton(title: "자세와 준비 순서 확인하기") {
                message = nil
                stage = .technique
            }.disabled(!(experienced && comfortable && protected) || number(referenceWeight) == nil)
        }
    }

    private var technique: some View {
        MugeCard {
            Text("\(exerciseName) · 자세 확인").font(MugeStyle.TypeStyle.section)
            ForEach(Array(techniqueSteps.enumerated()), id: \.offset) { index, line in
                HStack(alignment: .top, spacing: 12) {
                    Text("\(index + 1)").font(.headline).frame(width: 26)
                    Text(line).font(.body)
                }
            }
            Text("통증, 어지럼증, 자세 붕괴가 있으면 즉시 중단하세요. 이 짧은 안내는 대면 지도를 대신하지 않아요.")
                .font(.footnote).foregroundStyle(MugeStyle.muted)
            MugePrimaryButton(title: "준비 세트 시작하기") {
                warmupIndex = 0
                restUntil = nil
                stage = .warmup
            }
            Button("오늘은 측정하지 않기") { finish("측정을 시작하지 않았어요.") }
        }
    }

    private var techniqueSteps: [String] {
        switch exercise {
        case "squat":
            return ["안전바 높이와 랙 위치를 보조자와 확인하세요.", "발바닥으로 지면을 지지하고 몸통을 단단히 유지하세요.", "통제 가능한 깊이까지만 앉고, 무릎과 발의 방향을 맞춰 일어나세요."]
        case "deadlift":
            return ["주변 공간을 비우고 원판과 바의 고정을 확인하세요.", "바를 몸 가까이 두고, 몸통을 단단히 유지하며 지면을 밀어 올리세요.", "상체를 뒤로 과하게 젖히지 말고 통제하며 내려놓으세요."]
        default:
            return ["보조자와 신호를 정하고, 안전바와 벤치 위치를 확인하세요.", "발과 엉덩이를 안정적으로 지지하고 어깨를 고정하세요.", "바를 통제하며 내리고 반동 없이 밀어 올리세요. 보조자가 도왔다면 성공 기록으로 남기지 않아요."]
        }
    }

    private var warmup: some View {
        VStack(alignment: .leading, spacing: 18) {
            MugeCard {
                Text("준비 세트 \(warmupIndex + 1) / 5").font(MugeStyle.TypeStyle.section)
                Text("\(formatted((number(referenceWeight) ?? 0) * warmupFractions[warmupIndex]))킬로그램 · \(warmupRepetitions[warmupIndex])회")
                    .font(MugeStyle.TypeStyle.hero)
                Text("기준 무게의 \(formatted(warmupFractions[warmupIndex] * 100))% 예시예요. 실제 장비 단위와 컨디션에 맞춰 낮추거나 지도자와 조정하세요. 준비 세트는 운동 기록에 자동 저장하지 않아요.")
                    .font(.subheadline).foregroundStyle(MugeStyle.muted)
                if let deadline = restUntil {
                    TimelineView(.periodic(from: .now, by: 1)) { context in
                        let remaining = max(0, Int(ceil(deadline.timeIntervalSince(context.date))))
                        Text(remaining > 0 ? "회복 시간 \(remaining / 60)분 \(remaining % 60)초" : "호흡과 자세를 다시 확인해요")
                            .font(MugeStyle.TypeStyle.card).monospacedDigit()
                        MugePrimaryButton(title: warmupIndex == 4 ? "시도 무게 직접 입력하기" : "다음 준비 세트") {
                            restUntil = nil
                            if warmupIndex == 4 { stage = .attempt } else { warmupIndex += 1 }
                        }.disabled(remaining > 0)
                    }
                } else {
                    MugePrimaryButton(title: "준비 세트 완료 · 휴식 시작") {
                        restUntil = Date().addingTimeInterval(Double(warmupRest[warmupIndex]))
                    }
                }
                Button("통증이 있거나 오늘은 중단하기") { finish("준비 중 측정을 중단했어요.") }
            }
            MugeCard {
                Text("이 순서는 어디에서 왔나요?").font(.headline)
                Text("마카릴라 등(2022)의 훈련 경험이 있는 남성 17명 연구에서 사용한 점진적 준비 절차를 참고했어요. 준비 방식 중 무엇이 최적인지 비교한 연구는 아니며, 개인에게 검증된 처방도 아니에요. 표시되는 준비 비율과 휴식 시간은 앱의 안내 예시예요.")
                    .font(.footnote).foregroundStyle(MugeStyle.muted)
                Link("연구 원문 보기", destination: URL(string: "https://doi.org/10.2478/hukin-2022-0046")!)
            }
        }
    }

    private var attempt: some View {
        MugeCard {
            Text("한 번의 시도, 정확하게").font(MugeStyle.TypeStyle.section)
            Text("무게는 직접 정하세요. 성공해도 자동으로 증량하지 않아요. 무리한 추가 시도보다 안전하게 마무리하는 것이 우선이에요.")
                .font(.subheadline).foregroundStyle(MugeStyle.muted)
            if let deadline = restUntil {
                TimelineView(.periodic(from: .now, by: 1)) { context in
                    let remaining = max(0, Int(ceil(deadline.timeIntervalSince(context.date))))
                    Text(remaining > 0 ? "다음 시도 전 회복 · \(remaining / 60)분 \(remaining % 60)초" : "충분히 회복했는지 확인하세요")
                        .font(.headline).monospacedDigit()
                }
            }
            weightField("이번에 시도한 무게", text: $attemptWeight)
            TimelineView(.periodic(from: .now, by: 1)) { context in
                MugePrimaryButton(title: "도움 없이 성공 · 성공 기록 저장") {
                    guard let value = number(attemptWeight) else { return }
                    // Persist before advancing so leaving this screen cannot lose a success.
                    // A later lighter attempt must not replace this assessment's highest success.
                    let improvesBest = bestSuccess.map { value > $0 } ?? true
                    if improvesBest {
                        guard workouts.recordMeasuredMax(exerciseID: exercise, weightKg: value) else {
                            message = workouts.error ?? "저장하지 못했어요. 입력을 유지했으니 다시 저장해 주세요."
                            return
                        }
                    }
                    message = improvesBest ? "성공 기록을 저장했어요." : "이미 저장한 더 높은 성공 기록을 유지해요."
                    successfulWeights.append(value)
                    attemptNotes.append("\(formatted(value))킬로그램 · 성공")
                    attemptWeight = ""
                    restUntil = Date().addingTimeInterval(300)
                }.disabled(number(attemptWeight) == nil || (restUntil.map { $0 > context.date } ?? false))
            }
            Button("실패했어요 · 측정 마무리") {
                if let value = number(attemptWeight) { attemptNotes.append("\(formatted(value))킬로그램 · 실패") }
                finish("실패한 무게는 기록하지 않아요. 오늘의 성공 기록만 확인하세요.")
            }
            Button("통증 또는 불편함 · 즉시 중단") { finish("측정을 중단했어요. 증상이 있으면 추가 운동을 멈추고 필요한 도움을 받으세요.") }
            Button("더 시도하지 않고 결과 확인") { finish("오늘의 측정을 마쳤어요.") }
            if !attemptNotes.isEmpty {
                Divider()
                ForEach(Array(attemptNotes.enumerated()), id: \.offset) { _, note in Text(note).font(.subheadline) }
            }
        }
    }

    private var result: some View {
        MugeCard {
            MugeAdaptiveRow {
                VStack(alignment: .leading, spacing: 8) {
                    Text("오늘의 기준을 확인했어요").font(MugeStyle.TypeStyle.section)
                    Text(endingReason).font(.subheadline).foregroundStyle(MugeStyle.muted)
                }
                LilaRiveView(size: 88)
            }
            if let bestSuccess {
                Text("\(exerciseName) · \(formatted(bestSuccess))킬로그램").font(.title.bold())
                Text("이번 측정에서 성공한 가장 높은 무게를 이미 저장했어요. 화면을 나가거나 이후 시도에 실패해도 기록은 유지돼요.")
                    .font(.subheadline).foregroundStyle(MugeStyle.muted)
                Label("성공 기록 저장 완료", systemImage: "checkmark.circle.fill")
                    .font(.headline)
            } else {
                Text("성공한 시도가 없어 최대 중량은 저장하지 않아요.")
                    .font(.subheadline)
            }
            Button("최대 중량 관리로 돌아가기") { resetGuide() }
        }
    }

    private func weightField(_ title: String, text: Binding<String>) -> some View {
        HStack {
            Text(title).font(.subheadline)
            TextField("킬로그램", text: text)
                .keyboardType(.decimalPad).multilineTextAlignment(.trailing)
                .accessibilityLabel(title + ", 킬로그램")
        }.frame(minHeight: MugeStyle.minimumTarget).padding(MugeStyle.Space.md).background(MugeStyle.canvas, in: RoundedRectangle(cornerRadius: MugeStyle.Radius.field))
    }

    private func number(_ text: String) -> Double? {
        guard let value = Double(text.replacingOccurrences(of: ",", with: ".")),
              value.isFinite, value > 0, value <= 2000 else { return nil }
        return value
    }

    private func formatted(_ value: Double) -> String {
        value.formatted(.number.precision(.fractionLength(0...1)))
    }

    private func finish(_ reason: String) {
        restUntil = nil
        endingReason = reason
        stage = .result
    }

    private func resetGuide() {
        stage = .preparation
        successfulWeights = []
        attemptNotes = []
        attemptWeight = ""
        message = nil
        restUntil = nil
        experienced = false
        comfortable = false
        protected = false
    }
}
