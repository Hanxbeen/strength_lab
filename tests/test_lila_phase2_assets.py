"""Structural QA for Phase 2 editable artwork; does not certify .riv/3D likeness."""
import json
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
ART = BASE / "assets/lila"
NS = "{http://www.w3.org/2000/svg}"

class LilaPhase2AssetsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = json.loads((ART/"manifest.json").read_text(encoding="utf-8"))
        cls.level_svg = []
        for lv in cls.spec["levels"]:
            p=ART/lv["svg"]
            cls.level_svg.append(ET.parse(p).getroot())

    def test_all_six_levels_unique_and_ordered(self):
        self.assertEqual([x["id"] for x in self.spec["levels"]],list(range(1,7)))
        self.assertEqual(len(self.level_svg),6)
        self.assertEqual([root.get("data-level") for root in self.level_svg], [str(x) for x in range(1,7)])

    def test_mouthless_mascot_no_hidden_mouth_node(self):
        for svg in self.level_svg:
            self.assertFalse(any("mouth" in (node.get("id","").lower()) for node in svg.iter()))
            self.assertEqual(len([x for x in svg.iter() if x.get("id") in ("eye_left","eye_right")]),2)
            self.assertEqual(len([x for x in svg.iter() if x.get("id") in ("nostril_left","nostril_right")]),2)

    def test_laid_tuft_A_present_on_all_levels(self):
        self.assertEqual(self.spec["approved_tuft"],"short_laid_2_to_3_strands")
        for svg in self.level_svg:
            tufts=[n for n in svg.iter() if n.get("id")=="tuft_A"]
            self.assertEqual(len(tufts),1)
            self.assertEqual(len([n for n in tufts[0] if n.tag.endswith("path")]),3)

    def test_crown_and_cape_only_on_level_six(self):
        for i,svg in enumerate(self.level_svg,1):
            ids={n.get("id") for n in svg.iter() if n.get("id")}
            self.assertEqual("crown_front" in ids,i==6)
            self.assertEqual("cape_back" in ids,i==6)
            self.assertEqual(self.spec["levels"][i-1]["props"], ["crown","cape"] if i==6 else [])

    def test_same_face_geometry_for_all_levels(self):
        faceparts=("head_skull","forehead_skin","muzzle_skin","eye_left","eye_right","nostril_left","nostril_right","tuft_A")
        snapshots=[]
        for svg in self.level_svg:
            pieces=[]
            for part in faceparts:
                group=next(n for n in svg.iter() if n.get("id")==part)
                pieces.append(ET.tostring(group,encoding="unicode"))
            snapshots.append(pieces)
        self.assertTrue(all(snapshot==snapshots[0] for snapshot in snapshots))

    def test_levels_have_real_body_shape_changes(self):
        # Upward scaling of a single image is NOT sufficient: arms/legs/chest dimensions vary independently.
        lv=self.spec["levels"]
        for i in (2,3,4):
            self.assertGreater(lv[i]["arm_rx"],lv[i-1]["arm_rx"] if i!=2 else 0)
        self.assertEqual(lv[4]["arm_rx"],lv[5]["arm_rx"])
        self.assertEqual(lv[4]["leg_rx"],lv[5]["leg_rx"])
        self.assertGreater(lv[3]["body_x"],lv[2]["body_x"])
        self.assertGreater(lv[4]["body_x"],lv[3]["body_x"])

    def test_leg_and_foot_groups_independent(self):
        for svg in self.level_svg:
            ids={n.get("id") for n in svg.iter() if n.get("id")}
            for part in ("leg_left", "leg_right", "foot_left", "foot_right"):
                self.assertIn(part, ids)

    def test_svg_avoids_unsupported_import_features(self):
        for svg in self.level_svg:
            self.assertEqual(svg.tag,NS+"svg")
            self.assertEqual(svg.get("viewBox"),"0 0 600 620")
            self.assertFalse(any(n.tag.endswith(("filter","image","mask","text","foreignObject")) for n in svg.iter()))
            # Rive import converts gradients to native editable artwork; leave colors on paths.
            self.assertFalse(any("filter" in n.attrib or "mask" in n.attrib for n in svg.iter()))

    def test_state_preview_has_all_controls_and_motion_accessibility(self):
        self.assertEqual(len(self.spec["moods"]),11)
        ids=[x["id"] for x in self.spec["moods"]]
        self.assertEqual(len(ids),len(set(ids)))
        page=(ART/"lila_motion_preview.html").read_text(encoding="utf-8")
        self.assertIn("prefers-reduced-motion",page)
        self.assertIn('id="stage"',page)
        self.assertEqual(page.count('class="level"'),6)
        self.assertEqual(page.count('class="mood"'),11)

    def test_rive_truthful_state(self):
        self.assertEqual(self.spec["asset_status"],"editable_svg_source_prototype_not_rive")
        self.assertFalse(self.spec["review_gates"]["production_ready"])
        self.assertEqual(self.spec["review_gates"]["real_riv_file"],"not_built")

if __name__=="__main__":
    unittest.main()
