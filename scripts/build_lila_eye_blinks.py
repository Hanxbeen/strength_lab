#!/usr/bin/env python3
"""Create clean transparent blinking-eye overlay from original Lila 3D render.

No new gorilla redraw, no mouth. Face patch color is inferred from neighboring
pixels of *the SAME* original high-res source; tiny closed-eye lines can
crossfade via Rive Image.opacity. Only the two eyes are edited.
"""
from pathlib import Path
import json
import math
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
INPUT=ROOT/"assets/lila/poster_upscaled"
OUTPUT=ROOT/"assets/lila/poster_eyelids"

# Measured on source poster sprites (native pixels): two dark pupil components.
# This explicitly ties overlays to the exact source and avoids ambiguous
# heuristics accidentally painting nostrils or the tuft.
EYES={
  1: [(112,99,119,115),(142,99,150,115)],
  2: [(135,127,143,144),(170,127,177,144)],
  3: [(187,121,194,139),(221,122,229,139)],
  4: [(199,122,207,141),(237,122,245,141)],
  5: [(210,127,219,146),(247,127,255,146)],
  6: [(251,137,259,154),(286,137,294,154)]
}
SCALE=4

def smoothed(x):
    t=max(0,min(1,x))
    return t*t*(3-2*t)

def fill_patch(dst,source,bbox):
    sx0,sy0,sx1,sy1=[n*SCALE for n in bbox]
    # Full opaque replacement over pupils, with a smooth skin-color seam.
    feather=7*SCALE
    padx=2*SCALE; pady=2*SCALE
    left=sx0-padx-feather
    right=sx1+padx+feather
    top=sy0-pady-feather
    bottom=sy1+pady+feather
    cx=(sx0+sx1)/2
    cy=(sy0+sy1)/2
    base=source.load();pix=dst.load()
    for y in range(max(0,top),min(source.height,bottom+1)):
        fy=smoothed((y-top)/feather)*smoothed((bottom-y)/feather)
        if fy<1e-5: continue
        # Actual skin samples well beyond eye, at the same vertical position.
        lx=max(0,sx0-(padx+feather)-SCALE)
        rx=min(source.width-1,sx1+(padx+feather)+SCALE)
        def skin_source(sample_x,step):
            # A pupil or tiny nostril can sit at a sampling coordinate.
            # Do not borrow the black nose when reconstructing the eye skin.
            for j in range(0,17*SCALE,2*SCALE):
                xx=max(0,min(source.width-1,sample_x+j*step))
                c=base[xx,y]
                if c[0]>165 and c[1]>132 and c[2]>110 and c[3]>200:
                    return c
            return base[max(0,min(source.width-1,sample_x)),y]
        lp=skin_source(lx,-1)
        rp=skin_source(rx,1)
        for x in range(max(0,left),min(source.width,right+1)):
            fx=smoothed((x-left)/feather)*smoothed((right-x)/feather)
            opacity=int(255*fx*fy)
            if opacity==0:continue
            mix=(x-lx)/max(1,rx-lx)
            mix=max(0,min(1,mix))
            # Avoid visible stamped boxes by borrowing actual adjacent 3D shading.
            rgb=tuple(round((1-mix)*lp[k]+mix*rp[k]) for k in range(3))
            pix[x,y]=(*rgb,opacity)

    # A small charcoal eyelid at the center of the original eye location.
    # Draw curved, minimal eyes (NO mouth/teeth/nose modification).
    width=(sx1-sx0)+2*SCALE
    line_y=cy+1*SCALE
    xstart=round(cx-width*.5)
    xend=round(cx+width*.5)
    draw=ImageDraw.Draw(dst)
    draw.arc((xstart,round(line_y-2.0*SCALE),xend,round(line_y+1.3*SCALE)),
             8,171,fill=(45,42,41,255),width=max(2,round(.9*SCALE)))

def build():
    OUTPUT.mkdir(parents=True,exist_ok=True)
    record=[]
    for lv,boxes in EYES.items():
        p=INPUT/f"lila_lv{lv:02}_4x.png"
        if not p.exists():raise FileNotFoundError(f"Run upscale_lila_posters.py first: {p}")
        src=Image.open(p).convert("RGBA")
        original=Image.open(ROOT/f"assets/lila/poster_sprites/lila_lv{lv:02}.webp").convert("RGBA")
        assert src.size==(original.width*4,original.height*4)
        overlay=Image.new("RGBA",src.size,(0,0,0,0))
        for eye in boxes:
            # verify dark pupil at center to catch shifted source images
            x=(eye[0]+eye[2])//2;y=(eye[1]+eye[3])//2
            pixel=original.getpixel((x,y))
            if max(pixel[:3])>125:raise ValueError(f"Lv{lv}: eye bbox alignment failed at {(x,y)}: {pixel}")
            fill_patch(overlay,src,eye)
        path=OUTPUT/f"lila_lv{lv:02}_blink_overlay.png"
        overlay.save(path,optimize=True)
        data={"level":lv,"source":str(p.relative_to(ROOT)),"overlay":str(path.relative_to(ROOT)),
              "eyes_native":boxes,"size":src.size,
              "nonempty_alpha_bbox":overlay.getchannel("A").getbbox()}
        record.append(data)
        print(f"Blink overlay Lv.{lv}: {path.name}, eyelid groups 2, bbox={data['nonempty_alpha_bbox']}")
    (OUTPUT/"blink_manifest.json").write_text(json.dumps({
      "rendered_from":"the same original sprite enlarged 4x",
      "method":"independent transparent eyelid overlay animated by Rive opacity",
      "no_mouth_added":True,
      "not_real_3d_joint_rig":True,
      "levels":record
    },ensure_ascii=False,indent=2)+"\n")
if __name__=="__main__":
    build()
