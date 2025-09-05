import pandas as pd
import numpy as np
from datetime import datetime, time

class DynamicVWAPFilter:
    def __init__(self):
        self.vwap_anchors = {
            'session': None,     # 9:30 AM anchor
            'overnight': None,   # Previous close anchor
            'key_level': None,   # Dynamic anchor from breakouts
            'rolling': None      # 20-period rolling VWAP
        }

    def calculate_multi_vwap(self, df):
        """Calculate multiple VWAP anchors"""

        # 1. Session VWAP (from 9:30 AM)
        session_start = df[df.index.time >= time(9, 30)].index[0]
        session_data = df.loc[session_start:]

        cumulative_volume = (session_data['volume']).cumsum()
        cumulative_pv = (session_data['close'] * session_data['volume']).cumsum()
        session_vwap = cumulative_pv / cumulative_volume

        # 2. Rolling VWAP (20 periods)
        rolling_pv = (df['close'] * df['volume']).rolling(20).sum()
        rolling_vol = df['volume'].rolling(20).sum()
        rolling_vwap = rolling_pv / rolling_vol

        # 3. Overnight VWAP (from previous close)
        # Implementation depends on your data structure

        return {
            'session_vwap': session_vwap,
            'rolling_vwap': rolling_vwap,
            'current_price': df['close'].iloc[-1]
        }

    def calculate_vwap_zones(self, vwap_value, recent_data):
        """Calculate dynamic support/resistance zones"""

        # Calculate VWAP standard deviation bands
        price_deviations = recent_data['close'] - vwap_value
        vwap_std = price_deviations.rolling(20).std().iloc[-1]

        zones = {
            'strong_resistance': vwap_value + (2.0 * vwap_std),
            'resistance': vwap_value + (1.0 * vwap_std),
            'vwap_center': vwap_value,
            'support': vwap_value - (1.0 * vwap_std),
            'strong_support': vwap_value - (2.0 * vwap_std)
        }

        return zones