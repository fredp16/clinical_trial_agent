import json
import tempfile
import unittest
from pathlib import Path

from ct_target_agent.agent import _extract_response_text, assess, parse_question, summarize
from ct_target_agent.clinicaltrials import normalize


def fixture(target_in_intervention=True, has_results=False, status="RECRUITING"):
    intervention = "B7-H3 ADC" if target_in_intervention else "Pembrolizumab"
    summary = "B7-H3 expression will be explored as a biomarker." if not target_in_intervention else "Dose escalation."
    return {
        "hasResults": has_results,
        "protocolSection": {
            "identificationModule": {"nctId": "NCT00000001", "briefTitle": "Lung cancer trial"},
            "statusModule": {"overallStatus": status, "startDateStruct": {"date": "2025-01"}},
            "designModule": {"studyType": "INTERVENTIONAL", "phases": ["PHASE1"], "enrollmentInfo": {"count": 42}},
            "sponsorCollaboratorsModule": {"leadSponsor": {"name": "Example Bio"}},
            "armsInterventionsModule": {"interventions": [{"name": intervention, "type": "DRUG"}], "armGroups": [{"label": intervention}]},
            "descriptionModule": {"briefSummary": summary},
            "conditionsModule": {"conditions": ["Lung Cancer"]},
        },
    }


class AgentTests(unittest.TestCase):
    def test_extract_response_text_from_nested_message(self):
        class FakeResponse:
            output_text = ""
            output = [{"type": "reasoning", "content": "hidden"}, {"type": "message", "content": [{"type": "output_text", "text": "Final report"}]}]

        self.assertEqual(_extract_response_text(FakeResponse()), "Final report")

    def test_extract_response_text_ignores_reasoning_only(self):
        class FakeResponse:
            output_text = ""
            output = [{"type": "reasoning", "content": "not the final answer"}]

        self.assertEqual(_extract_response_text(FakeResponse()), "")

    def test_parse(self):
        self.assertEqual(parse_question("Assess B7-H3 potential as a therapeutic target in lung cancer"), ("B7-H3", "lung cancer"))

    def test_biomarker_only_is_excluded(self):
        trial = normalize(fixture(False), ["B7-H3", "CD276"])
        self.assertEqual(trial.target_role, "background_or_biomarker")

    def test_direct_trial_summary(self):
        trial = normalize(fixture(True, True), ["B7-H3", "CD276"])
        stats = summarize([trial])
        self.assertEqual(stats["direct_intervention"], 1)
        self.assertEqual(stats["results_posted"], 1)

    def test_unrelated_late_stage_and_results_do_not_overgrade(self):
        early_results = normalize(fixture(True, True, "TERMINATED"), ["B7-H3", "CD276"])
        late = fixture(True, False)
        late["protocolSection"]["identificationModule"]["nctId"] = "NCT00000002"
        late["protocolSection"]["designModule"]["phases"] = ["PHASE3"]
        stats = summarize([early_results, normalize(late, ["B7-H3", "CD276"])])
        from ct_target_agent.agent import evidence_grade
        self.assertEqual(evidence_grade(stats, [early_results, normalize(late, ["B7-H3", "CD276"])])[0], "Clinically advanced hypothesis")

    def test_end_to_end_offline(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = assess("Assess B7-H3 potential as a therapeutic target in lung cancer", tmp, use_llm=False, raw_studies=[fixture()])
            self.assertTrue(report.exists())
            self.assertIn("Clinical hypothesis under active test", report.read_text())
            self.assertEqual(len(json.loads((Path(tmp) / "trials.json").read_text())), 1)

    def test_empty_llm_never_overwrites_report(self):
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as tmp, patch("ct_target_agent.agent.deepseek_plan", return_value=(["B7-H3", "CD276"], "lung cancer")), patch("ct_target_agent.agent.llm_refine", return_value=""):
            report_path = assess("Assess B7-H3 potential as a therapeutic target in lung cancer", tmp, use_llm=True, raw_studies=[fixture()])
            report = report_path.read_text()
            metadata = json.loads((Path(tmp) / "retrieval.json").read_text())
            self.assertIn("Clinical hypothesis under active test", report)
            self.assertGreater(len(report), 100)
            self.assertEqual(metadata["llm_refinement_status"], "fallback_to_deterministic")


if __name__ == "__main__":
    unittest.main()
