from .entitlements import require_trade_access
from .models import Evidence, UserClaims
from .store import get_trade


_SEVERITY_PRIORITY = {
    "CRITICAL": 0,
    "HIGH": 1,
    "MEDIUM": 2,
    "LOW": 3,
    "INFO": 4,
}


class FxExceptionService:
    def get_trade_summary(self, trade_id: str, claims: UserClaims) -> dict:
        trade = get_trade(trade_id)
        require_trade_access(claims, trade)
        return {
            "trade_id": trade.trade_id,
            "currency_pair": trade.currency_pair,
            "lifecycle_state": trade.lifecycle_state,
        }

    def get_investigation_view(self, trade_id: str, claims: UserClaims) -> dict:
        trade = get_trade(trade_id)
        require_trade_access(claims, trade)
        ordered_evidence = sorted(trade.evidence, key=_evidence_priority)
        return {
            "trade_id": trade.trade_id,
            "currency_pair": trade.currency_pair,
            "lifecycle_state": trade.lifecycle_state,
            "evidence": [_serialize_evidence(item) for item in ordered_evidence],
            "derived_recommendation": _derive_recommendation(ordered_evidence),
        }


def _evidence_priority(evidence: Evidence) -> tuple[int, str, str]:
    return (
        _SEVERITY_PRIORITY.get(evidence.severity, len(_SEVERITY_PRIORITY)),
        evidence.timestamp_utc,
        evidence.source_record_id,
    )


def _serialize_evidence(evidence: Evidence) -> dict:
    return {
        "event_type": evidence.event_type,
        "severity": evidence.severity,
        "source": evidence.source,
        "source_record_id": evidence.source_record_id,
        "timestamp_utc": evidence.timestamp_utc,
    }


def _derive_recommendation(ordered_evidence: list[Evidence]) -> dict:
    highest_priority = ordered_evidence[0] if ordered_evidence else None
    if highest_priority is None:
        next_step = "Review the trade lifecycle state and gather exception evidence."
        basis = None
    elif highest_priority.severity == "INFO":
        next_step = "Review lifecycle evidence before escalating the investigation."
        basis = highest_priority.event_type
    else:
        next_step = f"Investigate {highest_priority.event_type} using the linked source evidence."
        basis = highest_priority.event_type

    return {
        "type": "derived",
        "next_step": next_step,
        "basis_event_type": basis,
    }
