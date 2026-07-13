import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fx_exception_service.entitlements import AccessDenied
from fx_exception_service.models import UserClaims
from fx_exception_service.service import FxExceptionService
from fx_exception_service.store import TRADES, TradeNotFound


class FxExceptionServiceBaselineTests(unittest.TestCase):
    def setUp(self):
        self.service = FxExceptionService()
        self.entitled = UserClaims("analyst-1", frozenset({"ORION-AM"}), frozenset({"EMEA"}))

    def test_entitled_summary(self):
        result = self.service.get_trade_summary("FXT-1001", self.entitled)
        self.assertEqual("DELAYED", result["lifecycle_state"])

    def test_account_entitlement_is_required(self):
        claims = UserClaims("analyst-2", frozenset({"OTHER"}), frozenset({"EMEA"}))
        with self.assertRaisesRegex(AccessDenied, "^Access denied$"):
            self.service.get_trade_summary("FXT-1001", claims)

    def test_region_entitlement_is_required(self):
        claims = UserClaims("analyst-3", frozenset({"ORION-AM"}), frozenset({"AMERICAS"}))
        with self.assertRaisesRegex(AccessDenied, "^Access denied$"):
            self.service.get_trade_summary("FXT-1001", claims)

    def test_unknown_trade_uses_existing_behavior(self):
        with self.assertRaises(TradeNotFound):
            self.service.get_trade_summary("FXT-9999", self.entitled)


class Fx142InvestigationViewUatTests(unittest.TestCase):
    def setUp(self):
        self.service = FxExceptionService()
        self.entitled = UserClaims("uat-analyst", frozenset({"ORION-AM"}), frozenset({"EMEA"}))

    def test_uat_entitled_analyst_receives_investigation_view(self):
        result = self.service.get_investigation_view("FXT-1001", self.entitled)

        self.assertEqual("FXT-1001", result["trade_id"])
        self.assertEqual("EUR/USD", result["currency_pair"])
        self.assertEqual("DELAYED", result["lifecycle_state"])
        self.assertEqual("ACK_TIMEOUT", result["evidence"][0]["event_type"])
        self.assertEqual("derived", result["derived_recommendation"]["type"])
        self.assertNotIn("derived_recommendation", result["evidence"][0])

    def test_uat_access_denied_without_trade_or_evidence_disclosure(self):
        claims = UserClaims("uat-denied", frozenset({"ORION-AM"}), frozenset({"AMERICAS"}))

        with self.assertRaisesRegex(AccessDenied, "^Access denied$") as context:
            self.service.get_investigation_view("FXT-1001", claims)

        denial_text = str(context.exception)
        self.assertNotIn("FXT-1001", denial_text)
        self.assertNotIn("ORION-AM", denial_text)
        self.assertNotIn("EUR/USD", denial_text)
        self.assertNotIn("ACK_TIMEOUT", denial_text)

    def test_uat_unknown_trade_uses_existing_not_found_behavior(self):
        with self.assertRaises(TradeNotFound):
            self.service.get_investigation_view("FXT-9999", self.entitled)


class Fx142InvestigationViewQualityTests(unittest.TestCase):
    def setUp(self):
        self.service = FxExceptionService()
        self.entitled = UserClaims("quality-analyst", frozenset({"ORION-AM"}), frozenset({"EMEA"}))

    def test_quality_evidence_has_provenance_and_priority_ordering(self):
        result = self.service.get_investigation_view("FXT-1001", self.entitled)
        evidence = result["evidence"]

        self.assertGreater(len(evidence), 1)
        self.assertEqual("HIGH", evidence[0]["severity"])
        self.assertEqual("ACK_TIMEOUT", evidence[0]["event_type"])
        self.assertEqual(["INFO", "INFO"], [item["severity"] for item in evidence[1:]])
        for item in evidence:
            self.assertIn("source", item)
            self.assertIn("source_record_id", item)
            self.assertIn("timestamp_utc", item)
            self.assertTrue(item["source"])
            self.assertTrue(item["source_record_id"])
            self.assertTrue(item["timestamp_utc"])

    def test_quality_account_and_region_entitlements_are_required(self):
        scenarios = (
            UserClaims("missing-account", frozenset({"OTHER"}), frozenset({"EMEA"})),
            UserClaims("missing-region", frozenset({"ORION-AM"}), frozenset({"AMERICAS"})),
        )
        for claims in scenarios:
            with self.subTest(claims=claims):
                with self.assertRaisesRegex(AccessDenied, "^Access denied$"):
                    self.service.get_investigation_view("FXT-1001", claims)

    def test_quality_view_does_not_mutate_trade_or_evidence(self):
        trade_before = TRADES["FXT-1001"]
        evidence_before = trade_before.evidence

        self.service.get_investigation_view("FXT-1001", self.entitled)

        trade_after = TRADES["FXT-1001"]
        self.assertIs(trade_before, trade_after)
        self.assertEqual(evidence_before, trade_after.evidence)
        self.assertEqual("TRADE_CONFIRMED", trade_after.evidence[0].event_type)


if __name__ == "__main__":
    unittest.main()
