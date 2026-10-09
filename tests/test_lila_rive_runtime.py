"""QA for the actual Rive CLI output and iOS bundle integration."""
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "assets/lila/rive_cli/scene.rml"
RIV = ROOT / "apps/ios/MugeMuge/Resources/lila.riv"
IOS = ROOT / "apps/ios/MugeMuge/LilaRiveView.swift"

class LilaRiveRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tree=ET.parse(ART).getroot()

    def test_six_named_artboards(self):
        artboards=self.tree.findall("Artboard")
        self.assertEqual([x.get("name") for x in artboards],
                         [f"LilaLv{i}" for i in range(1,7)])

    def test_each_level_has_actual_state_machine_and_two_loop_animations(self):
        for art in self.tree.findall("Artboard"):
            machines=art.findall("StateMachine")
            self.assertEqual(len(machines),1)
            self.assertEqual(art.get("defaultStateMachineId"),machines[0].get("id"))
            animations={x.get("name"):x for x in art.findall("LinearAnimation")}
            self.assertEqual(set(animations),{"IdleBreath","NaturalBlink"})
            self.assertEqual(animations["IdleBreath"].get("loopValue"),"1")
            self.assertEqual(animations["NaturalBlink"].get("loopValue"),"1")
            self.assertEqual(len(animations["NaturalBlink"].findall("KeyedObject")),2)

    def test_eye_shape_is_individually_animatable(self):
        for art in self.tree.findall("Artboard"):
            names={node.get("id"):node.get("name") for node in art.iter() if node.get("id")}
            animation=next(x for x in art.findall("LinearAnimation") if x.get("name")=="NaturalBlink")
            eye_targets={names.get(k.get("objectId")) for k in animation.findall("KeyedObject")}
            self.assertEqual(eye_targets,{"eye_left","eye_right"})
            for keyobj in animation.findall("KeyedObject"):
                y=keyobj.find("KeyedProperty")
                self.assertEqual(y.get("propertyKey"),"17")
                self.assertLess(min(float(frame.get("value")) for frame in y.findall("KeyFrameDouble")),0.2)

    def test_no_mouth_or_extraneous_props(self):
        for i,art in enumerate(self.tree.findall("Artboard"),1):
            names=[node.get("name") for node in art.iter() if node.get("name")]
            self.assertFalse(any("mouth" in name.lower() for name in names))
            self.assertEqual("crown_front" in names,i==6)
            self.assertEqual("cape_back" in names,i==6)

    def test_rive_binary_bundled_and_signed_header(self):
        self.assertGreater(RIV.stat().st_size,10000)
        self.assertEqual(RIV.read_bytes()[:4],b"RIVE")

    def test_bundled_rive_matches_cli_compiled_binary(self):
        compiled = ROOT / "assets/lila/rive_cli/build/rive_cli.riv"
        if compiled.is_file():
            self.assertEqual(RIV.read_bytes(), compiled.read_bytes())

    def test_debug_studio_present_and_home_navigates_to_it(self):
        studio=(ROOT/"apps/ios/MugeMuge/LilaStudioView.swift").read_text(encoding="utf-8")
        self.assertIn("#if DEBUG",studio)
        self.assertIn("ForEach(1...6",studio)
        home=(ROOT/"apps/ios/MugeMuge/HomeView.swift").read_text(encoding="utf-8")
        self.assertIn("LilaStudioView()",home)

    def test_swift_ui_reads_local_rive_binary(self):
        swift=IOS.read_text(encoding="utf-8")
        self.assertIn('File(source: .local("lila", Bundle.main)',swift)
        self.assertIn('LilaLv',swift)
        self.assertIn("accessibilityReduceMotion",swift)
        home=(ROOT/"apps/ios/MugeMuge/HomeView.swift").read_text(encoding="utf-8")
        self.assertIn("LilaRiveView",home)

if __name__=="__main__":
    unittest.main()
