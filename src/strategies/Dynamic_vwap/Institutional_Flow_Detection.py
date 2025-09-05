def detect_institutional_flow(self, df, vwap_zones):
    """Detect institutional buying/selling patterns"""

    current_price = df['close'].iloc[-1]
    recent_volume = df['volume'].rolling(5).mean().iloc[-1]
    avg_volume = df['volume'].rolling(50).mean().iloc[-1]

    # Large volume near VWAP = institutional activity
    near_vwap = abs(current_price - vwap_zones['vwap_center']) < (vwap_zones['vwap_center'] * 0.002)
    high_volume = recent_volume > (avg_volume * 2.0)

    if near_vwap and high_volume:
        # Direction based on price action
        price_momentum = df['close'].pct_change(5).iloc[-1]

        if price_momentum > 0.001:  # 0.1% up with volume
            return "INSTITUTIONAL_BUYING", 75
        elif price_momentum < -0.001:  # 0.1% down with volume
            return "INSTITUTIONAL_SELLING", 75

    return "NO_INSTITUTIONAL_FLOW", 50