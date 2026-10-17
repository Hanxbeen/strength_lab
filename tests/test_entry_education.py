"""Education extraction integrity; not efficacy or release validation."""
import json
import unittest
from pathlib import Path
from research_engine import programme_dispatch

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "data/research/coaching/reviews/entry-education-20261017.json"


class EntryEducationTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(REVIEW.read_text())

    def test_three_paths_and_source_boundaries(self):
        paths = {p["lift"]: p for p in self.data["paths"]}
        self.assertEqual(set(paths), {"squat", "bench_press", "deadlift"})
        self.assertEqual(sum(len(p["examples"]) for p in paths.values()), 9)
        for p in paths.values():
            self.assertEqual(p["target"] in p["examples"], p["target_in_source_sequence"])
        self.assertFalse(paths["squat"]["target_in_source_sequence"])
        self.assertFalse(paths["deadlift"]["target_in_source_sequence"])

    def test_no_invented_dose_or_automatic_mastery(self):
        policy = self.data["product_contract"]
        for field in ("sets", "reps", "load_kg", "rest_seconds"):
            self.assertIsNone(policy["training_dose"][field])
        for field in ("mandatory_sequence", "automatic_mastery", "automatic_training_unlock"):
            self.assertFalse(policy[field])
        self.assertEqual(set(policy["responses"]), set(policy["experience_values"]))
        self.assertEqual(policy["responses"]["unknown"], "ask_lift_experience")
        self.assertEqual(policy["assessment_unit"], "per_lift")

    def test_education_not_executable_programme(self):
        self.assertFalse(self.data["scientific_approval"])
        self.assertFalse(self.data["runtime_enabled"])
        self.assertEqual(self.data["kind"], "education_not_training_programme")
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED_SOURCE"):
            programme_dispatch.validate_source(self.data)

    def test_scenario_reference_resolves_to_real_review(self):
        mapping = json.loads((ROOT / "data/research/coaching/reviews/scenario-evidence-map-20261017.json").read_text())
        source = next(s for s in mapping["sources"] if s["id"] == self.data["source"]["id"])
        self.assertEqual(ROOT / source["record"], REVIEW)
        entry = next(d for d in mapping["decisions"] if d["id"] == "SD01")
        self.assertIn(source["id"], entry["source_ids"])
        self.assertEqual(entry["coverage"], "partial_not_release_ready")
        self.assertEqual(len({s["id"] for s in mapping["sources"]}), len(mapping["sources"]))

    def test_release_gates_have_scope_and_action(self):
        gates = self.data["release_gates"]
        self.assertEqual({g["id"] for g in gates}, {
            "barbell_bridge", "equipment_safety", "original_instruction_media", "entry_to_training"
        })
        for gate in gates:
            self.assertEqual(gate["status"], "open")
            self.assertTrue(gate["scope"])
            self.assertTrue(gate["requirement"])
