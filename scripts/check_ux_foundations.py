"""Static contracts only; does not replace Swift type checking or simulator QA.

Run: python scripts/check_ux_foundations.py
Optional Swift syntax parsing: pip install tree-sitter tree-sitter-swift
"""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps/ios/MugeMuge"
home = (APP / "ApprovedHomeView.swift").read_text()
guided = (APP / "GuidedWorkoutView.swift").read_text()
brand = (APP / "BrandUI.swift").read_text()
services = (APP / "Services.swift").read_text()
assert home.count(".tabItem") == 3
library = home.split("private struct RoutineLibrary:")[1].split("private struct RoutineCard:")[0]
assert "catalog.demo" not in library
assert "catalog.isLoading" in library and "catalog.error" in library
assert "onboardingCompleted.v2" in home and "homeHelpDismissed.v2" in home
assert "recordMeasuredMaxes" in services
assert "schemaVersion: Int = 1" in services
assert "remainingSets > 1 ? exercise.restSeconds : 0" in guided
assert "restSeconds > 0 ?" in services
assert "MugeStyle.accent" in brand and "MugeStyle.actionHeight" in brand
for name in ["ApprovedHomeView", "StrengthSetupView", "GuidedWorkoutView"]:
    source = (APP / f"{name}.swift").read_text()
    assert "킬로그램" not in source, name
    assert "Color(red:" not in source, name
    assert "systemImage:" not in source and "systemName:" not in source, name
    assert '@AppStorage("displayUnit")' in source, name

assets = APP / "Resources/Assets.xcassets"
svgs = list(assets.glob("lucide-*.imageset/*.svg"))
assert len(svgs) == 10
for path in svgs:
    root = ET.parse(path).getroot()
    assert root.attrib["viewBox"] == "0 0 24 24", path
    assert root.attrib["stroke-width"] == "2", path
    assert root.attrib["stroke-linecap"] == "round", path
    metadata = json.loads((path.parent / "Contents.json").read_text())
    assert metadata["images"][0]["filename"] == path.name
    assert metadata["properties"]["template-rendering-intent"] == "template"
assert "ISC License" in brand and "Cole Bemis" in brand

# Enabled CTA white text contrast against the shared blue token.
def linear(x):
    return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4
tokens = json.loads((ROOT / 'design-tokens/tokens.json').read_text())
def luminance(hex_color):
    rgb = [int(hex_color[i:i+2], 16) / 255 for i in (1, 3, 5)]
    return sum(c * linear(v) for c,v in zip((.2126,.7152,.0722),rgb))
ratios = []
for background, foreground in zip(tokens['colors']['accent'],tokens['colors']['onAccent']):
    light,dark = sorted([luminance(background),luminance(foreground)],reverse=True)
    ratios.append((light+.05)/(dark+.05))
assert min(ratios) >= 4.5
print(f"PASS: navigation, unit labels, component tokens, 10 vector assets, CTA contrast light/dark {ratios[0]:.2f}/{ratios[1]:.2f}:1")

try:
    import tree_sitter
    import tree_sitter_swift
except ImportError:
    print("SKIP: Swift parser unavailable; Xcode build remains required")
else:
    parser = tree_sitter.Parser(tree_sitter.Language(tree_sitter_swift.language()))
    files = list(APP.glob("*.swift")) + list((ROOT / "apps/ios/Tests").glob("*.swift"))
    errors = []
    for path in files:
        tree = parser.parse(path.read_bytes())
        def visit(node):
            if node.type == "ERROR" or node.is_missing:
                errors.append(f"{path.relative_to(ROOT)}:{node.start_point}: {node.type}")
            for child in node.children:
                visit(child)
        visit(tree.root_node)
    assert not errors, "\n".join(errors)
    print(f"PASS: Swift syntax parsing ({len(files)} files); NOT type checking or a build")
