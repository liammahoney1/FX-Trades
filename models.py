from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Evidence:
    event_type: str
    severity: str
    source: str
    source_record_id: str
    timestamp_utc: str


@dataclass(frozen=True)
class Trade:
    trade_id: str
    client_account: str
    region: str
    currency_pair: str
    lifecycle_state: str
    evidence: Tuple[Evidence, ...]


@dataclass(frozen=True)
class UserClaims:
    user_id: str
    accounts: frozenset[str]
    regions: frozenset[str]
