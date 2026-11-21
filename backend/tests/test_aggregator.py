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
        # likely_real_looking is never emitted as a verdict; mapped to inconclusive
        self.assertEqual(result["verdict"], "inconclusive")
        self.assertEqual(result["confidence_band"], "low")
        self.assertIn("no_ai_signs_found", [r["key"] for r in result["reasons"]])

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

    def test_matched_returns_exactly_one_origin_reason(self):
        """Matched image returns strictly ONE of origin_match_exact or origin_match_near, never both."""
        phash_match = {
            "source": "Wikimedia Commons (DEMO)",
            "date": "2023-01-01",
            "factcheck_url": "url",
            "claim_en": "Demo claim",
            "claim_hi": "डेमो दावा",
            "thumb_url": "thumb",
            "phash": "1111111111111111"
        }
        # Case A: Exact match
        res_exact = aggregate(
            phash_match=phash_match,
            diff_result={"changed_regions": []},
            c2pa=None,
            ml_output=None,
            demo_data=self.demo,
            input_meta={"width": 800, "height": 600, "phash": "1111111111111111"}
        )
        keys_exact = [r["key"] for r in res_exact["reasons"]]
        self.assertIn("origin_match_exact", keys_exact)
        self.assertNotIn("origin_match_near", keys_exact)

        # Case B: Near match
        res_near = aggregate(
            phash_match=phash_match,
            diff_result={"changed_regions": []},
            c2pa=None,
            ml_output=None,
            demo_data=self.demo,
            input_meta={"width": 800, "height": 600, "phash": "0000000000000000"}
        )
        keys_near = [r["key"] for r in res_near["reasons"]]
        self.assertIn("origin_match_near", keys_near)
        self.assertNotIn("origin_match_exact", keys_near)

    def test_scope_note_matched_vs_checked(self):
        """Scope note says 'Checked against' when no match, 'Matched against' on match."""
        # 1. No match
        res_nomatch = aggregate(
            phash_match=None,
            diff_result=None,
            c2pa=None,
            ml_output={"band": "inconclusive", "reasons": [], "gate_triggered": False},
            demo_data=self.demo,
        )
        fin_nomatch = finalize_passport(res_nomatch, "pass_none", consent_external=False)
        self.assertIn("Checked against the Trinetra index", fin_nomatch["scope_note"]["en"])
        self.assertIn("त्रिनेत्र इंडेक्स में जांच की गई", fin_nomatch["scope_note"]["hi"])

        # 2. Matched
        phash_match = {
            "source": "Wikimedia", "date": "2023-01-01", "factcheck_url": "u",
            "claim_en": "En", "claim_hi": "Hi", "thumb_url": "t", "phash": "1"
        }
        res_match = aggregate(
            phash_match=phash_match,
            diff_result=None,
            c2pa=None,
            ml_output=None,
            demo_data=self.demo,
        )
        fin_match = finalize_passport(res_match, "pass_match", consent_external=False)
        self.assertIn("Matched against the Trinetra index", fin_match["scope_note"]["en"])
        self.assertIn("त्रिनेत्र इंडेक्स से मिलान किया गया", fin_match["scope_note"]["hi"])

    def test_known_image_headline_and_amber_style(self):
        """Verdict original headline is 'Known image: matches an indexed reference'."""
        phash_match = {
            "source": "Wikimedia", "date": "2023-01-01", "factcheck_url": "u",
            "claim_en": "En", "claim_hi": "Hi", "thumb_url": "t", "phash": "1"
        }
        res = aggregate(
            phash_match=phash_match,
            diff_result=None,
            c2pa=None,
            ml_output=None,
            demo_data=self.demo,
        )
        self.assertEqual(res["verdict"], "original")
        self.assertIn("Known image: matches an indexed reference", res["lang"]["en"])
        self.assertIn("ज्ञात छवि: इंडेक्स संदर्भ से मेल खाती है", res["lang"]["hi"])

    def test_gate_triggered_returns_specific_rule(self):
        """Gate triggered returns gate_triggered AND the specific rule that fired."""
        for rule in ["low_resolution", "heavy_compression", "signals_disagree"]:
            ml_out = {"band": "inconclusive", "reasons": [rule], "gate_triggered": True}
            res = aggregate(
                phash_match=None,
                diff_result=None,
                c2pa=None,
                ml_output=ml_out,
                demo_data=self.demo,
            )
            keys = [r["key"] for r in res["reasons"]]
            self.assertIn("gate_triggered", keys)
            self.assertIn(rule, keys)

    def test_tiny_image_gate_consistency(self):
        """Low-res (<256) or heavy compression (<=75) triggers gate."""
        from app import config as cfg
        self.assertEqual(cfg.MIN_IMAGE_DIM, 256)
        self.assertEqual(cfg.HEAVY_COMPRESSION_JPEG_QUALITY, 75.0)

        # Input meta with low resolution
        phash_match = {
            "source": "Wikimedia", "date": "2023-01-01", "factcheck_url": "u",
            "claim_en": "En", "claim_hi": "Hi", "thumb_url": "t", "phash": "1"
        }
        diff_res = {"changed_regions": [{"x": 10, "y": 10, "w": 20, "h": 20}], "heatmap_path": "h"}
        res = aggregate(
            phash_match=phash_match,
            diff_result=diff_res,
            c2pa=None,
            ml_output=None,
            demo_data=self.demo,
            input_meta={"width": 200, "height": 180, "jpeg_quality": 85.0}
        )
        self.assertEqual(res["verdict"], "inconclusive")
        keys = [r["key"] for r in res["reasons"]]
        self.assertIn("low_resolution", keys)



if __name__ == "__main__":
    unittest.main()
