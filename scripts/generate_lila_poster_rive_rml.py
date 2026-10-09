#!/usr/bin/env python3
"""Build a true Rive file from the user's poster-derived 3D Lila sprites.

The user-selected images stay intact as embedded image assets, not redrawn SVG.
Only tiny full-character breath/sway are animated until independent hi-res layers
are produced. This does not claim eye blinks, limb rigging, or a real 3D mesh.
"""
from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image as PILImage

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets/lila/poster_sprites"
TARGET = ROOT / "assets/lila/rive_cli"
RASTER = TARGET / "sprites"
ARTBOARD_W, ARTBOARD_H, FLOOR_Y = 600, 620, 562

def element(parent, tag, **attributes):
    return ET.SubElement(parent, tag, {
        key: str(value) for key, value in attributes.items() if value is not None
    })

def keyed(animation, object_id, property_key, values):
    o = element(animation, "KeyedObject", objectId=object_id)
    p = element(o, "KeyedProperty", propertyKey=property_key)
    for frame, value in values:
        element(p, "KeyFrameDouble", frame=frame,
                value=value, interpolationType="1")

def build():
    if not SOURCE.is_dir():
        raise RuntimeError(f"Missing authorized character cutouts: {SOURCE}")
    RASTER.mkdir(parents=True, exist_ok=True)
    root = ET.Element("Rive",version="1",kind="fragment")
    data = []
    for level in range(1,7):
        source = SOURCE / f"lila_lv{level:02}.webp"
        if not source.is_file():
            raise RuntimeError(f"Missing Lv{level} original sprite {source}")
        img = PILImage.open(source).convert("RGBA")
        if img.getchannel("A").getextrema() != (0,255):
            raise ValueError(f"Lv{level} not a transparent original cutout")
        out = RASTER / f"lila_lv{level:02}.png"
        img.save(out,optimize=True)
        data.append({
            "level":level,"source":str(source.relative_to(ROOT)),
            "width":img.width,"height":img.height,
            "sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
            "png":str(out.relative_to(ROOT))
        })
        print(f"Original 3D sprite Lv.{level}: {img.width}x{img.height}")
    for d in data:
        element(root,"ImageAsset",id=f"0:{100+d['level']}",
                name=f"Original3D_Lv{d['level']:02}",
                file=f"sprites/lila_lv{d['level']:02}.png")
    for d in data:
        level=d["level"]
        board=element(root,"Artboard",id=f"0:{level*1000+1}",
                      width=ARTBOARD_W,height=ARTBOARD_H,
                      name=f"LilaLv{level}",styleId=f"0:{level*1000+2}",
                      defaultStateMachineId=f"0:{level*1000+5}",
                      x=(level-1)*650,y=0)
        element(board,"LayoutComponentStyle",name="Artboard Style",
                id=f"0:{level*1000+2}")
        pivot=element(board,"Node",id=f"0:{level*1000+3}",
                      x=300,y=FLOOR_Y,name="character_root_original3D")
        element(pivot,"Image",id=f"0:{level*1000+4}",
                x=0,y=0,assetId=f"0:{100+level}",
                originX=".5",originY="1",
                name="original_poster_character")
        machine=element(board,"StateMachine",id=f"0:{level*1000+5}",name="LilaCompanion")
        for i,(state_name,anim_id) in enumerate((
            ("Breathing",f"0:{level*1000+11}"),
            ("Sway",f"0:{level*1000+12}")
        )):
            layer=element(machine,"StateMachineLayer",id=f"0:{level*1000+20+i}",
                          name=state_name)
            entry=element(layer,"EntryState",x=30,y=110+i*130)
            element(entry,"StateTransition",
                    stateToId=f"0:{level*1000+30+i}")
            element(layer,"AnimationState",id=f"0:{level*1000+30+i}",
                    x=250,y=110+i*130,animationId=anim_id)
        breath=element(board,"LinearAnimation",id=f"0:{level*1000+11}",
                       name="CalmBreath",loopValue=1,duration=180)
        keyed(breath,pivot.get("id"),"17",[
            (0,"1"),(45,".993"),(90,"1"),(135,".993"),(180,"1")])
        sway=element(board,"LinearAnimation",id=f"0:{level*1000+12}",
                     name="SoftSway",loopValue=1,duration=300)
        keyed(sway,pivot.get("id"),"15",[
            (0,"-.008"),(80,".008"),(160,"-.006"),
            (240,".007"),(300,"-.008")])
    ET.indent(root,space="  ")
    path=TARGET/"scene.rml"
    path.write_text('<?xml version="1.0" encoding="utf-8"?>\n'+
                    ET.tostring(root,encoding="unicode")+"\n",encoding="utf-8")
    meta={
        "version":"poster-derived-Rive-v1",
        "kind":"embedded_3D_poster_bitmaps",
        "source_reference":"assets/lila/poster_sprites/poster_reference.jpeg",
        "reference_is_3D_render_not_editable_3D_model":True,
        "level_pngs":data,
        "artboard":"600x620","floor_y":FLOOR_Y,
        "animation_implemented":["calm_full_body_breath","subtle_full_body_sway"],
        "animation_not_implemented":["independent_eye_blink","emotion_states",
                                     "articulated_sbd_exercise","viewpoint_rotation"],
        "quality_gate":"user_reference_match_required_on_physical_iphone"
    }
    (SOURCE/"implementation_manifest.json").write_text(
        json.dumps(meta,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"
    )
    print(f"RML generated: {path.relative_to(ROOT)} with 6 embedded original-sprite artboards")

if __name__=="__main__":
    build()
