import SwiftUI

enum MugeStyle {
    static let ink = Color(red: 0.09, green: 0.13, blue: 0.17)
    static let accent = Color(red: 0.18, green: 0.40, blue: 0.35)
    static let canvas = Color(red: 0.965, green: 0.968, blue: 0.955)
    static let muted = Color(red: 0.44, green: 0.49, blue: 0.47)
}

struct MugeCard<Content: View>: View {
    @ViewBuilder let content: Content
    var body: some View {
        VStack(alignment: .leading, spacing: 14) { content }
            .padding(20)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(.white, in: RoundedRectangle(cornerRadius: 24, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: 24).strokeBorder(MugeStyle.ink.opacity(0.05)))
    }
}

struct MugeSectionTitle: View {
    let title: String
    let subtitle: String
    var body: some View {
        VStack(alignment: .leading, spacing: 5) {
            Text(title).font(.title2.bold()).foregroundStyle(MugeStyle.ink)
            Text(subtitle).font(.subheadline).foregroundStyle(MugeStyle.muted)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

struct MugePrimaryButton: View {
    let title: String
    let action: () -> Void
    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.headline)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 17)
        }
        .buttonStyle(.plain)
        .foregroundStyle(.white)
        .background(MugeStyle.accent, in: RoundedRectangle(cornerRadius: 17, style: .continuous))
        .accessibilityAddTraits(.isButton)
    }
}

/// Uses genuine system Liquid Glass on iOS 26, with a native material fallback on iOS 17–18.
/// Never simulates Apple's glass effects using a custom gradient overlay.
struct NativeGlassPanel<Content: View>: View {
    @ViewBuilder let content: Content
    private var fallback: some View {
        content.padding(15)
            .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 22))
    }
    var body: some View {
        #if compiler(>=6.2)
        if #available(iOS 26.0, *) {
            content
                .padding(15)
                .glassEffect(.regular, in: .rect(cornerRadius: 22))
        } else {
            fallback
        }
        #else
        fallback
        #endif
    }
}
