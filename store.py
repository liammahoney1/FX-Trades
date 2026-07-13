from .models import Evidence, Trade


class TradeNotFound(Exception):
    pass


TRADES = {
    "FXT-1001": Trade(
        trade_id="FXT-1001",
        client_account="ORION-AM",
        region="EMEA",
        currency_pair="EUR/USD",
        lifecycle_state="DELAYED",
        evidence=(
            Evidence("TRADE_CONFIRMED", "INFO", "trade-lifecycle", "EV-1001-A", "2026-04-08T07:58:00Z"),
            Evidence("SETTLEMENT_INSTRUCTION_SENT", "INFO", "settlement-gateway", "EV-1001-B", "2026-04-08T08:15:00Z"),
            Evidence("ACK_TIMEOUT", "HIGH", "settlement-monitor", "EV-1001-C", "2026-04-08T08:45:00Z"),
        ),
    )
}


def get_trade(trade_id: str) -> Trade:
    try:
        return TRADES[trade_id]
    except KeyError as exc:
        raise TradeNotFound("Trade not found") from exc
