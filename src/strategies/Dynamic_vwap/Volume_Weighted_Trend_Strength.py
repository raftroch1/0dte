def calculate_trend_strength(self, df, lookback=20):
    """Volume-weighted trend strength indicator"""

    price_changes = df['close'].pct_change()
    volume_weights = df['volume'] / df['volume'].rolling(lookback).mean()

    # Volume-weighted price momentum
    vw_momentum = (price_changes * volume_weights).rolling(lookback).sum()

    if vw_momentum > 0.02:  # 2% volume-weighted gain
        return "STRONG_UPTREND", min(90, abs(vw_momentum) * 1000)
    elif vw_momentum > 0.005:  # 0.5% gain
        return "WEAK_UPTREND", min(70, abs(vw_momentum) * 1000)
    elif vw_momentum < -0.02:
        return "STRONG_DOWNTREND", min(90, abs(vw_momentum) * 1000)
    elif vw_momentum < -0.005:
        return "WEAK_DOWNTREND", min(70, abs(vw_momentum) * 1000)
    else:
        return "SIDEWAYS", 50