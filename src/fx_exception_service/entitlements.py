from .models import Trade, UserClaims


class AccessDenied(Exception):
    """Raised without restricted resource details."""


def require_trade_access(claims: UserClaims, trade: Trade) -> None:
    if trade.client_account not in claims.accounts or trade.region not in claims.regions:
        raise AccessDenied("Access denied")
