import unittest
from pathlib import Path
from backend.aggregator import aggregate, finalize_passport

class TestAggregatorLadder(unittest.TestCase):
    def setUp(self):
        self.demo = True
        self.passport_id = "test-id"

    def test_ai_confirmed_via_c2pa(self):
        c2pa = {"status": "valid", "ai_generated": True, "issuer": "demo", "history": []}
        result = aggregate(
            phash_match=None,
            diff_result=None,
            c2pa=c2pa,
            ml_output=None,
            demo_data=self.demo,
        )
        result = finalize_passport(result, self.passport_id, consent_external=False)
        self.assertEqual(result["verdict"], "ai_confirmed")
        self.assertEqual(result["eyes"]["synthesis"], "confirmed")

    def test_modified_with_diff(self):
        phash_match = {"source": "src", "date": "2023-01-01", "factcheck_url": "url", "claim_en": "Demo entry", "claim_hi": "डेमो", "thumb_url": "thumb"}
        diff_res = {"changed_regions": [{"x":0,"y":0,"w":10,"h":10}], "heatmap_path": "hm.png", "aligned_path": "al.png"}
        result = aggregate(
            phash_match=phash_match,
            diff_result=diff_res,
            c2pa=None,
            ml_output=None,
            demo_data=self.demo,
        )
        result = finalize_passport(result, self.passport_id, consent_external=False)
        self.assertEqual(result["verdict"], "modified")
        self.assertEqual(result["eyes"]["change"], "found")
        self.assertIn("diff_detected", [r["key"] for r in result["reasons"]])

    def test_original_no_diff(self):
        phash_match = {"source": "src", "date": "2023-01-01", "factcheck_url": "url", "claim_en": "Demo entry", "claim_hi": "डेमो", "thumb_url": "thumb"}
        result = aggregate(
            phash_match=phash_match,
            diff_result=None,
            c2pa=None,
            ml_output=None,
            demo_data=self.demo,
        )
        result = finalize_passport(result, self.passport_id, consent_external=False)
        self.assertEqual(result["verdict"], "original")
        self.assertEqual(result["eyes"]["change"], "none")

    def test_out_of_context(self):
        phash_match = {"source": "src", "date": "2023-01-01", "factcheck_url": "url", "claim_en": "Demo entry", "claim_hi": "डेमो", "thumb_url": "thumb"}
        result = aggregate(
            phash_match=phash_match,
            diff_result=None,
            c2pa=None,
            ml_output=None,
            claim_text="Different claim",
            demo_data=self.demo,
        )
        result = finalize_passport(result, self.passport_id, consent_external=False)
        self.assertEqual(result["verdict"], "out_of_context")
        self.assertIn("out_of_context", [r["key"] for r in result["reasons"]])

    def test_ai_lane_likely_ai(self):
        ml_out = {"band": "likely_ai", "reasons": [], "gate_triggered": False}
        result = aggregate(
            phash_match=None,
            diff_result=None,
            c2pa=None,
            ml_output=ml_out,
            demo_data=self.demo,
        )
        result = finalize_passport(result, self.passport_id, consent_external=False)
        self.assertEqual(result["verdict"], "likely_ai")
        self.assertEqual(result["eyes"]["synthesis"], "likely")

    def test_ai_lane_likely_real_looking(self):
        ml_out = {"band": "likely_real_looking", "reasons": [], "gate_triggered": False}
        result = aggregate(
            phash_match=None,
            diff_result=None,
            c2pa=None,
            ml_output=ml_out,
            demo_data=self.demo,
        )
        result = finalize_passport(result, self.passport_id, consent_external=False)
        self.assertEqual(result["verdict"], "likely_real_looking")
        self.assertEqual(result["confidence_band"], "high")

    def test_ai_lane_gate_triggered(self):
        ml_out = {"band": "likely_ai", "reasons": [], "gate_triggered": True}
        result = aggregate(
            phash_match=None,
            diff_result=None,
            c2pa=None,
            ml_output=ml_out,
            demo_data=self.demo,
        )
        result = finalize_passport(result, self.passport_id, consent_external=False)
        self.assertEqual(result["verdict"], "inconclusive")
        self.assertIn("gate_triggered", [r["key"] for r in result["reasons"]])

    def test_ai_lane_inconclusive_band(self):
        ml_out = {"band": "inconclusive", "reasons": [], "gate_triggered": False}
        result = aggregate(
            phash_match=None,
            diff_result=None,
            c2pa=None,
            ml_output=ml_out,
            demo_data=self.demo,
        )
        result = finalize_passport(result, self.passport_id, consent_external=False)
        self.assertEqual(result["verdict"], "inconclusive")

if __name__ == "__main__":
    unittest.main()
