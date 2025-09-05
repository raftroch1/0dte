def check_vwap_alignment(self, df_1min, df_5min, df_15min):
    """Check VWAP alignment across timeframes"""

    current_price = df_1min['close'].iloc[-1]

    # Calculate VWAP for each timeframe
    vwap_1m = self.calculate_session_vwap(df_1min)
    vwap_5m = self.calculate_session_vwap(df_5min)
    vwap_15m = self.calculate_session_vwap(df_15min)

    # Check alignment
    above_all = current_price > vwap_1m and current_price > vwap_5m and current_price > vwap_15m
    below_all = current_price < vwap_1m and current_price < vwap_5m and current_price < vwap_15m

    if above_all:
        return "BULLISH_ALIGNMENT", 80
    elif below_all:
        return "BEARISH_ALIGNMENT", 80
    else:
        return "MIXED_ALIGNMENT", 40