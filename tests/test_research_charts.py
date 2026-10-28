"""Compare chart payloads with cached primary text and table cells."""
import copy
import hashlib
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from backend.research_charts import chart_for

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/research/coaching"

def load(name):
    return json.loads((DATA / name).read_text())

class ResearchChartTests(unittest.TestCase):
    def test_helms_values_match_abstract_not_inconsistent_post_test(self):
        source=load("helms2018.json")
        result=chart_for(source,"RPEG")
        self.assertTrue(result["available"])
        raw=(DATA/"sources/PMC5877330.xml").read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),result["source"]["source_sha256"])
        abstract="".join(ET.fromstring(raw).find(".//abstract").itertext())
        for point in result["points"]:
            # The original abstract reports every mean change and SD pair.
            self.assertIn(f'{point["value"]:.2f} ± {point["sd"]:.2f}',abstract)
            self.assertEqual(point["selected"],point["arm"]=="RPEG")
        self.assertEqual(len(result["points"]),6)
        self.assertNotIn("post_value",str(result["points"]))
        self.assertIn("표준편차",str(result["limits"]))

    def test_metd_intervals_match_results_and_keep_studies_separate(self):
        source=load("metd2021.json")
        result=chart_for(source,"MAX_BOFF")
        raw=(DATA/"sources/PMC8435792.xml").read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),result["source"]["source_sha256"])
        text="".join(ET.fromstring(raw).find(".//sec[@id='sec44']").itertext())
        self.assertEqual(result["statistic"],"posterior_mode_with_95_percent_hdi")
        self.assertEqual(len(result["points"]),4)
        self.assertEqual({p["panel_id"] for p in result["points"]},{"study_3","study_4"})
        for point in result["points"]:
            exact=f'{point["value"]} kg (95% HDI, {point["interval_lower"]}–{point["interval_upper"]} kg)'
            self.assertIn(exact,text)
            self.assertEqual(point["prior_from_study_3"],point["study"]==4 and point["arm"]=="MAX_BOFF")
            self.assertNotIn("sd",point)
        self.assertEqual(sum(p["n"] for p in result["points"]),25)

    def test_per_all_individual_lifts_match_primary_table_without_conflicting_total(self):
        result=chart_for(load("pilot2018-source-labels.json"),"PER_SOURCE_LABELS")
        raw=(DATA/"sources/PMC6162635.xml").read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),result["source"]["source_sha256"])
        table=ET.fromstring(raw).find(".//table-wrap[@id='sports-06-00086-t004']")
        rows=[["".join(cell.itertext()).strip() for cell in row] for row in table.findall(".//tr")]
        actual={}
        exercise=None
        mapping={"SQ":"barbell_back_squat","BP":"barbell_bench_press","DL":"barbell_deadlift"}
        for row in rows:
            if row[0] in mapping:exercise=mapping[row[0]]
            if row[0]=="Total":exercise=None
            if exercise and row[0] in ("Pre 1RM (kg)","Post 1RM (kg)"):
                time="pre" if row[0].startswith("Pre") else "post"
                for index,value in enumerate(row[1:],1):
                    actual[(exercise,str(index),time)]=float(value)
        self.assertEqual(len(result["points"]),18)
        for point in result["points"]:
            self.assertEqual(point["value"],actual[(point["exercise_id"],point["participant_id"],point["timepoint"])])
        self.assertEqual(len(actual),18)
        self.assertFalse(result["interpolation_allowed"])
        self.assertFalse(result["population"]["comparator_displayed"])

    def test_petrizzo_counts_preserve_full_denominator_and_no_frequency_effect_comparison(self):
        two=chart_for(load("petrizzo2018-four-lift-2d.json"),"FOUR_LIFT")
        three=chart_for(load("petrizzo2018-four-lift-3d.json"),"FOUR_LIFT")
        raw=(DATA/"sources/JEPonlineOCTOBER2018_Petrizzo.pdf").read_bytes()
        self.assertTrue(raw.startswith(b"%PDF"))
        self.assertEqual(hashlib.sha256(raw).hexdigest(),two["source"]["source_sha256"])
        review=load("reviews/novice-sbd-20261016.json")["reports"][1]
        self.assertEqual(two["points"],three["points"])
        self.assertEqual(two["metric"],"participant_flow")
        self.assertEqual(sum(p["value"] for p in two["points"]),58)
        self.assertTrue(all(p["denominator"]==58 for p in two["points"]))
        values={p["category"]:p["value"] for p in two["points"]}
        self.assertEqual(values["completed_12_weeks"],review["completion"]["completed_12_weeks"])
        self.assertEqual(values["progression_stalled"],review["completion"]["stalled"])
        self.assertEqual(values["other_excluded_dropouts"],18)
        self.assertEqual(two["population"]["analyzed"],40)

    def test_unreported_effects_and_unknown_versions_are_not_zero_or_forecasts(self):
        for name,reason in (
            ("mugemuge-sbd-foundation-v1.json","product_synthesis_not_directly_tested"),
            ("mugemuge-sbd-trained-v1.json","product_synthesis_not_directly_tested"),
            ("mugemuge-entry-learning-v2.json","education_not_efficacy_trial")):
            result=chart_for(load(name))
            self.assertFalse(result["available"])
            self.assertEqual(result["reason"],reason)
            self.assertEqual(result["points"],[])
            self.assertIsNone(result["metric"])
        for name,field in (("helms2018.json","source_sha256"),("pilot2018-source-labels.json","source_sha256")):
            source=load(name);source[field]="changed"
            self.assertEqual(chart_for(source)["reason"],"source_revision_unreviewed")
        source=load("metd2021.json");source["citation"]["source_sha256"]="changed"
        self.assertFalse(chart_for(source)["available"])
        self.assertEqual(chart_for({"id":"unknown"})["reason"],"source_not_reviewed")
        self.assertEqual(chart_for(load("helms2018.json"),"AMRAP")["reason"],"arm_not_reviewed")

    def test_projection_is_pure_and_mutations_do_not_leak_between_arms(self):
        source=load("metd2021.json");before=copy.deepcopy(source)
        first=chart_for(source,"MAX");first["points"][0]["value"]=-999
        second=chart_for(source,"AMRAP")
        self.assertEqual(source,before)
        self.assertEqual(second["points"][0]["value"],11.4)
        self.assertEqual(sum(p["selected"] for p in second["points"]),1)
        for key in ("scientific_approval","individual_forecast","user_comparison_allowed"):
            self.assertFalse(second[key])

if __name__=="__main__":
    unittest.main()

