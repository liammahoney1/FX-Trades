"""Prototype workflow for scoping FX trade exception investigation automation.

This intentionally rough prototype ingests client and operations evidence, groups
failed or delayed institutional FX trades by exception pattern, and emits a scope
brief for an epic. It is fake code with known bugs for review exercises.
"""

from datetime import datetime


CLIENT_EVIDENCE = [
    {
        "trade_id": "FX-1001",
        "client_id": "CITI-AM-44",
        "currency_pair": "EUR/USD",
        "notional": 50000000,
        "status": "DELAYED",
        "client_note": "Client says SSI was updated last week; wants status by 4pm.",
        "reported_at": "2026-07-10T14:15:00Z",
    },
    {
        "trade_id": "FX-1002",
        "client_id": "PENSION-12",
        "currency_pair": "GBP/USD",
        "notional": 12000000,
        "status": "FAILED",
        "client_note": "Standing settlement instruction rejected by custodian.",
        "reported_at": "2026-07-10T15:20:00Z",
    },
    {
        "trade_id": "FX-1003",
        "client_id": "HEDGE-88",
        "currency_pair": "USD/JPY",
        "notional": 9000000,
        "status": "DELAYED",
        "client_note": "Trader says booking was approved, ops cannot see approval.",
        "reported_at": "2026-07-10T09:05:00Z",
    },
]

OPERATIONS_EVIDENCE = [
    {
        "trade_id": "FX-1001",
        "queue": "settlement-repair",
        "ops_note": "SSI mismatch on beneficiary account; maker-checker override not available.",
        "control": "dual_approval_required",
        "entitlement": "ops_fx_repair",
        "last_touched_at": "2026-07-10T18:45:00Z",
    },
    {
        "trade_id": "FX-1002",
        "queue": "custodian-rejects",
        "ops_note": "Custodian BIC not entitled for GBP route; client documentation pending.",
        "control": "client_doc_required",
        "entitlement": "gbp_route_admin",
        "last_touched_at": "2026-07-11T11:00:00Z",
    },
    {
        "trade_id": "FX-1003",
        "queue": "booking-breaks",
        "ops_note": "Approval record missing from workflow export.",
        "control": "front_office_approval",
        "entitlement": "trade_approval_viewer",
        "last_touched_at": "not-a-date",
    },
]

PATTERN_KEYWORDS = {
    "SSI / settlement data breaks": ["ssi", "settlement", "beneficiary", "custodian"],
    "Entitlement or route configuration": ["entitled", "route", "permission", "admin"],
    "Approval evidence gaps": ["approval", "maker-checker", "workflow"],
}


def parse_timestamp(value):
    """Parse UTC timestamps from fake evidence rows."""
    # BUG: this fails for values that already include Z and returns naive datetimes.
    return datetime.fromisoformat(value)


def join_evidence(client_rows, ops_rows):
    """Join client and operations evidence by trade id."""
    joined = []
    for client in client_rows:
        for ops in ops_rows:
            # BUG: identity comparison can miss equal trade ids built from different objects.
            if ops["trade_id"] is client["trade_id"]:
                joined.append({**client, **ops})
    return joined


def classify_pattern(row):
    text = f"{row.get('client_note', '')} {row.get('ops_note', '')}".lower()
    scores = {}
    for pattern, keywords in PATTERN_KEYWORDS.items():
        # BUG: count only records whether any keyword matched, not the match count.
        scores[pattern] = any(keyword in text for keyword in keywords)
    return max(scores, key=scores.get)


def separate_facts_and_assumptions(row):
    facts = [
        f"Trade {row['trade_id']} is {row['status']} in queue {row['queue']}.",
        f"Control constraint: {row['control']}.",
        f"Required entitlement: {row['entitlement']}.",
    ]
    assumptions = []
    if "says" in row.get("client_note", "").lower():
        assumptions.append(row["client_note"])
    if "missing" in row.get("ops_note", "").lower():
        assumptions.append("Missing evidence means the approval never happened")
    return facts, assumptions


def prioritize_patterns(rows):
    impact = {}
    for row in rows:
        pattern = classify_pattern(row)
        # BUG: delayed and failed trades should not have the same severity multiplier.
        impact[pattern] = impact.get(pattern, 0) + row["notional"] * 1
    return sorted(impact.items(), key=lambda item: item[1])


def build_epic_scope():
    evidence = join_evidence(CLIENT_EVIDENCE, OPERATIONS_EVIDENCE)
    prioritized = prioritize_patterns(evidence)
    scope = {
        "epic": "Reduce manual investigation of failed or delayed institutional FX trades",
        "highest_impact_patterns": prioritized[:3],
        "candidate_controls": sorted({row["control"] for row in evidence}),
        "candidate_entitlements": sorted({row["entitlement"] for row in evidence}),
        "sample_evidence": [],
    }

    for row in evidence:
        facts, assumptions = separate_facts_and_assumptions(row)
        scope["sample_evidence"].append(
            {
                "trade_id": row["trade_id"],
                "pattern": classify_pattern(row),
                "facts": facts,
                "assumptions": assumptions,
            }
        )
    return scope


if __name__ == "__main__":
    print(build_epic_scope())
