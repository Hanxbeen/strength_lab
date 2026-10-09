#!/usr/bin/env python3
"""Create Rive-importable layered Lila artwork and a local motion preview.

IMPORTANT: This exports editable SVG artwork + a CSS motion proof, not a .riv
file or a Rive animation. A real Rive editor rig is a separate review gate.
"""
from __future__ import annotations

from pathlib import Path
import html
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/lila"
SVG_DIR = OUT / "rive_import"
SVG_DIR.mkdir(parents=True, exist_ok=True)

CHARCOAL = "#2A2A2A"
IVORY = "#F3E7DB"
LEVELS = [
    {"id": 1, "name": "아기 릴라", "body_x": 106, "body_y": 116, "head_scale": 1.10, "head_offset": 35, "arm_rx": 31, "leg_rx": 34, "shoulder": 102, "seated": True},
    {"id": 2, "name": "새싹 릴라", "body_x": 106, "body_y": 119, "head_scale": 1.055, "head_offset": 23, "arm_rx": 31, "leg_rx": 30, "shoulder": 105, "seated": False},
    {"id": 3, "name": "성장 릴라", "body_x": 121, "body_y": 131, "head_scale": 1.015, "head_offset": 15, "arm_rx": 37, "leg_rx": 37, "shoulder": 117, "seated": False},
    {"id": 4, "name": "단단한 릴라", "body_x": 144, "body_y": 143, "head_scale": .98, "head_offset": 8, "arm_rx": 45, "leg_rx": 44, "shoulder": 138, "seated": False},
    {"id": 5, "name": "숙련 릴라", "body_x": 164, "body_y": 152, "head_scale": .96, "head_offset": 0, "arm_rx": 56, "leg_rx": 52, "shoulder": 155, "seated": False},
    {"id": 6, "name": "무게왕 릴라", "body_x": 164, "body_y": 152, "head_scale": .96, "head_offset": 0, "arm_rx": 56, "leg_rx": 52, "shoulder": 155, "seated": False},
]
MOODS = [
    {"id":"idle","label":"기본","symbol":""},
    {"id":"happy","label":"행복","symbol":"♥"},
    {"id":"surprise","label":"놀람","symbol":"!"},
    {"id":"curious","label":"궁금","symbol":"?"},
    {"id":"dizzy","label":"어지러움","symbol":"@"},
    {"id":"focus","label":"집중","symbol":"•"},
    {"id":"sleepy","label":"졸림","symbol":"Zzz"},
    {"id":"confident","label":"자신감","symbol":"✦"},
    {"id":"celebrate","label":"축하","symbol":"✧"},
    {"id":"repairing","label":"정비","symbol":"⚙"},
    {"id":"warning","label":"주의","symbol":"!"},
]
LAYERS = [
    "cape_back","leg_left","leg_right","foot_left","foot_right","body_torso","belly_skin","arm_left",
    "arm_right","head_group","ear_left","ear_right","head_skull",
    "tuft_A","forehead_skin","muzzle_skin","eye_left","eye_right",
    "nostril_left","nostril_right","crown_front"
]
SVG_NS = "http://www.w3.org/2000/svg"

def defs():
    return """
<defs>
  <radialGradient id="furGrad" cx="36%" cy="23%" r="89%" fx="28%" fy="20%">
    <stop offset="0%" stop-color="#515151"/>
    <stop offset="45%" stop-color="#343434"/>
    <stop offset="100%" stop-color="#1B1C1D"/>
  </radialGradient>
  <radialGradient id="furDark" cx="30%" cy="15%" r="98%">
    <stop offset="0%" stop-color="#424141"/>
    <stop offset="100%" stop-color="#222223"/>
  </radialGradient>
  <radialGradient id="skinGrad" cx="30%" cy="12%" r="98%">
    <stop offset="0%" stop-color="#FFF6EA"/>
    <stop offset="62%" stop-color="#F3E7DB"/>
    <stop offset="100%" stop-color="#D8C3B3"/>
  </radialGradient>
  <radialGradient id="skinMuzzle" cx="32%" cy="12%" r="100%">
    <stop offset="0%" stop-color="#FFF8EB"/>
    <stop offset="65%" stop-color="#F3E7DB"/>
    <stop offset="100%" stop-color="#DFCCBA"/>
  </radialGradient>
  <linearGradient id="gold" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" stop-color="#FFE6A7"/>
    <stop offset="45%" stop-color="#E4AE50"/>
    <stop offset="100%" stop-color="#B27B2B"/>
  </linearGradient>
  <linearGradient id="capeRed" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" stop-color="#C84943"/>
    <stop offset="100%" stop-color="#8C2424"/>
  </linearGradient>
</defs>"""

# Head uses identical paths across levels. Scaling occurs at head_group
# rather than independently mutating eyes, nose, mouth, ears or muzzle.
def head_group(level):
    scale = level["head_scale"]
    offset = level["head_offset"]
    return f"""<g id="head_group" transform="translate(300 {187+offset}) scale({scale}) translate(-300 -187)">
    <g id="ear_left">
      <ellipse cx="166" cy="218" rx="40" ry="48" fill="url(#furDark)"/>
      <ellipse cx="166" cy="220" rx="19" ry="27" fill="#2A2A2A"/>
    </g>
    <g id="ear_right">
      <ellipse cx="434" cy="218" rx="40" ry="48" fill="url(#furDark)"/>
      <ellipse cx="434" cy="220" rx="19" ry="27" fill="#2A2A2A"/>
    </g>
    <g id="head_skull">
      <path d="M300 48 C197 43 142 120 142 219 C137 306 190 365 300 367 C410 365 463 306 458 219 C458 120 403 43 300 48Z" fill="url(#furGrad)"/>
    </g>
    <g id="tuft_A" aria-label="짧게 옆으로 누운 3가닥 잔털">
      <path d="M299 52 C285 41 279 30 284 25 C295 24 302 37 307 48Z" fill="#353535"/>
      <path d="M304 51 C304 33 312 24 320 30 C323 38 318 46 309 53Z" fill="#3B3B3B"/>
      <path d="M305 54 C314 41 328 40 332 46 C331 54 317 59 305 54Z" fill="#303031"/>
    </g>
    <g id="forehead_skin">
      <path d="M207 226 C206 176 218 139 252 137 C269 132 289 144 300 155 C315 140 327 132 348 136 C387 135 397 178 394 227 C390 272 358 285 301 288 C237 285 210 263 207 226Z" fill="url(#skinGrad)"/>
    </g>
    <g id="muzzle_skin">
      <path d="M215 255 C236 237 265 236 298 247 C333 235 363 237 386 255 C411 272 416 313 401 345 C386 380 338 399 300 396 C256 399 212 377 198 341 C186 310 192 276 215 255Z" fill="url(#skinMuzzle)"/>
    </g>
    <g id="eye_left"><rect x="265" y="195" width="13" height="33" rx="6.5" fill="#191A1B"/></g>
    <g id="eye_right"><rect x="322" y="195" width="13" height="33" rx="6.5" fill="#191A1B"/></g>
    <g id="nostril_left"><ellipse cx="292" cy="272" rx="4.1" ry="4.8" fill="#191A1B"/></g>
    <g id="nostril_right"><ellipse cx="307" cy="272" rx="4.1" ry="4.8" fill="#191A1B"/></g>
  </g>"""

def level_svg(level, face_only=False):
    lv = level["id"]
    body_x = level["body_x"]
    body_y = level["body_y"]
    arms = level["arm_rx"]
    shoulder = level["shoulder"]
    legs = level["leg_rx"]
    # All hands are empty; tools never appear in the level artwork.
    cape = ""
    crown = ""
    if lv == 6 and not face_only:
        cape = """<g id="cape_back" data-role="accessory-cape">
          <path d="M196 324 C141 366 124 443 113 569 C144 555 169 576 196 565 C219 557 232 572 246 561 L355 561 C379 574 402 553 430 568 C457 579 481 558 508 572 C492 451 475 359 403 325Z" fill="url(#capeRed)"/>
          <path d="M194 343 C145 400 144 490 130 548" fill="none" stroke="#D65C55" stroke-width="9" opacity=".6"/>
        </g>"""
        crown = """<g id="crown_front" data-role="accessory-crown">
          <path d="M245 88 L238 35 L268 60 L300 22 L333 60 L364 35 L357 88Z" fill="url(#gold)" stroke="#AF792C" stroke-width="3" stroke-linejoin="round"/>
          <rect x="244" y="82" width="113" height="15" rx="7" fill="url(#gold)" stroke="#AF792C" stroke-width="2"/>
          <circle cx="300" cy="67" r="6" fill="#7C9EA2"/>
          <circle cx="238" cy="34" r="7" fill="#FFDE98"/>
          <circle cx="300" cy="21" r="7" fill="#FFDE98"/>
          <circle cx="365" cy="34" r="7" fill="#FFDE98"/>
        </g>"""
    # Each leg and each foot is separate to support future hip/knee/ankle pivots.
    if level["seated"]:
        legs_group = """<g id="leg_left" data-pivot="230,461"><ellipse cx="218" cy="514" rx="67" ry="47" fill="url(#furDark)"/></g>
        <g id="leg_right" data-pivot="370,461"><ellipse cx="382" cy="514" rx="67" ry="47" fill="url(#furDark)"/></g>
        <g id="foot_left" data-pivot="218,530"><ellipse cx="197" cy="534" rx="34" ry="21" fill="url(#skinGrad)"/></g>
        <g id="foot_right" data-pivot="382,530"><ellipse cx="403" cy="534" rx="34" ry="21" fill="url(#skinGrad)"/></g>"""
    else:
        legs_group = f"""<g id="leg_left" data-pivot="{300-body_x*.46:.1f},466">
          <ellipse cx="{300-body_x*.46:.1f}" cy="508" rx="{legs:.1f}" ry="64" fill="url(#furDark)"/>
        </g>
        <g id="leg_right" data-pivot="{300+body_x*.46:.1f},466">
          <ellipse cx="{300+body_x*.46:.1f}" cy="508" rx="{legs:.1f}" ry="64" fill="url(#furDark)"/>
        </g>
        <g id="foot_left" data-pivot="{300-body_x*.47:.1f},548">
          <ellipse cx="{300-body_x*.47:.1f}" cy="561" rx="{legs+14:.1f}" ry="20" fill="url(#furGrad)"/>
          <ellipse cx="{300-body_x*.47:.1f}" cy="568" rx="{legs*.68:.1f}" ry="12" fill="url(#skinGrad)"/>
        </g>
        <g id="foot_right" data-pivot="{300+body_x*.47:.1f},548">
          <ellipse cx="{300+body_x*.47:.1f}" cy="561" rx="{legs+14:.1f}" ry="20" fill="url(#furGrad)"/>
          <ellipse cx="{300+body_x*.47:.1f}" cy="568" rx="{legs*.68:.1f}" ry="12" fill="url(#skinGrad)"/>
        </g>"""
    # Arms become wider and fuller independently of overall body scale.
    arm_r_y = 76 + (lv - 1) * 7
    xdist = shoulder+arms*.22
    return f'''<svg xmlns="{SVG_NS}" viewBox="0 0 600 620" width="600" height="620" aria-label="릴라 {html.escape(level["name"])}" data-level="{lv}" data-role="lila-layered-artwork">
  {defs()}
  <g id="character_root">
    {cape}
    {legs_group if not face_only else ""}
    {f'<g id="body_torso"><ellipse cx="300" cy="429" rx="{body_x}" ry="{body_y}" fill="url(#furGrad)"/></g>' if not face_only else ""}
    {f'<g id="belly_skin"><ellipse cx="300" cy="440" rx="{body_x*.48:.1f}" ry="{body_y*.48:.1f}" fill="url(#skinGrad)"/></g>' if not face_only else ""}
    {f'<g id="arm_left" data-pivot="{300-xdist:.1f},359"><ellipse cx="{300-xdist:.1f}" cy="426" rx="{arms}" ry="{arm_r_y}" transform="rotate(-11 {300-xdist:.1f} 426)" fill="url(#furDark)"/><ellipse cx="{300-xdist-11:.1f}" cy="{426+arm_r_y*.83:.1f}" rx="{arms*.62:.1f}" ry="{arms*.52:.1f}" fill="url(#skinGrad)"/></g>' if not face_only else ""}
    {f'<g id="arm_right" data-pivot="{300+xdist:.1f},359"><ellipse cx="{300+xdist:.1f}" cy="426" rx="{arms}" ry="{arm_r_y}" transform="rotate(11 {300+xdist:.1f} 426)" fill="url(#furDark)"/><ellipse cx="{300+xdist+11:.1f}" cy="{426+arm_r_y*.83:.1f}" rx="{arms*.62:.1f}" ry="{arms*.52:.1f}" fill="url(#skinGrad)"/></g>' if not face_only else ""}
    {head_group(level)}
    {crown}
  </g>
</svg>'''

def unique_gradient_ids(svg: str, suffix: str) -> str:
    """Avoid SVG gradient collisions when six inline artworks share one HTML DOM."""
    for ident in ("furGrad", "furDark", "skinGrad", "skinMuzzle", "gold", "capeRed"):
        svg = svg.replace(f'id="{ident}"', f'id="{ident}_{suffix}"')
        svg = svg.replace(f'url(#{ident})', f'url(#{ident}_{suffix})')
    return svg


def build_html(svg_files):
    svg_files = {lv: unique_gradient_ids(svg, f'level{lv}') for lv, svg in svg_files.items()}
    buttons = "".join(f'<button type="button" class="level" data-level="{l["id"]}" aria-pressed="{"true" if l["id"]==3 else "false"}">Lv.{l["id"]} {l["name"]}</button>' for l in LEVELS)
    moods = "".join(f'<button type="button" class="mood" data-mood="{m["id"]}" aria-pressed="{"true" if m["id"]=="idle" else "false"}">{m["label"]}</button>' for m in MOODS)
    artworks = "".join(f'<div class="artwork" data-art="{l["id"]}" style="display:{"block" if l["id"]==3 else "none"}">{svg_files[l["id"]]}</div>' for l in LEVELS)
    return '''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>릴라 Phase 2 · 파츠와 모션 검증</title>
<style>
:root{font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Malgun Gothic",sans-serif;color:#252524;background:#eee8df}
*{box-sizing:border-box}body{margin:0;padding:18px}main{max-width:900px;margin:auto}
h1{font-size:24px;margin:0}p{color:#6d6760;line-height:1.55}.hero{padding:22px;background:#f8f5ee;border-radius:22px}
.panel{background:#f8f5ee;border-radius:22px;margin-top:14px;padding:18px}.flex{display:flex;flex-wrap:wrap;gap:7px}
button{cursor:pointer;font:inherit;font-size:13px;border:1px solid #dad1c6;background:white;border-radius:10px;padding:8px 10px}
button[aria-pressed=true]{background:#2a2a2a;color:white;border-color:#2a2a2a}
.stage{height:380px;display:flex;justify-content:center;align-items:center;position:relative;overflow:hidden}
.artwork{position:absolute;width:min(360px,100%);height:100%}.artwork svg{width:100%;height:100%;overflow:visible}
.symbol{position:absolute;font-size:46px;top:25px;right:20%;color:#ed9d48;transform:rotate(7deg);font-weight:850}
.stage [id^="body_torso"],.stage [id^="belly_skin"]{transform-origin:300px 440px;animation:breathe 3.4s ease-in-out infinite}
.stage [id="head_group"]{transform-box:fill-box;transform-origin:50% 75%;animation:tilt 5.5s ease-in-out infinite}
.stage [id^="eye_"]{transform-box:fill-box;transform-origin:center;animation:blink 5.8s infinite}
.stage[data-mood="sleepy"] [id^="eye_"]{transform:scaleY(.35);animation:none}
.stage[data-mood="focus"] [id^="eye_"]{transform:scaleY(.75);animation:none}
.stage[data-mood="happy"] [id^="eye_"]{transform:scaleY(.5) rotate(10deg);animation:none}
.stage[data-mood="surprise"] [id^="eye_"]{transform:scale(1.25);animation:none}
.stage[data-mood="celebrate"] .artwork svg{animation:hop .65s ease-in-out infinite alternate}
.stage[data-mood="dizzy"] .artwork svg{animation:wobble .9s ease-in-out infinite alternate}
.stage[data-mood="repairing"] [id="arm_right"]{transform-box:fill-box;transform-origin:50% 15%;animation:fix 1s ease-in-out infinite alternate}
.note{font-size:12px;margin:8px 0 0;color:#7a7168}
@keyframes breathe{50%{transform:scale(1.013,.985)}}
@keyframes blink{0%,40%,44%,100%{transform:scaleY(1)}42%{transform:scaleY(.06)}}
@keyframes tilt{33%{rotate:-1.8deg}70%{rotate:1.8deg}}
@keyframes hop{50%{transform:translateY(-14px)}}
@keyframes wobble{50%{transform:rotate(-3deg)}}
@keyframes fix{50%{transform:rotate(12deg)}}
@media(prefers-reduced-motion:reduce){*,*:before,*:after{animation:none!important;transition:none!important}}
</style></head><body><main>
<section class="hero"><h1>릴라 · Phase 2 개발용 미리보기</h1><p>포스터가 아닌 <strong>파츠별 SVG 원화와 상태 제어</strong> 검증용 화면입니다. 원본 3D 캐릭터의 완전 재현이나 실제 Rive 파일이 아닙니다.</p></section>
<section class="panel"><h2>성장 단계</h2><div class="flex" id="levels">''' + buttons + '''</div>
<div class="stage" id="stage" data-mood="idle">''' + artworks + '''<div class="symbol" id="symbol" aria-live="polite"></div></div>
<p class="note" id="stateLabel">Lv.3 성장 릴라 · 기본</p>
</section>
<section class="panel"><h2>상태 선택</h2><div class="flex" id="moods">''' + moods + '''</div>
<p class="note">여기서 보는 움직임은 CSS로 작동 구조를 시험하는 임시 미리보기입니다. Rive 에디터 리그와는 별도입니다.</p></section>
<section class="panel"><h2>리깅을 위한 레이어 규칙</h2><p>머리, 귀, 이마 피부, 주둥이, 양쪽 눈, 두 콧구멍, 짧게 누운 잔털, 몸통, 배, 좌우 팔, 다리, Lv.6 장식은 각각 독립 그룹입니다. 입은 어떤 레벨에도 없습니다.</p></section>
</main><script>
(function(){
const stage=document.getElementById('stage'),sym=document.getElementById('symbol'),label=document.getElementById('stateLabel');
let level=3,mood='idle';
const glyphs={idle:'',happy:'♥',surprise:'!',curious:'?',dizzy:'@',focus:'•',sleepy:'Zzz',confident:'✦',celebrate:'✧',repairing:'⚙',warning:'!'};
function render(){
document.querySelectorAll('[data-art]').forEach(e=>e.style.display=Number(e.dataset.art)===level?'block':'none');
stage.dataset.mood=mood;sym.textContent=glyphs[mood]||'';
document.querySelectorAll('button[data-level]').forEach(e=>e.setAttribute('aria-pressed',String(Number(e.dataset.level)===level)));
document.querySelectorAll('button[data-mood]').forEach(e=>e.setAttribute('aria-pressed',String(e.dataset.mood===mood)));
label.textContent='Lv.'+level+' '+({1:'아기',2:'새싹',3:'성장',4:'단단한',5:'숙련',6:'무게왕'}[level])+' 릴라 · '+({idle:'기본',happy:'행복',surprise:'놀람',curious:'궁금',dizzy:'어지러움',focus:'집중',sleepy:'졸림',confident:'자신감',celebrate:'축하',repairing:'정비',warning:'주의'}[mood]);
}
document.getElementById('levels').addEventListener('click',e=>{const b=e.target.closest('button[data-level]');if(b){level=+b.dataset.level;render()}});
document.getElementById('moods').addEventListener('click',e=>{const b=e.target.closest('button[data-mood]');if(b){mood=b.dataset.mood;render()}});
render();
})();
</script></body></html>'''

def build():
    by_id = {}
    for level in LEVELS:
        svg = level_svg(level)
        path = SVG_DIR / f"lila_level_{level['id']:02}.svg"
        path.write_text(svg, encoding="utf-8")
        ET.fromstring(svg)  # Fail fast for malformed SVG, including broken groups.
        by_id[level["id"]] = svg
        print(f"SVG {path.relative_to(ROOT)} ({len(svg):,} chars)")
    master = level_svg(LEVELS[2], face_only=True)
    (SVG_DIR / "lila_face_master.svg").write_text(master, encoding="utf-8")
    ET.fromstring(master)

    # Manifest stores constraints and pivot hints, not a fake .riv artifact.
    manifest = {
      "version": "2.0.0-alpha",
      "brand": "무게꾼",
      "character": "릴라",
      "phase": 2,
      "asset_status": "editable_svg_source_prototype_not_rive",
      "approved_tuft": "short_laid_2_to_3_strands",
      "mouth": False,
      "artboard": {"width": 600, "height": 620, "viewbox": "0 0 600 620"},
      "levels": [
        {"id": lv["id"], "name": lv["name"], "svg":f"rive_import/lila_level_{lv['id']:02}.svg",
         "body_x": lv["body_x"], "arm_rx": lv["arm_rx"], "leg_rx":lv["leg_rx"], "head_scale": lv["head_scale"],
         "props": ["crown","cape"] if lv["id"] == 6 else []}
        for lv in LEVELS
      ],
      "master_face": "rive_import/lila_face_master.svg",
      "part_groups": LAYERS,
      "pivot_hints": {"head_group": [300, 187], "body_torso": [300, 430], "arm_left": [160, 360],
                      "arm_right":[440, 360], "leg_left":[230, 465], "leg_right":[370, 465], "foot_left":[230, 548], "foot_right":[370, 548], "tuft_A":[300, 52]},
      "moods": MOODS,
      "motion_contract": {
        "idle":"breathing_and_subtle_head_sway",
        "blink":"brief_eye_compression",
        "happy":"soft_eyes_plus_heart_optional",
        "surprise":"enlarged_eyes_plus_exclamation",
        "curious":"eyes_glance_plus_question",
        "dizzy":"brief_wobble_and_spiral",
        "focus":"stillness_and_narrowed_eyes",
        "sleepy":"lowered_lids_and_slow_breath",
        "confident":"subtle_chest_expansion",
        "celebrate":"brief_safe_hop_and_star",
        "repairing":"arm_reaches_tool_to_target_actual_tool_animation_pending",
        "warning":"brief_alert_then_stationary",
      },
      "import_guidance": {"svg_features":["editable_groups","simple_paths","linear_gradients","radial_gradients"],
                          "unsupported_avoided":["filter","embedded_images","mask","stroke-dasharray"]},
      "review_gates": {
        "original_3d_likeness":"manual_review_required",
        "rive_bones_and_states":"not_built",
        "real_riv_file":"not_built",
        "ios_runtime":"not_integrated",
        "production_ready":False
      }
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (OUT / "lila_motion_preview.html").write_text(build_html(by_id),encoding="utf-8")
    print("BUILD OK: 6 levels + face master + manifest + preview")

if __name__ == "__main__":
    build()
