import SwiftUI

/// Native, resolution-independent mascot prototype. Motion respects Reduce Motion.
/// This is an in-app vector character, not an imported raster concept render.
struct MugeMascot: View {
    var size: CGFloat = 120
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    var body: some View {
        TimelineView(.animation(minimumInterval: 1.0 / 30.0, paused: reduceMotion)) { timeline in
            let t = timeline.date.timeIntervalSinceReferenceDate
            let bounce = reduceMotion ? 0.0 : sin(t * 2.0) * 3.0
            let sway = reduceMotion ? 0.0 : sin(t * 1.1) * 4.0
            ZStack {
                Ellipse()
                    .fill(MugeStyle.ink.opacity(0.10))
                    .frame(width: size * 0.62, height: size * 0.12)
                    .offset(y: size * 0.39)
                // Feet, hands, body and eyes use vector primitives for crisp scaling.
                Capsule().fill(Color(red: 0.83, green: 0.81, blue: 0.76))
                    .frame(width: size * 0.24, height: size * 0.17)
                    .offset(x: -size * 0.21, y: size * 0.31)
                Capsule().fill(Color(red: 0.83, green: 0.81, blue: 0.76))
                    .frame(width: size * 0.24, height: size * 0.17)
                    .offset(x: size * 0.21, y: size * 0.31)
                Ellipse()
                    .fill(Color(red: 0.98, green: 0.96, blue: 0.91))
                    .frame(width: size * 0.72, height: size * 0.79)
                    .shadow(color: MugeStyle.ink.opacity(0.10), radius: 12, y: 7)
                Capsule().fill(Color(red: 0.94, green: 0.91, blue: 0.85))
                    .frame(width: size * 0.16, height: size * 0.28)
                    .rotationEffect(.degrees(-24 + sway))
                    .offset(x: -size * 0.36, y: size * 0.13)
                Capsule().fill(Color(red: 0.94, green: 0.91, blue: 0.85))
                    .frame(width: size * 0.16, height: size * 0.28)
                    .rotationEffect(.degrees(24 - sway))
                    .offset(x: size * 0.36, y: size * 0.13)
                Capsule()
                    .fill(MugeStyle.ink)
                    .frame(width: size * 0.76, height: size * 0.15)
                    .overlay {
                        Text("무게무게")
                            .font(.system(size: size * 0.078, weight: .heavy, design: .rounded))
                            .foregroundStyle(.white)
                    }
                    .offset(y: -size * 0.29)
                HStack(spacing: size * 0.18) {
                    Capsule().frame(width: size * 0.055, height: size * 0.095)
                    Capsule().frame(width: size * 0.055, height: size * 0.095)
                }
                .foregroundStyle(MugeStyle.ink)
                .offset(y: -size * 0.06)
                HStack(spacing: size * 0.33) {
                    Circle().fill(Color.pink.opacity(0.32))
                    Circle().fill(Color.pink.opacity(0.32))
                }
                .frame(width: size * 0.45, height: size * 0.085)
                .offset(y: size * 0.035)
                Image(systemName: "mouth")
                    .font(.system(size: size * 0.13, weight: .semibold))
                    .foregroundStyle(MugeStyle.ink)
                    .offset(y: size * 0.08)
            }
            .offset(y: bounce)
            .frame(width: size, height: size)
        }
        .frame(width: size, height: size)
        .accessibilityLabel("살짝 흔들리며 응원하는 무게무게 마스코트")
        .accessibilityAddTraits(.isImage)
    }
}
