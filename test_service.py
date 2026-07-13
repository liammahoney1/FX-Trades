import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fx_exception_service.entitlements import AccessDenied
from fx_exception_service.models import UserClaims
from fx_exception_service.service import FxExceptionService
from fx_exception_service.store import TradeNotFound


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


if __name__ == "__main__":
    unittest.main()
