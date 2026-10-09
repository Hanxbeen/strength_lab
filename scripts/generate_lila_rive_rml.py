#!/usr/bin/env python3
"""Compile layered Rilla SVG parts into authentic Rive Markup Language.

Input: assets/lila/rive_import/lila_level_01..06.svg
Output: assets/lila/rive_cli/scene.rml

The Rive CLI builds .riv from this RML. This is *not* a vector SVG
screen recording or an HTML animation.
"""
from __future__ import annotations

import importlib.util
import math
import re
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SVG_DIR = ROOT / "assets/lila/rive_import"
RML_PATH = ROOT / "assets/lila/rive_cli/scene.rml"
SVGNS = "{http://www.w3.org/2000/svg}"

p = importlib.util.spec_from_file_location("lila_svg", ROOT / "scripts/build_lila_phase2_assets.py")
mod = importlib.util.module_from_spec(p)
p.loader.exec_module(mod)

class IDs:
    counter = 100
    def __init__(self):
        self.group_ids = {}
    def next(self):
        self.counter += 1
        return f"0:{self.counter}"

def sub(parent, tag, **props):
    elt = ET.SubElement(parent, tag, {k:str(v) for k,v in props.items() if v is not None})
    return elt

def f(value):
    return str(round(float(value), 5))

def sample_color(grad):
    return {
        "furGrad": ["#555555", "#353535", "#1B1C1D"],
        "furDark": ["#464647", "#2A2A2B", "#1B1C1D"],
        "skinGrad": ["#FFF4E7", "#F3E7DB", "#D8C3B3"],
        "skinMuzzle": ["#FFF8EC", "#F3E7DB", "#E0CAB9"],
        "gold": ["#FFE4A3", "#E4AE50", "#AB792F"],
        "capeRed": ["#CA4C44", "#B53B35", "#89282B"]
    }[grad]

def paint(shape, fill, bounds):
    if not fill or fill.lower() == "none":
        return
    m = re.fullmatch(r"url\(#([^)]+)\)",fill)
    pa = sub(shape, "Fill", name="Fill")
    if m:
        colors=sample_color(m.group(1))
        w,h=bounds
        radius=max(w,h)
        rad=sub(pa,"RadialGradient", name="Matte shading", startX=f(-w*.30), startY=f(-h*.38),
                endX=f(w*.55),endY=f(h*.52))
        for pos,col in zip((0,.48,1),colors):
            sub(rad,"GradientStop",position=pos,colorValue="FF"+col.lstrip("#").upper())
    else:
        v=fill.lstrip("#")
        if len(v)==3:v="".join(x*2 for x in v)
        if len(v)!=6:raise ValueError("Unsupported fill "+fill)
        sub(pa,"SolidColor", name="Color",colorValue="FF"+v.upper())

def parse_path(data):
    """Convert M/L/C/Z absolute commands to vertices + asymmetric tangents."""
    tokens=re.findall(r"[MLCZ]|[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?",data)
    idx=0; pos=(0.,0.); verts=[]; op=None; closed=False
    def read(n):
        nonlocal idx
        a=[float(x) for x in tokens[idx:idx+n]]
        if len(a)!=n:raise ValueError("Path short data: "+data)
        idx+=n
        return a
    while idx<len(tokens):
        if re.fullmatch("[MLCZ]",tokens[idx]):
            op=tokens[idx];idx+=1
        if op=="M":
            x,y=read(2);pos=(x,y);verts=[{"point":pos,"in":None,"out":None}]
            op="L"
        elif op=="L":
            x,y=read(2);pos=(x,y);verts.append({"point":pos,"in":None,"out":None})
        elif op=="C":
            x1,y1,x2,y2,x,y=read(6)
            verts[-1]["out"]=(x1-pos[0],y1-pos[1])
            new={"point":(x,y),"in":(x2-x,y2-y),"out":None}
            if math.hypot(x-verts[0]["point"][0],y-verts[0]["point"][1]) < 1e-5 and idx<len(tokens) and tokens[idx]=="Z":
                verts[0]["in"]=new["in"]
            else:
                verts.append(new)
            pos=(x,y)
        elif op=="Z":
            closed=True
        else:
            raise ValueError("Unsupported opcode: "+str(op))
    return verts,closed or (pos==verts[0]["point"] and len(verts)>2)

def path_shape(parent,node,name,offset,ids):
    data=node.attrib["d"]
    vertices,closed=parse_path(data)
    if not vertices:return
    xs=[v["point"][0] for v in vertices];ys=[v["point"][1] for v in vertices]
    midx=(min(xs)+max(xs))/2;midy=(min(ys)+max(ys))/2
    obj=sub(parent,"Shape",x=f(midx-offset[0]),y=f(midy-offset[1]),name=name,id=ids.next())
    pp=sub(obj,"PointsPath",isClosed=str(closed).lower(),isClockwise="true",name="Path")
    for v in vertices:
        x,y=v["point"]
        iv,ov=v["in"],v["out"]
        kwargs={"x":f(x-midx),"y":f(y-midy)}
        if iv or ov:
            iv=iv or (0,0);ov=ov or (0,0)
            kwargs.update(inRotation=f(math.atan2(iv[1],iv[0])) if iv!=(0,0) else "0",
                         inDistance=f(math.hypot(*iv)),
                         outRotation=f(math.atan2(ov[1],ov[0])) if ov!=(0,0) else "0",
                         outDistance=f(math.hypot(*ov)))
            sub(pp,"CubicDetachedVertex",**kwargs)
        else:
            sub(pp,"StraightVertex",**kwargs)
    paint(obj,node.get("fill"),(max(xs)-min(xs),max(ys)-min(ys)))

def primitive_shape(parent,node,name,offset,ids):
    tag=node.tag.split("}")[-1]
    if tag=="path":
        return path_shape(parent,node,name,offset,ids)
    rot=0
    if tag=="ellipse":
        x=float(node.get("cx"));y=float(node.get("cy"));rx=float(node.get("rx"));ry=float(node.get("ry"))
        w,h=rx*2,ry*2
        typ="Ellipse"
    elif tag=="circle":
        x=float(node.get("cx"));y=float(node.get("cy"));rx=float(node.get("r"));ry=rx
        w,h=rx*2,ry*2;typ="Ellipse"
    elif tag=="rect":
        w=float(node.get("width"));h=float(node.get("height"))
        x=float(node.get("x"))+w/2;y=float(node.get("y"))+h/2
        typ="Rectangle"
    else:
        raise ValueError("Unknown SVG primitive: "+tag)
    transform=node.get("transform","")
    match=re.search(r"rotate\(([-\d.]+)",transform)
    if match:rot=math.radians(float(match.group(1)))
    obj=sub(parent,"Shape",x=f(x-offset[0]),y=f(y-offset[1]),rotation=f(rot),name=name,id=ids.next())
    geo=sub(obj,typ,width=f(w),height=f(h),name="Path")
    if typ=="Rectangle":
        rr=float(node.get("rx","0"))
        geo.set("cornerRadiusTL",f(rr))
    paint(obj,node.get("fill"),(w,h))

def converted_group(parent,g,offset,ids):
    name=g.get("id") or "unnamed"
    group_offset=offset
    nx=ny=0.
    sx=sy=1.
    if name=="head_group":
        # parent head pivot is (300,187); the per-level head offset & scale
        # are always defined in the selected level manifest.
        raise ValueError("use head branch")
    pivot=g.get("data-pivot")
    if name in ("eye_left","eye_right"):
        pivot="271.5,211.5" if name=="eye_left" else "328.5,211.5"
    elif name in ("body_torso", "belly_skin"):
        pivot="300,429" if name=="body_torso" else "300,440"
    if pivot:
        nx,ny=(float(x) for x in pivot.split(","))
        group_offset=(nx,ny)
        nx-=offset[0];ny-=offset[1]
    el=sub(parent,"Node",x=f(nx),y=f(ny),name=name,id=ids.next())
    ids.group_ids[name]=el.get("id")
    for ix,child in reversed(list(enumerate(list(g)))):
        if child.tag==SVGNS+"g":
            converted_group(el,child,group_offset,ids)
        elif child.tag.startswith(SVGNS):
            primitive_shape(el,child,f"{name}_{ix}",group_offset,ids)
    return el

def build_level(parent,level,ids):
    i=level["id"]
    dom=ET.parse(SVG_DIR/f"lila_level_{i:02}.svg").getroot()
    root=next(e for e in dom.iter() if e.get("id")=="character_root")
    body_group=sub(parent,"Node",name="character_root",id=ids.next())
    children=list(root)
    head=next(x for x in children if x.get("id")=="head_group")
    head_params=(level["head_scale"],level["head_offset"])
    # SVG order is back-to-front. RML requires front-to-back.
    for child in reversed(children):
        if child.get("id")=="head_group":
            pivot=(300.,187.)
            scale,head_offset=head_params
            hd=sub(body_group,"Node",x="300",y=f(187+head_offset),scaleX=f(scale),
                   scaleY=f(scale),name="head_group",id=ids.next())
            head_id=hd.get("id")
            for part in reversed(list(child)):
                converted_group(hd,part,pivot,ids)
        else:
            converted_group(body_group,child,(0,0),ids)
    return {"body_id":body_group.get("id"),"head_id":head_id,
            "eyes":(ids.group_ids["eye_left"],ids.group_ids["eye_right"]),
            "breathing":(ids.group_ids["body_torso"],ids.group_ids["belly_skin"])}

def animation(parent,ids,head_id,body_id,eyes,breathing):
    machine_id=ids.next()
    st_idle=ids.next();st_blink=ids.next()
    anim_breath=ids.next();anim_blink=ids.next()
    machine=sub(parent,"StateMachine",name="LilaCompanion",id=machine_id)
    for idx,(label,state_id,animation_id,y) in enumerate((
        ("Breathing",st_idle,anim_breath,70),("Blinking",st_blink,anim_blink,230))):
        layer=sub(machine,"StateMachineLayer",name=label,id=ids.next())
        sub(layer,"AnyState",x="90",y=f(y-105))
        sub(layer,"ExitState",x="450",y=f(y-105))
        entry=sub(layer,"EntryState",x="30",y=f(y))
        sub(entry,"StateTransition",stateToId=state_id)
        sub(layer,"AnimationState",x="270",y=f(y),animationId=animation_id,id=state_id)
    breath=sub(parent,"LinearAnimation",name="IdleBreath",loopValue="1",duration="180",id=anim_breath)
    # head sway is purposely tiny so face parts never float apart
    ob=sub(breath,"KeyedObject",objectId=head_id)
    prop=sub(ob,"KeyedProperty",propertyKey="15")  # rotation
    for frame,rad in ((0,-.014),(45,.017),(90,-.012),(135,.011),(180,-.014)):
        sub(prop,"KeyFrameDouble",frame=frame,value=f(rad),interpolationType="1")
    for breath_part in breathing:
        keyed=sub(breath,"KeyedObject",objectId=breath_part)
        by=sub(keyed,"KeyedProperty",propertyKey="17")
        for frame,value in ((0,1),(45,.976),(90,1),(135,.988),(180,1)):
            sub(by,"KeyFrameDouble",frame=frame,value=f(value),interpolationType="1")
    blink=sub(parent,"LinearAnimation",name="NaturalBlink",loopValue="1",duration="220",id=anim_blink)
    for eye_id in eyes:
        keyed=sub(blink,"KeyedObject",objectId=eye_id)
        by=sub(keyed,"KeyedProperty",propertyKey="17")
        for frame,value in ((0,1),(107,1),(111,.08),(116,1),(219,1)):
            sub(by,"KeyFrameDouble",frame=frame,value=f(value),interpolationType="1")
    return machine_id,anim_blink

def main():
    ids=IDs()
    doc=ET.Element("Rive",version="1",kind="fragment")
    levels=mod.LEVELS
    for level in levels:
        # machine id is appended after artwork; export reads id attributes by reference.
        art=sub(doc,"Artboard",width="600",height="620",name=f"LilaLv{level['id']}",
                id=ids.next(),styleId=ids.next(),x=f((level["id"]-1)*660),y="0")
        sub(art,"LayoutComponentStyle",name="Artboard Style",id=art.get("styleId"))
        ids.group_ids = {}
        refs=build_level(art,level,ids)
        default_id,_=animation(art,ids,refs["head_id"],refs["body_id"],refs["eyes"],refs["breathing"])
        art.set("defaultStateMachineId",default_id)
    ET.indent(doc,space="  ")
    RML_PATH.write_text('<?xml version="1.0" encoding="utf-8"?>\n'+ET.tostring(doc,encoding="unicode")+"\n")
    print(f"Wrote {RML_PATH.relative_to(ROOT)} ({RML_PATH.stat().st_size:,} bytes, {len(levels)} artboards)")
if __name__=="__main__":main()
