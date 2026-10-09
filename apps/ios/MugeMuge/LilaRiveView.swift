import SwiftUI
import RiveRuntime

/// The first *real Rive runtime* implementation of Lila.
///
/// Artboards: LilaLv1 ... LilaLv6, state machine: LilaCompanion.
/// The binary is built reproducibly from assets/lila/rive_cli/scene.rml.
/// Visual layers embed the user-approved 3D poster sprite without SVG redraw.
/// Large independent limb/eye motion is NOT yet implemented.
struct LilaRiveView: View {
    var level: Int = 1
    var size: CGFloat = 112

    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    private var safeLevel: Int {
        min(max(level, 1), 6)
    }

    var body: some View {
        AsyncRiveUIViewRepresentable {
            let worker = try await Worker()
            let file = try await File(source: .local("lila", Bundle.main), worker: worker)
            let artboard = try await file.createArtboard("LilaLv\(safeLevel)")
            return try await Rive(file: file, artboard: artboard)
        }
        .paused(reduceMotion)
        .frame(width: size, height: size)
        .id(safeLevel)
        .accessibilityLabel("릴라 레벨 \(safeLevel)")
        .accessibilityAddTraits(.isImage)
    }
}
