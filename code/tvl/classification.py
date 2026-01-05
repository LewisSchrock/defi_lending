from .config import ASSET_CLASS_OVERRIDES

def classify_asset(tags, symbol):
    """Deterministic classification without external APIs.
    Returns (asset_class, category_source). tags is ignored but kept for signature compatibility.
    """
    s = (symbol or "").upper()

    # Manual overrides first
    if symbol in ASSET_CLASS_OVERRIDES:
        return ASSET_CLASS_OVERRIDES[symbol], "manual_dict"

    # Heuristics
    if any(x in s for x in ["STETH","WSTETH","RETH","CBETH","WEETH","OSETH","RSETH","EZETH","ETHX"]):
        return "LST","symbol_heuristic"
    if any(x in s for x in ["WBTC","CBBTC","FBTC","LBTC","TBTC","EBTC"]):
        return "wrapped","symbol_heuristic"
    if any(x in s for x in ["USDE","SUSDE","EUSDE","CRVUSD","RLUSD","USDTB","PYUSD"]):
        return "synthetic","symbol_heuristic"
    if any(x in s for x in ["AAVE","BAL","UNI","CRV","SNX","LINK","MKR"]):
        return "gov_token","symbol_heuristic"
    if any(x in s for x in ["USDC","USDT","DAI","FRAX","LUSD","EURC"]):
        return "base","symbol_heuristic"

    return "unclassified","none"
