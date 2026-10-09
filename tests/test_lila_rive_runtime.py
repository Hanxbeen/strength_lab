"""QA for authentic original-poster Lila sprites embedded in a Rive binary.

These checks do NOT certify independent limbs, facial animation or 3D mesh.
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

    def test_six_named_artboards(self):
        self.assertEqual([x.get("name") for x in self.scene.findall("Artboard")],
                         [f"LilaLv{i}" for i in range(1,7)])

    def test_embedded_images_from_exact_poster_sprites(self):
        assets=self.scene.findall("ImageAsset")
        self.assertEqual(len(assets),6)
        for i,asset in enumerate(assets,1):
            self.assertEqual(asset.get("file"),f"sprites/lila_lv{i:02}.png")
            self.assertEqual(asset.get("name"),f"Original3D_Lv{i:02}")
            src=Image.open(SOURCE/f"lila_lv{i:02}.webp").convert("RGBA")
            png=Image.open(ASSETS/f"lila_lv{i:02}.png").convert("RGBA")
            self.assertEqual(src.size,png.size)
            self.assertEqual(src.tobytes(),png.tobytes())
            self.assertEqual(png.getchannel("A").getextrema(),(0,255))

    def test_each_artboard_has_only_original_bitmap_layer(self):
        for i,art in enumerate(self.scene.findall("Artboard"),1):
            pictures=art.findall(".//Image")
            self.assertEqual(len(pictures),1)
            self.assertEqual(pictures[0].get("assetId"),f"0:{100+i}")
            self.assertEqual(pictures[0].get("originY"),"1")
            self.assertEqual(art.findall(".//Shape"),[])

    def test_real_animations_only_claim_what_is_implemented(self):
        for art in self.scene.findall("Artboard"):
            machine=art.find("StateMachine")
            self.assertIsNotNone(machine)
            self.assertEqual(art.get("defaultStateMachineId"),machine.get("id"))
            animations={x.get("name"):x for x in art.findall("LinearAnimation")}
            self.assertEqual(set(animations),{"CalmBreath","SoftSway"})
            for anim in animations.values():
                self.assertEqual(anim.get("loopValue"),"1")
        self.assertIn("independent_eye_blink",self.metadata["animation_not_implemented"])

    def test_original_crown_only_on_level_six_visual_source(self):
        self.assertEqual(self.metadata["kind"],"embedded_3D_poster_bitmaps")
        self.assertEqual([x["level"] for x in self.metadata["level_pngs"]],list(range(1,7)))

    def test_bundled_rive_is_real_rive(self):
        self.assertGreater(RIV.stat().st_size,250000)
        self.assertEqual(RIV.read_bytes()[:4],b"RIVE")
        compiled=ROOT/"assets/lila/rive_cli/build/rive_cli.riv"
        if compiled.is_file():
            self.assertEqual(RIV.read_bytes(),compiled.read_bytes())

    def test_debug_studio_and_app_integration(self):
        studio=(ROOT/"apps/ios/MugeMuge/LilaStudioView.swift").read_text()
        self.assertIn("#if DEBUG",studio)
        self.assertIn("ForEach(1...6",studio)
        self.assertNotIn("• 실제 머리 움직임·호흡·눈 깜빡임",studio)
        ios=(ROOT/"apps/ios/MugeMuge/LilaRiveView.swift").read_text()
        self.assertIn('File(source: .local("lila", Bundle.main)',ios)
        self.assertIn("LilaLv",ios)
        self.assertIn("accessibilityReduceMotion",ios)
        home=(ROOT/"apps/ios/MugeMuge/HomeView.swift").read_text()
        self.assertIn("LilaRiveView",home)
        self.assertIn("LilaStudioView()",home)

if __name__=="__main__":
    unittest.main()
