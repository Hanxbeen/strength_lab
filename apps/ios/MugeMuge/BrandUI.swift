import SwiftUI

/// Shared presentation foundations. Screen code depends on semantic roles.
enum MugeStyle {
    static let ink = Color.primary
    static let accent = Color.primary
    static let canvas = Color(uiColor: .systemGroupedBackground)
    static let surface = Color(uiColor: .secondarySystemGroupedBackground)
    static let muted = Color.secondary
    static let border = Color.primary.opacity(0.07)
    static let onAccent = Color(uiColor: UIColor { trait in
        trait.userInterfaceStyle == .dark ? .black : .white
    })

    enum Space {
        static let xs: CGFloat = 4
        static let sm: CGFloat = 8
        static let md: CGFloat = 12
        static let lg: CGFloat = 16
        static let page: CGFloat = 20
        static let section: CGFloat = 24
        static let xl: CGFloat = 32
    }
    enum Radius {
        static let field: CGFloat = 12
        static let control: CGFloat = 16
        static let card: CGFloat = 24
    }
    enum TypeStyle {
        static let hero = Font.largeTitle.weight(.bold)
        static let section = Font.title2.weight(.bold)
        static let card = Font.title3.weight(.bold)
        static let action = Font.headline
        static let body = Font.body
        static let detail = Font.subheadline
        static let note = Font.footnote
    }
    static let minimumTarget: CGFloat = 44
}

/// Numeric display retains the approved hierarchy while honoring Dynamic Type.
private struct MugeNumberStyle: ViewModifier {
    @ScaledMetric(relativeTo: .largeTitle) private var size: CGFloat = 34
    init(size: CGFloat) { _size = ScaledMetric(wrappedValue: size, relativeTo: .largeTitle) }
    func body(content: Content) -> some View {
        content.font(.system(size: size, weight: .bold, design: .rounded)).monospacedDigit()
    }
}

extension View {
    func mugeNumber(size: CGFloat = 34) -> some View { modifier(MugeNumberStyle(size: size)) }
}

/// Reflows related content without shrinking text at accessibility sizes.
struct MugeAdaptiveRow<Content: View>: View {
    @Environment(\.dynamicTypeSize) private var typeSize
    var spacing: CGFloat = MugeStyle.Space.md
    @ViewBuilder let content: Content
    var body: some View {
        let layout = typeSize.isAccessibilitySize
            ? AnyLayout(VStackLayout(alignment: .leading, spacing: spacing))
            : AnyLayout(HStackLayout(alignment: .top, spacing: spacing))
        layout { content }
    }
}

/// A grid aligns paired metric cards to the same row height.
struct MugeMetricRow<Content: View>: View {
    @Environment(\.dynamicTypeSize) private var typeSize
    @ViewBuilder let content: Content
    var body: some View {
        if typeSize.isAccessibilitySize {
            VStack(spacing: MugeStyle.Space.md) { content }
        } else {
            Grid(horizontalSpacing: MugeStyle.Space.md) { GridRow { content } }
        }
    }
}

struct MugeCard<Content: View>: View {
    @ViewBuilder let content: Content
    var body: some View {
        VStack(alignment: .leading, spacing: MugeStyle.Space.lg) { content }
            .padding(MugeStyle.Space.page)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(MugeStyle.surface, in: RoundedRectangle(cornerRadius: MugeStyle.Radius.card, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: MugeStyle.Radius.card).strokeBorder(MugeStyle.border))
    }
}

struct MugeSectionTitle: View {
    let title: String
    let subtitle: String
    var body: some View {
        VStack(alignment: .leading, spacing: MugeStyle.Space.sm) {
            Text(title).font(MugeStyle.TypeStyle.section).foregroundStyle(MugeStyle.ink)
                .accessibilityAddTraits(.isHeader)
            Text(subtitle).font(MugeStyle.TypeStyle.detail).foregroundStyle(MugeStyle.muted)
        }
        .fixedSize(horizontal: false, vertical: true)
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

struct MugePrimaryButtonStyle: ButtonStyle {
    @Environment(\.isEnabled) private var isEnabled
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(MugeStyle.TypeStyle.action)
            .multilineTextAlignment(.center)
            .padding(.horizontal, MugeStyle.Space.lg)
            .padding(.vertical, MugeStyle.Space.lg)
            .frame(maxWidth: .infinity, minHeight: MugeStyle.minimumTarget)
            .foregroundStyle(MugeStyle.onAccent)
            .background(MugeStyle.accent, in: RoundedRectangle(cornerRadius: MugeStyle.Radius.control, style: .continuous))
            .contentShape(RoundedRectangle(cornerRadius: MugeStyle.Radius.control))
            .opacity(isEnabled ? (configuration.isPressed ? 0.8 : 1) : 0.4)
    }
}

struct MugeSecondaryButtonStyle: ButtonStyle {
    @Environment(\.isEnabled) private var isEnabled
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(MugeStyle.TypeStyle.action)
            .multilineTextAlignment(.center)
            .padding(.horizontal, MugeStyle.Space.lg)
            .padding(.vertical, MugeStyle.Space.md)
            .frame(minHeight: MugeStyle.minimumTarget)
            .foregroundStyle(MugeStyle.ink)
            .background(MugeStyle.surface, in: RoundedRectangle(cornerRadius: MugeStyle.Radius.control))
            .contentShape(RoundedRectangle(cornerRadius: MugeStyle.Radius.control))
            .opacity(isEnabled ? (configuration.isPressed ? 0.65 : 1) : 0.4)
    }
}

struct MugePrimaryButton: View {
    let title: String
    let action: () -> Void
    var body: some View {
        Button(title, action: action).buttonStyle(MugePrimaryButtonStyle())
    }
}

struct NativeGlassPanel<Content: View>: View {
    @ViewBuilder let content: Content
    private var fallback: some View {
        content.padding(MugeStyle.Space.lg)
            .background(.regularMaterial, in: RoundedRectangle(cornerRadius: MugeStyle.Radius.card))
    }
    var body: some View {
        #if compiler(>=6.2)
        if #available(iOS 26.0, *) {
            content.padding(MugeStyle.Space.lg).glassEffect(.regular, in: .rect(cornerRadius: MugeStyle.Radius.card))
        } else { fallback }
        #else
        fallback
        #endif
    }
}
