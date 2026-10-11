"""One shared token source. Generated iOS roles use native Dynamic Type styles."""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
START = '// BEGIN GENERATED DESIGN TOKENS'
END = '// END GENERATED DESIGN TOKENS'

def swift(tokens):
    lines = [START, '// Source: design-tokens/tokens.json; run scripts/generate_design_tokens.py', 'enum MugeStyle {']
    lines += ['    private static func adaptive(_ light: UInt32, _ dark: UInt32) -> Color {',
              '        Color(uiColor: UIColor { trait in',
              '            let value = trait.userInterfaceStyle == .dark ? dark : light',
              '            return UIColor(red: CGFloat((value >> 16) & 255) / 255,',
              '                           green: CGFloat((value >> 8) & 255) / 255,',
              '                           blue: CGFloat(value & 255) / 255, alpha: 1)',
              '        })', '    }']
    for name, (light, dark) in tokens['colors'].items():
        assert all(re.fullmatch(r'#[A-Fa-f0-9]{6}', value) for value in (light,dark))
        lines.append(f'    static let {name} = adaptive(0x{light[1:]}, 0x{dark[1:]})')
    for source, enum in [('spacing','Space'), ('radius','Radius')]:
        lines.append(f'    enum {enum} {{')
        lines.extend(f'        static let {name}: CGFloat = {value}' for name,value in tokens[source].items())
        lines.append('    }')
    lines.append('    enum TypeStyle {')
    lines.extend(f'        static let {name} = Font.{style["ios"]}.weight(.{style["weight"]})' for name,style in tokens['typography'].items())
    lines.append('    }')
    lines.extend(f'    static let {name}: CGFloat = {value}' for name,value in tokens['sizing'].items())
    lines.extend(['}', END])
    return '\n'.join(lines)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    tokens=json.loads((ROOT/'design-tokens/tokens.json').read_text())
    path=ROOT/'apps/ios/MugeMuge/BrandUI.swift'
    original=path.read_text()
    pattern=re.escape(START)+'.*?'+re.escape(END) if START in original else r'enum MugeStyle \{.*?\n\}'
    generated,count=re.subn(pattern,lambda _:swift(tokens),original,count=1,flags=re.S)
    assert count==1,'Missing token generation target'
    if args.check:
        assert original==generated,'Generated iOS tokens drifted from shared source'
        print('PASS: shared JSON and SwiftUI foundation match')
    else:
        path.write_text(generated)
        print('Generated SwiftUI foundation')

if __name__=='__main__':
    main()
