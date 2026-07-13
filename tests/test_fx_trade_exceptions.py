from datetime import UTC, datetime, timedelta
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "FX Trade Exceptions"
loader = SourceFileLoader("fx_trade_exceptions", str(MODULE_PATH))
spec = spec_from_loader(loader.name, loader)
fx = module_from_spec(spec)
loader.exec_module(fx)


def test_missing_ssi_returns_failed_validation():
    result = fx.validate_settlement_instructions({
        "counterparty_id": "UNKNOWN",
        "currency_pair": "EUR/USD",
    })

    assert result == {
        "nostro_match": False,
        "correspondent_match": False,
        "validated": False,
        "reason": "SSI record not found",
    }


def test_evidence_classifier_exact_matches_and_empty_ratio():
    classified = fx.EvidenceClassifier().classify([
        {"source": "swift_message", "content": "confirmed"},
        {"source": "swift_message_draft", "content": "draft only"},
    ])

    assert len(classified["facts"]) == 1
    assert len(classified["assumptions"]) == 1
    assert fx.EvidenceClassifier().classify([])["fact_ratio"] == 0.0


def test_pattern_analysis_uses_lookback_average_and_serializable_clients():
    recent = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=1)
    old = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=90)

    result = fx.analyze_exception_patterns([
        {
            "trade_date": recent.isoformat(),
            "exception_category": "ssi_mismatch",
            "notional_usd": 100,
            "client_id": "C2",
            "resolution_hours": 2,
        },
        {
            "trade_date": recent.isoformat(),
            "exception_category": "ssi_mismatch",
            "notional_usd": 200,
            "client_id": "C1",
            "resolution_hours": 4,
        },
        {
            "trade_date": old.isoformat(),
            "exception_category": "ssi_mismatch",
            "notional_usd": 999,
            "client_id": "OLD",
            "resolution_hours": 100,
        },
    ], lookback_days=30)

    category, stats = result["patterns"][0]
    assert category == "ssi_mismatch"
    assert result["total_exceptions"] == 2
    assert stats["avg_resolution_hours"] == 3
    assert stats["affected_clients"] == ["C1", "C2"]


def test_compliance_gate_enforces_four_eyes_and_market_hours():
    result = fx.ComplianceGate({"restricted_currency": True, "roles": ["senior_ops"]}).can_resolve({
        "currency_pair": "USD/RUB",
        "notional_usd": 60_000_000,
        "approver_id": "ops-1",
        "resolver_id": "ops-1",
        "market_open": False,
    }, "manual_release")

    assert "FOUR_EYES: Requires secondary approval" in result["blocks"]
    assert "MARKET_HOURS: Resolution requires an open market" in result["blocks"]


def test_epic_scope_uses_observed_date_span_and_zero_team_size():
    result = fx.scope_epic_impact([
        {
            "trade_date": "2026-01-01",
            "investigation_hours": 2,
            "notional_usd": 1_000_000,
            "status": "failed",
            "penalty_bps": 10,
        },
        {
            "trade_date": "2026-01-10",
            "investigation_hours": 3,
            "notional_usd": 5_000_000,
            "status": "settled",
        },
    ], ops_team_size=0)

    assert result["current_state"]["observed_days"] == 10
    assert result["current_state"]["total_failed_notional"] == 1_000_000
    assert result["projected"]["avg_hours_per_analyst"] == 0
    assert result["projected"]["manual_hours_saved"] == 126
