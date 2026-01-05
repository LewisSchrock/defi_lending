def get_reserves(w3, provider_addr):
    """
    Return a list of dicts with keys:
    symbol, asset, aToken, stableDebt, variableDebt
    Each adapter should translate its own contract architecture to this format.
    """
    raise NotImplementedError("Implement get_reserves() for this protocol")

def get_oracle_price(w3, oracle, asset):
    """Return USD price for this asset."""
    raise NotImplementedError("Implement get_oracle_price() for this protocol")

def get_protocol_metadata():
    """Static metadata for version, oracle scale, etc."""
    return {"price_scale": 1e18, "description": "template", "version": "vX"}