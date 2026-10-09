import SwiftUI

/// Internal QA screen, compiled only for development builds.
/// Lets the product owner inspect all six REAL Rive artboards before signoff.
#if DEBUG
struct LilaStudioView: View {
    @State private var selectedLevel = 1

    private let levelNames = [
        "아기", "새싹", "성장", "단단한", "숙련", "무게왕"
    ]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 22) {
                Text("릴라 Rive 실험실")
                    .font(.title2.bold())
                Text("원본 3D 포스터 속 릴라 6단계를 실제 .riv 파일에서 렌더링하는 개발용 화면입니다.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)

                Picker("성장 단계", selection: $selectedLevel) {
                    ForEach(1...6, id: \.self) { level in
                        Text("Lv.\(level) \(levelNames[level - 1])")
                            .tag(level)
                    }
                }
                .pickerStyle(.menu)

                LilaRiveView(level: selectedLevel, size: 280)
                    .frame(maxWidth: .infinity)
                    .frame(height: 320)
                    .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 24))

                VStack(alignment: .leading, spacing: 10) {
                    Label("실제 Rive", systemImage: "checkmark.circle.fill")
                        .foregroundStyle(.green)
                    Text("• 한 개의 .riv 파일에 6개 아트보드")
                    Text("• 포스터 원본 이미지 그대로 · 미세한 호흡과 흔들림")
                    Text("• Lv.6에만 왕관과 망토")
                }
                .font(.subheadline)

                VStack(alignment: .leading, spacing: 8) {
                    Label("아직 제작·검수 전", systemImage: "exclamationmark.triangle")
                        .foregroundStyle(.orange)
                    Text("포스터에서 추출한 이미지라 큰 화면에서는 흐릿할 수 있습니다. 독립적인 눈 깜빡임, 팔·다리 운동 애니메이션, 감정 11종 전환은 아직 구현 전입니다.")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
                Spacer(minLength: 12)
            }
            .padding()
        }
        .navigationTitle("릴라 실험실")
        .navigationBarTitleDisplayMode(.inline)
    }
}
#endif
