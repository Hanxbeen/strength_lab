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
                    Text("• 원본 릴라 기반 4배 AI 초해상도 이미지")
                    Text("• 실제 눈 깜빡임 · 호흡 · 미세한 몸 흔들림")
                    Text("• Lv.6에만 왕관과 망토")
                }
                .font(.subheadline)

                VStack(alignment: .leading, spacing: 8) {
                    Label("아직 제작·검수 전", systemImage: "exclamationmark.triangle")
                        .foregroundStyle(.orange)
                    Text("원본 포스터의 작은 이미지를 AI로 확대했기 때문에 세부 질감은 추정된 것입니다. 독립 팔·다리 관절 운동, 감정 11종, 자유로운 3D 회전은 아직 구현 전입니다.")
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
