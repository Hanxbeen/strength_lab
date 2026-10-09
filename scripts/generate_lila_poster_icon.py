#!/usr/bin/env python3
"""Use the actual 3D Lila face from the poster as the iOS icon, not vector redraw."""
from pathlib import Path
from PIL import Image, ImageFilter
import math

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"assets/lila/poster_upscaled/lila_lv03_4x.png"
DEST=ROOT/"apps/ios/MugeMuge/Resources/Assets.xcassets/AppIcon.appiconset/AppIcon.png"

def create():
    src=Image.open(SOURCE).convert("RGBA")
    # Face (including both ears and 3 original tiny fur wisps) but no body/props.
    face=src.crop((44*4,0,373*4,214*4))
    # Naturally soften lower seam where the original head overlaps shoulders.
    pixels=face.load()
    for y in range(face.height):
        if y<198*4:continue
        factor=max(0,(214*4-y)/(16*4))
        for x in range(face.width):
            r,g,b,a=pixels[x,y]
            pixels[x,y]=(r,g,b,int(a*factor))
    s=1024
    base=Image.new("RGB",(s,s))
    pix=base.load()
    for y in range(s):
        for x in range(s):
            v=math.hypot((x-500)/s,(y-390)/s)
            t=min(1,max(0,v))
            pix[x,y]=(round(250-14*t),round(247-15*t),round(239-18*t))
    layer=Image.new("RGBA",(s,s),(0,0,0,0))
    width=934;height=round(face.height*width/face.width)
    resized=face.resize((width,height),Image.Resampling.LANCZOS)
    x=(s-width)//2;y=160
    # Soft shadow emphasizes 3D shape on matte cream background.
    alpha=Image.new("L",(s,s),0);alpha.paste(resized.getchannel("A"),(x,y+17))
    shade=Image.new("RGBA",(s,s),(20,20,19,0))
    shade.putalpha(alpha.filter(ImageFilter.GaussianBlur(24)).point(lambda a:int(a*.20)))
    layer.alpha_composite(shade)
    layer.alpha_composite(resized,(x,y))
    base=Image.alpha_composite(base.convert("RGBA"),layer).convert("RGB")
    DEST.parent.mkdir(parents=True,exist_ok=True)
    base.save(DEST,optimize=True)
    print(f"Real-poster-face app icon: {DEST} / {DEST.stat().st_size:,} bytes")
if __name__=="__main__":
    create()
