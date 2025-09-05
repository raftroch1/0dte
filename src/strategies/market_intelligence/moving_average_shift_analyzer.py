#!/usr/bin/env python3
"""
Moving Average Shift Analyzer - ChartPrime Implementation for 0DTE Trading
=========================================================================

ADVANCED MOVING AVERAGE SHIFT INDICATOR:
Perfect for 15-minute retest breakout signals in 0DTE options trading.
This replaces the VWAP system with a more sophisticated indicator specifically
designed for short-term momentum and reversal detection.

Key Features:
- Multiple MA types (EMA, SMA, WMA, Hull MA, etc.)
- Percentile-based normalization
- Hull MA smoothing for reduced noise
- Crossover signals optimized for 0DTE timeframes
- Trend confirmation with MA positioning

Location: src/strategies/market_intelligence/ (following .cursorrules structure)
Author: Advanced Options Trading Framework - MA Shift Integration
Inspired by: ChartPrime's Moving Average Shift indicator
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class MAShiftSignal:
    """Moving Average Shift signal analysis"""
    
    # Core Indicator Values
    ma_value: float
    source_value: float
    oscillator_value: float
    
    # Trend Analysis
    ma_trend: str  # 'BULLISH', 'BEARISH', 'NEUTRAL'
    trend_strength: float  # 0.0 to 1.0
    
    # Signal Detection
    signal_type: str  # 'BULLISH_CROSS', 'BEARISH_CROSS', 'NO_SIGNAL'
    signal_strength: float  # 0.0 to 1.0
    signal_confidence: float  # 0.0 to 1.0
    
    # Market Context
    market_regime: str  # 'TRENDING_UP', 'TRENDING_DOWN', 'RANGING', 'BREAKOUT'
    volatility_state: str  # 'LOW', 'NORMAL', 'HIGH'
    
    # 0DTE Specific
    momentum_score: float  # -1.0 to 1.0
    reversal_probability: float  # 0.0 to 1.0
    breakout_potential: float  # 0.0 to 1.0

class MovingAverageShiftAnalyzer:
    """
    Advanced Moving Average Shift Analyzer for 0DTE Trading
    
    Implements ChartPrime's Moving Average Shift indicator with enhancements
    specifically designed for 0DTE options trading strategies.
    
    Perfect for:
    - 15-minute retest breakout signals
    - Short-term momentum detection
    - Reversal identification
    - Trend confirmation
    """
    
    def __init__(self,
                 ma_type: str = "EMA",
                 ma_length: int = 40,
                 osc_length: int = 15,
                 osc_threshold: float = 0.5,
                 percentile_lookback: int = 1000):
        """
        Initialize Moving Average Shift Analyzer
        
        Args:
            ma_type: Type of moving average ('EMA', 'SMA', 'WMA', 'Hull', 'SMMA')
            ma_length: Length of the moving average (default: 40)
            osc_length: Length for oscillator calculation (default: 15)
            osc_threshold: Threshold for signal generation (default: 0.5)
            percentile_lookback: Lookback period for percentile calculation (default: 1000)
        """
        
        self.ma_type = ma_type
        self.ma_length = ma_length
        self.osc_length = osc_length
        self.osc_threshold = osc_threshold
        self.percentile_lookback = percentile_lookback
        
        logger.info("📊 MOVING AVERAGE SHIFT ANALYZER INITIALIZED")
        logger.info(f"   MA Type: {ma_type}, Length: {ma_length}")
        logger.info(f"   Oscillator Length: {osc_length}, Threshold: {osc_threshold}")
        logger.info(f"   Percentile Lookback: {percentile_lookback}")
    
    def calculate_ma(self, data: pd.Series, length: int, ma_type: str) -> pd.Series:
        """Calculate various moving averages"""
        
        if len(data) < length:
            logger.warning(f"Insufficient data for MA calculation: {len(data)} < {length}")
            return pd.Series(index=data.index, dtype=float)
        
        if ma_type == "SMA":
            return data.rolling(window=length, min_periods=1).mean()
        elif ma_type == "EMA":
            return data.ewm(span=length, min_periods=1).mean()
        elif ma_type == "WMA":
            weights = np.arange(1, length + 1)
            return data.rolling(window=length, min_periods=1).apply(
                lambda x: np.dot(x, weights[:len(x)]) / weights[:len(x)].sum() if len(x) > 0 else np.nan, 
                raw=True
            )
        elif ma_type == "VWMA":
            # Simplified VWMA (fallback to SMA if no volume)
            return data.rolling(window=length, min_periods=1).mean()
        elif ma_type == "SMMA":  # Same as RMA
            return data.ewm(alpha=1/length, min_periods=1).mean()
        elif ma_type == "Hull":
            return self.hull_moving_average(data, length)
        else:
            return data.rolling(window=length, min_periods=1).mean()  # Default to SMA
    
    def hull_moving_average(self, data: pd.Series, length: int) -> pd.Series:
        """Calculate Hull Moving Average for smoother signals"""
        
        if len(data) < length:
            return pd.Series(index=data.index, dtype=float)
        
        half_length = max(1, int(length / 2))
        sqrt_length = max(1, int(np.sqrt(length)))
        
        wma_half = self.calculate_ma(data, half_length, "WMA")
        wma_full = self.calculate_ma(data, length, "WMA")
        
        hull_data = 2 * wma_half - wma_full
        hull_ma = self.calculate_ma(hull_data, sqrt_length, "WMA")
        
        return hull_ma
    
    def percentile_linear_interpolation(self, data: pd.Series, lookback: int, percentile: float) -> pd.Series:
        """Calculate rolling percentile with linear interpolation"""
        
        def calc_percentile(x):
            if len(x) < 2:
                return np.nan
            return np.percentile(x, percentile)
        
        effective_lookback = min(lookback, len(data))
        return data.rolling(window=effective_lookback, min_periods=2).apply(calc_percentile, raw=True)
    
    def calculate_indicator(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate the complete Moving Average Shift indicator
        
        Args:
            df: DataFrame with OHLCV data (must have 'high', 'low', 'close' columns)
            
        Returns:
            Dictionary with MA, oscillator, and signals
        """
        
        if len(df) < self.ma_length:
            logger.warning(f"Insufficient data for MA Shift calculation: {len(df)} < {self.ma_length}")
            return self._get_empty_result()
        
        # Validate required columns
        required_cols = ['high', 'low', 'close']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.error(f"Missing required columns: {missing_cols}")
            return self._get_empty_result()
        
        try:
            # Use HL2 as source (high + low) / 2
            source = (df['high'] + df['low']) / 2
            
            # Calculate Moving Average
            ma = self.calculate_ma(source, self.ma_length, self.ma_type)
            
            # Calculate difference between source and MA
            diff = source - ma
            
            # Calculate percentile ranking of difference
            perc_r = self.percentile_linear_interpolation(diff, self.percentile_lookback, 99)
            
            # Avoid division by zero and handle NaN values
            perc_r = perc_r.replace(0, np.nan).ffill().fillna(1)
            perc_r = perc_r.replace([np.inf, -np.inf], 1)
            
            # Calculate rate of change
            normalized_diff = diff / perc_r
            change_diff = normalized_diff.diff(self.osc_length)
            
            # Apply Hull Moving Average smoothing
            osc = self.hull_moving_average(change_diff, 10)
            
            # Generate signals
            signals = self.generate_signals(osc)
            
            # Calculate trend information
            ma_trend = source > ma  # True = bullish, False = bearish
            
            return {
                'ma': ma,
                'source': source,
                'diff': diff,
                'oscillator': osc,
                'signals': signals,
                'ma_trend': ma_trend,
                'normalized_diff': normalized_diff,
                'change_diff': change_diff
            }
            
        except Exception as e:
            logger.error(f"Error calculating MA Shift indicator: {e}")
            return self._get_empty_result()
    
    def generate_signals(self, osc: pd.Series) -> Dict[str, pd.Series]:
        """Generate crossover signals optimized for 0DTE trading"""
        
        if len(osc) < 3:
            return {
                'bullish_signal': pd.Series(dtype=bool),
                'bearish_signal': pd.Series(dtype=bool),
                'osc_above_threshold': pd.Series(dtype=bool),
                'osc_below_threshold': pd.Series(dtype=bool)
            }
        
        # Crossover signals (current vs 2 periods ago for smoothing)
        osc_shifted = osc.shift(2)
        
        # Bullish signal: crossover above threshold from below
        bullish_cross = (
            (osc > osc_shifted) &
            (osc.shift(1) <= osc_shifted.shift(1)) &
            (osc < -self.osc_threshold)
        )
        
        # Bearish signal: crossunder below threshold from above
        bearish_cross = (
            (osc < osc_shifted) &
            (osc.shift(1) >= osc_shifted.shift(1)) &
            (osc > self.osc_threshold)
        )
        
        return {
            'bullish_signal': bullish_cross.fillna(False),
            'bearish_signal': bearish_cross.fillna(False),
            'osc_above_threshold': (osc > self.osc_threshold).fillna(False),
            'osc_below_threshold': (osc < -self.osc_threshold).fillna(False)
        }
    
    def analyze_ma_shift_intelligence(self, spy_data: pd.DataFrame, 
                                    current_spy_price: float) -> MAShiftSignal:
        """
        Comprehensive MA Shift analysis for 0DTE trading
        
        Args:
            spy_data: Historical SPY price data with OHLCV
            current_spy_price: Current SPY price
            
        Returns:
            MAShiftSignal with comprehensive analysis
        """
        
        logger.debug(f"🔍 Analyzing MA Shift intelligence with {len(spy_data)} bars")
        
        if len(spy_data) < self.ma_length:
            logger.warning("Insufficient data for MA Shift analysis")
            return self._get_neutral_signal()
        
        # Calculate the indicator
        indicator_data = self.calculate_indicator(spy_data)
        
        if not indicator_data or indicator_data.get('ma') is None:
            return self._get_neutral_signal()
        
        # Get latest values
        latest_ma = indicator_data['ma'].iloc[-1] if not pd.isna(indicator_data['ma'].iloc[-1]) else current_spy_price
        latest_source = indicator_data['source'].iloc[-1] if not pd.isna(indicator_data['source'].iloc[-1]) else current_spy_price
        latest_osc = indicator_data['oscillator'].iloc[-1] if not pd.isna(indicator_data['oscillator'].iloc[-1]) else 0.0
        
        # Determine trend
        ma_trend = self._determine_trend(latest_source, latest_ma, latest_osc)
        trend_strength = self._calculate_trend_strength(indicator_data)
        
        # Detect signals
        signal_type, signal_strength, signal_confidence = self._detect_signals(indicator_data)
        
        # Analyze market regime
        market_regime = self._analyze_market_regime(indicator_data, spy_data)
        volatility_state = self._analyze_volatility(spy_data)
        
        # Calculate 0DTE specific metrics
        momentum_score = self._calculate_momentum_score(indicator_data)
        reversal_probability = self._calculate_reversal_probability(indicator_data)
        breakout_potential = self._calculate_breakout_potential(indicator_data, spy_data)
        
        signal = MAShiftSignal(
            ma_value=float(latest_ma),
            source_value=float(latest_source),
            oscillator_value=float(latest_osc),
            ma_trend=ma_trend,
            trend_strength=float(trend_strength),
            signal_type=signal_type,
            signal_strength=float(signal_strength),
            signal_confidence=float(signal_confidence),
            market_regime=market_regime,
            volatility_state=volatility_state,
            momentum_score=float(momentum_score),
            reversal_probability=float(reversal_probability),
            breakout_potential=float(breakout_potential)
        )
        
        logger.debug(f"📊 MA Shift Analysis Complete:")
        logger.debug(f"   Trend: {ma_trend} (strength: {trend_strength:.2f})")
        logger.debug(f"   Signal: {signal_type} (confidence: {signal_confidence:.2f})")
        logger.debug(f"   Momentum: {momentum_score:.2f}, Reversal: {reversal_probability:.2f}")
        
        return signal
    
    def _determine_trend(self, source: float, ma: float, osc: float) -> str:
        """Determine current trend based on MA position and oscillator"""
        
        price_above_ma = source > ma
        osc_bullish = osc > 0
        
        if price_above_ma and osc_bullish:
            return "BULLISH"
        elif not price_above_ma and not osc_bullish:
            return "BEARISH"
        else:
            return "NEUTRAL"
    
    def _calculate_trend_strength(self, indicator_data: Dict) -> float:
        """Calculate trend strength based on MA separation and oscillator momentum"""
        
        try:
            source = indicator_data['source'].iloc[-10:].dropna()
            ma = indicator_data['ma'].iloc[-10:].dropna()
            osc = indicator_data['oscillator'].iloc[-10:].dropna()
            
            if len(source) < 5 or len(ma) < 5:
                return 0.5
            
            # Calculate average separation
            separation = abs((source.mean() - ma.mean()) / ma.mean())
            
            # Calculate oscillator momentum
            osc_momentum = abs(osc.iloc[-1] - osc.iloc[-5]) if len(osc) >= 5 else 0
            
            # Combine factors
            strength = min(1.0, (separation * 10 + osc_momentum) / 2)
            
            return strength
            
        except Exception:
            return 0.5
    
    def _detect_signals(self, indicator_data: Dict) -> Tuple[str, float, float]:
        """Detect and analyze crossover signals"""
        
        try:
            signals = indicator_data['signals']
            
            # Check latest signals
            latest_bullish = signals['bullish_signal'].iloc[-1] if len(signals['bullish_signal']) > 0 else False
            latest_bearish = signals['bearish_signal'].iloc[-1] if len(signals['bearish_signal']) > 0 else False
            
            if latest_bullish:
                signal_type = "BULLISH_CROSS"
                signal_strength = 0.8
                signal_confidence = 0.75
            elif latest_bearish:
                signal_type = "BEARISH_CROSS"
                signal_strength = 0.8
                signal_confidence = 0.75
            else:
                signal_type = "NO_SIGNAL"
                signal_strength = 0.0
                signal_confidence = 0.5
            
            return signal_type, signal_strength, signal_confidence
            
        except Exception:
            return "NO_SIGNAL", 0.0, 0.5
    
    def _analyze_market_regime(self, indicator_data: Dict, spy_data: pd.DataFrame) -> str:
        """Analyze current market regime"""
        
        try:
            # Look at recent price action
            recent_closes = spy_data['close'].iloc[-20:].dropna()
            
            if len(recent_closes) < 10:
                return "RANGING"
            
            # Calculate trend
            price_change = (recent_closes.iloc[-1] - recent_closes.iloc[-10]) / recent_closes.iloc[-10]
            
            # Calculate volatility
            returns = recent_closes.pct_change().dropna()
            volatility = returns.std()
            
            if abs(price_change) > 0.02 and volatility > 0.015:
                return "BREAKOUT"
            elif price_change > 0.01:
                return "TRENDING_UP"
            elif price_change < -0.01:
                return "TRENDING_DOWN"
            else:
                return "RANGING"
                
        except Exception:
            return "RANGING"
    
    def _analyze_volatility(self, spy_data: pd.DataFrame) -> str:
        """Analyze current volatility state"""
        
        try:
            recent_closes = spy_data['close'].iloc[-20:].dropna()
            
            if len(recent_closes) < 10:
                return "NORMAL"
            
            returns = recent_closes.pct_change().dropna()
            volatility = returns.std()
            
            if volatility > 0.02:
                return "HIGH"
            elif volatility < 0.01:
                return "LOW"
            else:
                return "NORMAL"
                
        except Exception:
            return "NORMAL"
    
    def _calculate_momentum_score(self, indicator_data: Dict) -> float:
        """Calculate momentum score (-1 to 1)"""
        
        try:
            osc = indicator_data['oscillator'].iloc[-5:].dropna()
            
            if len(osc) < 3:
                return 0.0
            
            # Calculate momentum based on oscillator direction and magnitude
            momentum = (osc.iloc[-1] - osc.iloc[-3]) / 2
            
            # Normalize to -1 to 1 range
            momentum_score = np.tanh(momentum * 2)
            
            return momentum_score
            
        except Exception:
            return 0.0
    
    def _calculate_reversal_probability(self, indicator_data: Dict) -> float:
        """Calculate probability of trend reversal"""
        
        try:
            osc = indicator_data['oscillator'].iloc[-10:].dropna()
            
            if len(osc) < 5:
                return 0.5
            
            # Look for extreme oscillator values
            extreme_threshold = 1.0
            recent_extreme = any(abs(val) > extreme_threshold for val in osc.iloc[-3:])
            
            # Look for divergence
            osc_trend = osc.iloc[-1] - osc.iloc[-5]
            
            if recent_extreme and abs(osc_trend) > 0.5:
                return 0.7
            elif recent_extreme:
                return 0.6
            else:
                return 0.3
                
        except Exception:
            return 0.5
    
    def _calculate_breakout_potential(self, indicator_data: Dict, spy_data: pd.DataFrame) -> float:
        """Calculate breakout potential based on consolidation and momentum"""
        
        try:
            # Analyze recent price consolidation
            recent_highs = spy_data['high'].iloc[-20:].dropna()
            recent_lows = spy_data['low'].iloc[-20:].dropna()
            
            if len(recent_highs) < 10 or len(recent_lows) < 10:
                return 0.5
            
            # Calculate consolidation (lower volatility = higher breakout potential)
            price_range = (recent_highs.max() - recent_lows.min()) / recent_highs.mean()
            
            # Calculate momentum building
            osc = indicator_data['oscillator'].iloc[-5:].dropna()
            momentum_building = abs(osc.iloc[-1]) > abs(osc.iloc[-3]) if len(osc) >= 3 else False
            
            # Combine factors
            consolidation_score = 1.0 - min(1.0, price_range * 20)  # Lower range = higher score
            momentum_score = 0.7 if momentum_building else 0.3
            
            breakout_potential = (consolidation_score + momentum_score) / 2
            
            return breakout_potential
            
        except Exception:
            return 0.5
    
    def _get_empty_result(self) -> Dict[str, Any]:
        """Return empty result for error cases"""
        return {
            'ma': pd.Series(dtype=float),
            'source': pd.Series(dtype=float),
            'diff': pd.Series(dtype=float),
            'oscillator': pd.Series(dtype=float),
            'signals': {
                'bullish_signal': pd.Series(dtype=bool),
                'bearish_signal': pd.Series(dtype=bool),
                'osc_above_threshold': pd.Series(dtype=bool),
                'osc_below_threshold': pd.Series(dtype=bool)
            },
            'ma_trend': pd.Series(dtype=bool)
        }
    
    def _get_neutral_signal(self) -> MAShiftSignal:
        """Return neutral signal for insufficient data cases"""
        return MAShiftSignal(
            ma_value=0.0,
            source_value=0.0,
            oscillator_value=0.0,
            ma_trend="NEUTRAL",
            trend_strength=0.5,
            signal_type="NO_SIGNAL",
            signal_strength=0.0,
            signal_confidence=0.5,
            market_regime="RANGING",
            volatility_state="NORMAL",
            momentum_score=0.0,
            reversal_probability=0.5,
            breakout_potential=0.5
        )

# Example usage and testing
if __name__ == "__main__":
    """Test the Moving Average Shift Analyzer"""
    
    # Create sample SPY data
    dates = pd.date_range('2024-01-01', periods=200, freq='15min')
    np.random.seed(42)
    
    # Generate realistic OHLC data
    base_price = 470.0
    returns = np.random.normal(0, 0.002, 200)
    closes = base_price * (1 + returns).cumprod()
    
    # Create OHLC from closes
    highs = closes * (1 + np.random.uniform(0, 0.005, 200))
    lows = closes * (1 - np.random.uniform(0, 0.005, 200))
    opens = pd.Series(closes).shift(1).fillna(closes[0])
    volumes = np.random.randint(1000000, 5000000, 200)
    
    spy_data = pd.DataFrame({
        'timestamp': dates,
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'volume': volumes
    })
    
    # Initialize analyzer
    analyzer = MovingAverageShiftAnalyzer(
        ma_type="EMA",
        ma_length=40,
        osc_length=15,
        osc_threshold=0.5
    )
    
    # Test indicator calculation
    print("🧪 Testing Moving Average Shift Analyzer")
    print("=" * 50)
    
    indicator_result = analyzer.calculate_indicator(spy_data)
    print(f"✅ Indicator calculated successfully")
    print(f"   MA values: {len(indicator_result['ma'])} points")
    print(f"   Oscillator range: {indicator_result['oscillator'].min():.3f} to {indicator_result['oscillator'].max():.3f}")
    
    # Test intelligence analysis
    current_price = closes[-1]
    signal = analyzer.analyze_ma_shift_intelligence(spy_data, current_price)
    
    print(f"\n📊 MA Shift Intelligence Analysis:")
    print(f"   Current Price: ${current_price:.2f}")
    print(f"   MA Value: ${signal.ma_value:.2f}")
    print(f"   Trend: {signal.ma_trend} (strength: {signal.trend_strength:.2f})")
    print(f"   Signal: {signal.signal_type} (confidence: {signal.signal_confidence:.2f})")
    print(f"   Market Regime: {signal.market_regime}")
    print(f"   Momentum Score: {signal.momentum_score:.2f}")
    print(f"   Breakout Potential: {signal.breakout_potential:.2f}")
    
    print(f"\n🎉 Moving Average Shift Analyzer test completed successfully!")
