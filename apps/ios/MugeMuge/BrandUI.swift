import SwiftUI

enum MugeThirdPartyNotices {
    // lucide-icons/lucide@70562c1ee1c4fdcf736fe97bc893fb8511927934; black template stroke only.
    static let lucide = """
    ISC License

    Copyright (c) 2026 Lucide Icons and Contributors

    Permission to use, copy, modify, and/or distribute this software for any
    purpose with or without fee is hereby granted, provided that the above
    copyright notice and this permission notice appear in all copies.

    THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
    WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
    MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
    ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
    WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
    ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
    OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

    ---

    The following Lucide icons are derived from the Feather project:

    airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out

    The MIT License (MIT) (for the icons listed above)

    Copyright (c) 2013-present Cole Bemis

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

    """
}

/// Shared presentation foundations. Screen code depends on semantic roles.
enum MugeStyle {
    static let ink = Color.primary
    static let accent = Color(red: 0.12, green: 0.34, blue: 0.85)
    static let canvas = Color(uiColor: .systemGroupedBackground)
    static let surface = Color(uiColor: .secondarySystemGroupedBackground)
    static let muted = Color.secondary
    static let border = Color.primary.opacity(0.07)
    static let onAccent = Color.white
    static let disabledSurface = Color(uiColor: .tertiarySystemFill)
    static let disabledInk = Color.secondary

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
    static let minimumTarget: CGFloat = 48
    static let actionHeight: CGFloat = 56
    static let inputNumberSize: CGFloat = 48
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
            .frame(maxWidth: .infinity, minHeight: MugeStyle.actionHeight)
            .foregroundStyle(isEnabled ? MugeStyle.onAccent : MugeStyle.disabledInk)
            .background(isEnabled ? MugeStyle.accent : MugeStyle.disabledSurface, in: RoundedRectangle(cornerRadius: MugeStyle.Radius.control, style: .continuous))
            .contentShape(RoundedRectangle(cornerRadius: MugeStyle.Radius.control))
            .opacity(configuration.isPressed && isEnabled ? 0.8 : 1)
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

/// Vendored Lucide assets; geometry and license are preserved, template tint is semantic.
struct MugeIcon: View {
    let name: String
    var body: some View {
        Image("lucide-" + name).renderingMode(.template).resizable()
            .scaledToFit().frame(width: 24, height: 24).accessibilityHidden(true)
    }
}

struct MugeNavigationLabel: View {
    let title: String
    var icon: String? = nil
    var body: some View {
        HStack(spacing: MugeStyle.Space.md) {
            if let icon { MugeIcon(name: icon) }
            Text(title).font(MugeStyle.TypeStyle.action)
            Spacer()
            MugeIcon(name: "chevron-right").foregroundStyle(MugeStyle.muted)
        }
        .frame(minHeight: MugeStyle.minimumTarget)
        .contentShape(Rectangle())
    }
}

struct MugeMassInput: View {
    let title: String
    @Binding var text: String
    let unit: MassUnit
    var allowsZero = false
    @FocusState private var focused: Bool
    private var valid: Bool { unit.parse(text, allowsZero: allowsZero) != nil }
    var body: some View {
        VStack(alignment: .leading, spacing: MugeStyle.Space.md) {
            Text(title).font(MugeStyle.TypeStyle.detail)
            HStack(alignment: .firstTextBaseline) {
                TextField("0", text: $text).keyboardType(.decimalPad)
                    .mugeNumber(size: MugeStyle.inputNumberSize).focused($focused)
                    .accessibilityLabel("\(title), \(unit.rawValue)")
                Text(unit.rawValue).font(MugeStyle.TypeStyle.card).foregroundStyle(MugeStyle.muted)
            }
            HStack {
                Button("−\(unit.step.formatted())") { adjust(-unit.step) }
                Spacer()
                Button("직접 입력") { focused = true }
                Spacer()
                Button("+\(unit.step.formatted())") { adjust(unit.step) }
            }.buttonStyle(MugeSecondaryButtonStyle())
            if !text.isEmpty && !valid {
                Text("0보다 \(allowsZero ? "작지 않은" : "큰") \(unit.label(2000)) 이하의 값을 입력해 주세요.")
                    .font(MugeStyle.TypeStyle.note).foregroundStyle(.red)
            }
        }
    }
    private func adjust(_ delta: Double) {
        let current = unit.parse(text, allowsZero: true).map(unit.display) ?? 0
        let lower = allowsZero ? 0 : unit.step
        let next = min(unit.display(2000), max(lower, current + delta))
        text = unit.input(unit.kilograms(next))
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
