from .entitlements import require_trade_access
from .models import UserClaims
from .store import get_trade


class FxExceptionService:
    def get_trade_summary(self, trade_id: str, claims: UserClaims) -> dict:
        trade = get_trade(trade_id)
        require_trade_access(claims, trade)
        return {
            "trade_id": trade.trade_id,
            "currency_pair": trade.currency_pair,
            "lifecycle_state": trade.lifecycle_state,
        }

    # FX-142 will add an entitled investigation view here.
