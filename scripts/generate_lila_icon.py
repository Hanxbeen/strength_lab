#!/usr/bin/env python3
"""LEGACY flat SVG-style icon generator; NOT the approved 3D Lila icon.

Production icon comes from scripts/generate_lila_poster_icon.py.
Generate the native iOS Lila face icon (transparent-free 1024px PNG).
Self-contained Pillow renderer; avoids screen captures and trademarked assets.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import math

SIZE = 1024

def bezier(a,b,c,d,steps=24):
    pts=[]
    for i in range(steps+1):
        t=i/steps;u=1-t
        pts.append(((u**3)*a[0]+3*(u**2)*t*b[0]+3*u*(t**2)*c[0]+t**3*d[0],
                    (u**3)*a[1]+3*(u**2)*t*b[1]+3*u*(t**2)*c[1]+t**3*d[1]))
    return pts

def shape_mask(curves):
    p=[]
    for a,b,c,d in curves:
        p+=bezier(a,b,c,d)
    m=Image.new('L',(SIZE,SIZE),0)
    ImageDraw.Draw(m).polygon(p,fill=255)
    return m

def oval_mask(bounds):
    m=Image.new('L',(SIZE,SIZE),0)
    ImageDraw.Draw(m).ellipse(bounds,fill=255)
    return m

def shaded(base,mask,top,bottom,light=(-.36,-.42),shine=.11):
    pix=Image.new('RGB',(SIZE,SIZE))
    px=pix.load()
    for y in range(SIZE):
        vertical=y/SIZE
        for x in range(SIZE):
            vignette=((x-SIZE*.5)**2+(y-SIZE*.30)**2)**.5 / SIZE
            t=min(1,max(0, vertical*.8 + .22*vignette + (x/SIZE-.5)*.045))
            w=shine*max(0,1-math.hypot((x/SIZE-light[0]-.5)*.8,(y/SIZE-light[1]-.5)*.8))
            px[x,y]=tuple(int(max(0,min(255,top[k]*(1-t)+bottom[k]*t+w*255))) for k in range(3))
    base.paste(pix,(0,0),mask)

def shadow_under(img,mask,blur=18,offset=(5,12),opacity=80):
    shifted=Image.new('L',(SIZE,SIZE),0)
    shifted.paste(mask,offset)
    alpha=shifted.filter(ImageFilter.GaussianBlur(blur)).point(lambda a:int(a*opacity/255))
    overlay=Image.new('RGBA',(SIZE,SIZE),(10,8,7,0))
    overlay.putalpha(alpha)
    img.alpha_composite(overlay)

# Warm matte app-icon background, no alpha (iOS applies icon corner clipping).
im=Image.new('RGBA',(SIZE,SIZE),(245,239,225,255))
b=Image.new('RGBA',(SIZE,SIZE))
p=b.load()
for y in range(SIZE):
    for x in range(SIZE):
        r=math.hypot((x-440)/960,(y-280)/1024)
        a=max(0,min(1,r))
        p[x,y]=(int(249-15*a),int(245-14*a),int(234-15*a),255)
im.alpha_composite(b)

# Two outer ears behind the head.
for cx in (176,848):
    mask=oval_mask((cx-87,420,cx+87,610))
    shadow_under(im,mask,12,(3,10),90)
    shaded(im,mask,(65,65,65),(24,24,25),shine=.025)
for cx in (173,851):
    mask=oval_mask((cx-45,460,cx+45,577))
    shaded(im,mask,(47,46,46),(29,29,30),shine=.01)

# Head silhouette: tall round skull, slightly flattened base.
head=shape_mask([
 ((512,120),(305,103),(212,228),(204,425)),
 ((204,425),(156,585),(199,810),(310,917)),
 ((310,917),(383,989),(642,989),(714,917)),
 ((714,917),(839,810),(868,596),(820,425)),
 ((820,425),(802,222),(708,103),(512,120)),
])
shadow_under(im,head,20,(7,18),125)
shaded(im,head,(65,65,65),(27,27,29),light=(-.20,-.16),shine=.045)

# Soft tuft: 3 tapered petal-like hairs, NOT spherical buns.
tufts=[
  [((496,165),(454,125),(453,86),(472,78)),
   ((472,78),(492,80),(508,108),(513,143)),
   ((513,143),(506,153),(500,160),(496,165))],
  [((511,155),(502,94),(513,56),(538,61)),
   ((538,61),(552,76),(540,118),(528,152)),
   ((528,152),(520,154),(514,155),(511,155))],
  [((525,157),(545,100),(578,93),(588,111)),
   ((588,111),(592,137),(559,160),(525,157))],
]
for seg in tufts:
    mm=shape_mask(seg)
    shaded(im,mm,(59,59,59),(30,30,31),shine=.022)

# Cream forehead patch that shapes the iconic eye region.
forehead=shape_mask([
 ((333,526),(326,402),(375,320),(450,340)),
 ((450,340),(483,338),(494,365),(512,388)),
 ((512,388),(543,340),(577,328),(616,348)),
 ((616,348),(700,329),(713,428),(692,540)),
 ((692,540),(664,596),(580,618),(512,610)),
 ((512,610),(431,616),(359,597),(333,526)),
])
shadow_under(im,forehead,8,(1,6),95)
shaded(im,forehead,(255,247,231),(233,213,191),light=(-.27,-.18),shine=.045)

# Wide protruding muzzle, no mouth. Classic Rilla's soft double-cheek profile.
muzzle=shape_mask([
 ((324,564),(354,516),(412,508),(465,532)),
 ((465,532),(501,539),(504,535),(512,535)),
 ((512,535),(541,530),(576,517),(614,519)),
 ((614,519),(688,495),(726,553),(720,630)),
 ((720,630),(711,740),(616,824),(513,821)),
 ((513,821),(391,825),(307,736),(304,637)),
 ((304,637),(302,603),(307,578),(324,564)),
])
shadow_under(im,muzzle,11,(3,11),92)
shaded(im,muzzle,(255,248,233),(232,211,190),light=(-.35,-.26),shine=.05)

# Two simple oval eyes, strategically above muzzle's upper silhouette.
eyes=ImageDraw.Draw(im)
eyes.ellipse((435,444,458,505),fill=(27,29,29,255))
eyes.ellipse((566,444,589,505),fill=(27,29,29,255))
# Two tiny nostrils. No mouth or eyebrows.
eyes.ellipse((495,566,508,579),fill=(37,36,35,255))
eyes.ellipse((518,566,531,579),fill=(37,36,35,255))

out=Path(__file__).resolve().parent.parent/'apps/ios/MugeMuge/Resources/Assets.xcassets/AppIcon.appiconset/AppIcon.png'
out.parent.mkdir(parents=True,exist_ok=True)
im.convert('RGB').save(out,optimize=True)
print(f"ICON={out} SIZE={out.stat().st_size} px={im.size}")
