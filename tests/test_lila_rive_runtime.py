"""QA for true Rive 4× upscaled 3D poster sprites + independent blink overlays.

These checks cannot certify genuine articulated 3D motion or texture accuracy.
"""
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SCENE = ROOT / "assets/lila/rive_cli/scene.rml"
SOURCE = ROOT / "assets/lila/poster_sprites"
ASSETS = ROOT / "assets/lila/rive_cli/sprites"
RIV = ROOT / "apps/ios/MugeMuge/Resources/lila.riv"

class LilaRiveRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scene = ET.parse(SCENE).getroot()
        cls.metadata = json.loads((SOURCE/"implementation_manifest.json").read_text())
        cls.upscaled = json.loads((ROOT/"assets/lila/poster_upscaled/upscale_manifest.json").read_text())

    def test_six_named_artboards(self):
        self.assertEqual([x.get("name") for x in self.scene.findall("Artboard")],
                         [f"LilaLv{i}" for i in range(1,7)])

    def test_embedded_high_resolution_original_design(self):
        assets=self.scene.findall("ImageAsset")
        self.assertEqual(len(assets),12)
        for i in range(1,7):
            base=next(a for a in assets if a.get("name")==f"Upres3D_Lv{i:02}")
            blink=next(a for a in assets if a.get("name")==f"EyeLidLayer_Lv{i:02}")
            self.assertEqual(base.get("file"),f"sprites/lila_lv{i:02}.png")
            self.assertEqual(blink.get("file"),f"sprites/lila_lv{i:02}_blink_overlay.png")
            with Image.open(SOURCE/f"lila_lv{i:02}.webp") as src:
                expected_size=(src.width*4,src.height*4)
            with Image.open(ASSETS/f"lila_lv{i:02}.png") as image_file:
                up=image_file.convert("RGBA")
            with Image.open(ASSETS/f"lila_lv{i:02}_blink_overlay.png") as image_file:
                lid=image_file.convert("RGBA")
            self.assertEqual(up.size,expected_size)
            self.assertEqual(lid.size,up.size)
            self.assertEqual(up.getchannel("A").getextrema(),(0,255))
            self.assertIsNotNone(lid.getchannel("A").getbbox())
            self.assertLess(lid.getchannel("A").getbbox()[3]-lid.getchannel("A").getbbox()[1],src.height*2)

    def test_each_artboard_has_two_image_layers_and_scaled_coordinates(self):
        for i,art in enumerate(self.scene.findall("Artboard"),1):
            images=art.findall(".//Image")
            self.assertEqual(len(images),2)
            layers={x.get("name"):x for x in images}
            self.assertEqual(layers["original_poster_character"].get("assetId"),f"0:{100+i}")
            self.assertEqual(layers["eye_blink_layer"].get("assetId"),f"0:{200+i}")
            self.assertEqual(layers["eye_blink_layer"].get("opacity"),"0")
            for p in images:
                self.assertEqual(float(p.get("scaleX")),0.25)
                self.assertEqual(float(p.get("scaleY")),0.25)
                self.assertEqual(p.get("originY"),"1")
            self.assertEqual(art.findall(".//Shape"),[])

    def test_all_six_states_have_actual_eye_overlay_animation(self):
        for i,art in enumerate(self.scene.findall("Artboard"),1):
            machine=art.find("StateMachine")
            self.assertIsNotNone(machine)
            self.assertEqual(art.get("defaultStateMachineId"),machine.get("id"))
            self.assertEqual(len(machine.findall("StateMachineLayer")),3)
            animations={x.get("name"):x for x in art.findall("LinearAnimation")}
            self.assertEqual(set(animations),{"CalmBreath","SoftSway","NaturalBlink"})
            for anim in animations.values():
                self.assertEqual(anim.get("loopValue"),"1")
            blink=animations["NaturalBlink"]
            target=blink.find("KeyedObject")
            self.assertEqual(target.get("objectId"),f"0:{i*1000+6}")
            opacity=target.find("KeyedProperty")
            self.assertEqual(opacity.get("propertyKey"),"18")
            values={int(k.get("frame")):float(k.get("value")) for k in opacity.findall("KeyFrameDouble")}
            self.assertEqual(values[0],0)
            self.assertEqual(values[105],1)
            self.assertEqual(values[108],1)
            self.assertEqual(values[112],0)

    def test_source_only_still_no_3d_model_or_articulated_limb_claim(self):
        self.assertEqual(self.metadata["kind"],"embedded_3D_poster_bitmaps")
        self.assertEqual([x["level"] for x in self.metadata["level_pngs"]],list(range(1,7)))
        self.assertIn("articulated_sbd_exercise",self.metadata["animation_not_implemented"])

    def test_upscale_metadata_preserves_provenance(self):
        self.assertEqual(self.upscaled["scale"],4)
        self.assertIn("RealESRGAN",self.upscaled["model"])
        self.assertEqual(len(self.upscaled["images"]),6)

    def test_bundled_rive_is_real_rive_and_current_binary(self):
        self.assertGreater(RIV.stat().st_size,1000000)
        self.assertEqual(RIV.read_bytes()[:4],b"RIVE")
        compiled=ROOT/"assets/lila/rive_cli/build/rive_cli.riv"
        if compiled.is_file():
            self.assertEqual(RIV.read_bytes(),compiled.read_bytes())

    def test_debug_studio_and_app_integration(self):
        studio=(ROOT/"apps/ios/MugeMuge/LilaStudioView.swift").read_text()
        self.assertIn("#if DEBUG",studio)
        self.assertIn("ForEach(1...6",studio)
        ios=(ROOT/"apps/ios/MugeMuge/LilaRiveView.swift").read_text()
        self.assertIn('File(source: .local("lila", Bundle.main)',ios)
        self.assertIn("LilaLv",ios)
        self.assertIn("accessibilityReduceMotion",ios)
        home=(ROOT/"apps/ios/MugeMuge/HomeView.swift").read_text()
        self.assertIn("LilaRiveView",home)
        self.assertIn("LilaStudioView()",home)

if __name__=="__main__":
    unittest.main()
