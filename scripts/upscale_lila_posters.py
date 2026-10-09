#!/usr/bin/env python3
"""Real-ESRGAN ×4 upscale for existing user-approved 3D Lila sprites.

Model: RealESRGAN_x4plus_anime_6B (RRDBNet, 6 residual blocks)
Source: https://github.com/xinntao/Real-ESRGAN
Weights: official v0.2.2.4 GitHub release, downloaded out of the repo.

Does NOT reconstruct actual 3D geometry, joint layers or genuinely new
photo details; generated high-frequency textures may be hallucinated.
Original user image always preserved separately as the truth reference.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F
from PIL import Image, ImageChops

ROOT=Path(__file__).resolve().parents[1]
SOURCES=ROOT/"assets/lila/poster_sprites"
UPSCALED=ROOT/"assets/lila/poster_upscaled"
WEIGHTS=Path.home()/".cache/lila-upscale/RealESRGAN_x4plus_anime_6B.pth"

class ResidualDenseBlock(nn.Module):
    def __init__(self,nf=64,grow=32):
        super().__init__()
        self.conv1=nn.Conv2d(nf,grow,3,1,1)
        self.conv2=nn.Conv2d(nf+grow,grow,3,1,1)
        self.conv3=nn.Conv2d(nf+2*grow,grow,3,1,1)
        self.conv4=nn.Conv2d(nf+3*grow,grow,3,1,1)
        self.conv5=nn.Conv2d(nf+4*grow,nf,3,1,1)
        self.lrelu=nn.LeakyReLU(.2,inplace=True)
    def forward(self,x):
        a=self.lrelu(self.conv1(x))
        b=self.lrelu(self.conv2(torch.cat((x,a),1)))
        c=self.lrelu(self.conv3(torch.cat((x,a,b),1)))
        d=self.lrelu(self.conv4(torch.cat((x,a,b,c),1)))
        e=self.conv5(torch.cat((x,a,b,c,d),1))
        return x+e*.2

class RRDB(nn.Module):
    def __init__(self,nf=64,grow=32):
        super().__init__()
        self.rdb1=ResidualDenseBlock(nf,grow)
        self.rdb2=ResidualDenseBlock(nf,grow)
        self.rdb3=ResidualDenseBlock(nf,grow)
    def forward(self,x):
        return x+.2*self.rdb3(self.rdb2(self.rdb1(x)))

class RRDBNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv_first=nn.Conv2d(3,64,3,1,1)
        self.body=nn.Sequential(*(RRDB(64,32) for _ in range(6)))
        self.conv_body=nn.Conv2d(64,64,3,1,1)
        self.conv_up1=nn.Conv2d(64,64,3,1,1)
        self.conv_up2=nn.Conv2d(64,64,3,1,1)
        self.conv_hr=nn.Conv2d(64,64,3,1,1)
        self.conv_last=nn.Conv2d(64,3,3,1,1)
        self.lrelu=nn.LeakyReLU(.2,inplace=True)
    def forward(self,x):
        feat=self.conv_first(x)
        feat=feat+self.conv_body(self.body(feat))
        feat=self.lrelu(self.conv_up1(F.interpolate(feat,scale_factor=2,mode="nearest")))
        feat=self.lrelu(self.conv_up2(F.interpolate(feat,scale_factor=2,mode="nearest")))
        return self.conv_last(self.lrelu(self.conv_hr(feat)))

def upscale_4x(img,net,device,tile=192,padding=16):
    # Model on composited cream RGB, preserve the real alpha matte separately.
    base=Image.new("RGB",img.size,(247,243,235))
    base.paste(img,mask=img.getchannel("A"))
    rgb=np.asarray(base,dtype=np.uint8)
    h,w=rgb.shape[:2]
    out=np.zeros((h*4,w*4,3),dtype=np.uint8)
    with torch.inference_mode():
        for top in range(0,h,tile):
            for left in range(0,w,tile):
                y0=max(0,top-padding)
                x0=max(0,left-padding)
                y1=min(h,top+tile+padding)
                x1=min(w,left+tile+padding)
                patch=rgb[y0:y1,x0:x1]
                x=torch.from_numpy(patch.copy()).permute(2,0,1).unsqueeze(0).to(device).float()/255.
                pred=net(x).clamp(0,1).mul(255).round().byte().squeeze(0).permute(1,2,0).cpu().numpy()
                ty=top-y0;tx=left-x0
                height=min(tile,h-top);width=min(tile,w-left)
                out[top*4:(top+height)*4,left*4:(left+width)*4]=pred[ty*4:(ty+height)*4,tx*4:(tx+width)*4]
                del x,pred
    upscale_alpha=img.getchannel("A").resize((w*4,h*4),Image.Resampling.LANCZOS)
    final=Image.fromarray(out,"RGB").convert("RGBA")
    final.putalpha(upscale_alpha)
    return final

def run(levels,tile=192):
    if not WEIGHTS.exists():
        raise FileNotFoundError(f"Download official RealESRGAN 6B weights to {WEIGHTS}")
    device="mps" if torch.backends.mps.is_available() else "cpu"
    net=RRDBNet()
    source=torch.load(WEIGHTS,map_location="cpu",weights_only=True)
    state=source.get("params_ema",source.get("params",source))
    net.load_state_dict(state,strict=True)
    net.eval().to(device)
    UPSCALED.mkdir(parents=True,exist_ok=True)
    metadata={"model":"RealESRGAN_x4plus_anime_6B","scale":4,
              "model_source":"https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth",
              "algorithm":"RRDBNet_6B_MPS_or_CPU","device":device,
              "caution":"AI super-resolution is a plausible reconstruction, not actual original 3D detail.",
              "images":[]}
    for level in levels:
        orig=Image.open(SOURCES/f"lila_lv{level:02}.webp").convert("RGBA")
        new=upscale_4x(orig,net,device,tile)
        path=UPSCALED/f"lila_lv{level:02}_4x.png"
        new.save(path,optimize=True)
        check=new.resize(orig.size,Image.Resampling.LANCZOS)
        diff=ImageChops.difference(check.convert("RGB"),orig.convert("RGB"))
        d=np.asarray(diff).mean()
        metadata["images"].append({
            "level":level,"source_size":orig.size,"output_size":new.size,
            "file":str(path.relative_to(ROOT)),"mean_rgb_downsample_difference":round(float(d),2),
            "source_alpha_preserved":True
        })
        print(f"UPSCALED Lv.{level}: {orig.size} → {new.size}, downsample RGB difference {d:.1f} / 255",flush=True)
    (UPSCALED/"upscale_manifest.json").write_text(
        json.dumps(metadata,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--levels",nargs="+",type=int,default=list(range(1,7)))
    parser.add_argument("--tile",type=int,default=192)
    args=parser.parse_args()
    run(args.levels,args.tile)
