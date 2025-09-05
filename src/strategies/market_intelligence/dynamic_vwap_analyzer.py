#!/usr/bin/env python3
"""
Dynamic VWAP Analyzer - Advanced Volume-Weighted Analysis
=========================================================

PROFESSIONAL VWAP SYSTEM FOR 0DTE TRADING:
- Multi-anchored VWAP calculations (session, rolling, overnight)
- Dynamic support/resistance zones with volatility adjustment
- Volume-confirmed breakout detection
- Institutional flow detection
- Multi-timeframe alignment validation
- Volume-weighted trend strength analysis

This system addresses systematic bearish bias by using price-action
based signals instead of sentiment-based indicators.

Location: src/strategies/market_intelligence/ (following .cursorrules structure)
Author: Advanced Options Trading System - VWAP Intelligence
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
import warnings
warnings.filterwarnings('ignore')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DynamicVWAPAnalyzer:
    """
    Professional Dynamic VWAP Analysis System
    
    Provides comprehensive VWAP-based market analysis:
    - Multi-anchored VWAP calculations
    - Dynamic support/resistance zones
    - Volume-confirmed breakout detection
    - Institutional flow detection
    - Trend strength analysis
    """
    
    def __init__(self):
        """Initialize VWAP analyzer with professional configuration"""
        
        # VWAP calculation parameters
        self.vwap_config = {
            'session_start': time(9, 30),  # Market open
            'rolling_periods': 20,         # Rolling VWAP periods
            'volume_threshold': 1.5,       # Volume confirmation multiplier
            'std_multipliers': [1.0, 2.0], # Standard deviation bands
            'trend_lookback': 20           # Trend strength lookback
        }
        
        # Signal confidence thresholds
        self.confidence_thresholds = {
            'strong_breakout': 85,
            'weak_breakout': 70,
            'mean_reversion': 60,
            'institutional_flow': 75,
            'trend_strength': 80
        }
        
        logger.info("🎯 DYNAMIC VWAP ANALYZER INITIALIZED")
        logger.info(f"   Session Start: {self.vwap_config['session_start']}")
        logger.info(f"   Rolling Periods: {self.vwap_config['rolling_periods']}")
        
    def analyze_vwap_intelligence(
        self, 
        price_data: pd.DataFrame,
        current_price: float,
        multi_timeframe_data: Optional[Dict[str, pd.DataFrame]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive VWAP intelligence analysis
        
        Args:
            price_data: Main price/volume data (1-minute or higher frequency)
            current_price: Current underlying price
            multi_timeframe_data: Optional dict with '5m', '15m' timeframe data
            
        Returns:
            Complete VWAP analysis with signals and confidence scores
        """
        
        logger.info("🎯 RUNNING DYNAMIC VWAP ANALYSIS")
        
        try:
            # ENHANCED: Use only current trading day for 0DTE VWAP analysis
            current_day_data = self._get_current_trading_day_data(price_data)
            
            if len(current_day_data) < 30:  # Need at least 30 minutes of data
                logger.warning("Insufficient intraday data for VWAP analysis, using recent data")
                current_day_data = price_data.tail(390)  # Use last 390 minutes (1 trading day)
            
            logger.debug(f"📊 Using {len(current_day_data)} bars for VWAP analysis (intraday only)")
            
            # Calculate multi-anchored VWAP using current day data
            vwap_data = self._calculate_multi_vwap(current_day_data)
            
            # Calculate dynamic zones using current day data
            vwap_zones = self._calculate_vwap_zones(
                vwap_data['session_vwap'].iloc[-1], current_day_data
            )
            
            # Detect breakouts with volume confirmation
            breakout_analysis = self._detect_vwap_breakout(
                current_price, vwap_data, price_data
            )
            
            # Calculate volume-weighted trend strength
            trend_analysis = self._calculate_trend_strength(price_data)
            
            # Detect institutional flow
            institutional_analysis = self._detect_institutional_flow(
                price_data, vwap_zones, current_price
            )
            
            # Multi-timeframe alignment (if data available)
            alignment_analysis = self._check_vwap_alignment(
                price_data, multi_timeframe_data, current_price
            )
            
            # Synthesize complete VWAP intelligence
            vwap_intelligence = self._synthesize_vwap_intelligence(
                vwap_data, vwap_zones, breakout_analysis, 
                trend_analysis, institutional_analysis, alignment_analysis
            )
            
            logger.info(f"🎯 VWAP ANALYSIS COMPLETE:")
            logger.info(f"   Primary Signal: {vwap_intelligence['primary_signal']}")
            logger.info(f"   Confidence: {vwap_intelligence['confidence']:.1f}%")
            logger.info(f"   Bull Score: {vwap_intelligence['bull_contribution']:.1f}")
            logger.info(f"   Bear Score: {vwap_intelligence['bear_contribution']:.1f}")
            
            return vwap_intelligence
            
        except Exception as e:
            logger.error(f"VWAP analysis failed: {e}")
            # Return neutral analysis on failure
            return self._get_neutral_analysis()
    
    def _get_current_trading_day_data(self, price_data: pd.DataFrame) -> pd.DataFrame:
        """
        Extract only the current trading day data for 0DTE VWAP analysis
        
        Args:
            price_data: Full historical price data
            
        Returns:
            DataFrame with only current trading day data
        """
        
        if len(price_data) == 0:
            return price_data
        
        # Get the last timestamp (current day)
        last_timestamp = price_data.index[-1]
        current_date = last_timestamp.date()
        
        # Filter for current trading day only
        current_day_mask = price_data.index.date == current_date
        current_day_data = price_data[current_day_mask]
        
        logger.debug(f"📅 Current trading day: {current_date}")
        logger.debug(f"📊 Intraday bars: {len(current_day_data)} (from {len(price_data)} total)")
        
        return current_day_data
    
    def _calculate_multi_vwap(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """Calculate multiple VWAP anchors"""
        
        vwap_data = {}
        
        try:
            # Ensure we have required columns
            if not all(col in df.columns for col in ['close', 'volume']):
                logger.warning("Missing required columns for VWAP calculation")
                return self._get_default_vwap_data(df)
            
            # 1. Session VWAP (from market open if available)
            if hasattr(df.index, 'time'):
                # Try to find session start
                session_mask = df.index.time >= self.vwap_config['session_start']
                if session_mask.any():
                    session_start_idx = df[session_mask].index[0]
                    session_data = df.loc[session_start_idx:]
                    
                    cumulative_volume = session_data['volume'].cumsum()
                    cumulative_pv = (session_data['close'] * session_data['volume']).cumsum()
                    
                    # Avoid division by zero
                    session_vwap = cumulative_pv / cumulative_volume.replace(0, np.nan)
                    vwap_data['session_vwap'] = session_vwap.reindex(df.index, method='ffill')
                else:
                    # Fallback to full dataset VWAP
                    vwap_data['session_vwap'] = self._calculate_simple_vwap(df)
            else:
                # No time index, use full dataset
                vwap_data['session_vwap'] = self._calculate_simple_vwap(df)
            
            # 2. Rolling VWAP (20 periods)
            rolling_pv = (df['close'] * df['volume']).rolling(
                self.vwap_config['rolling_periods'], min_periods=1
            ).sum()
            rolling_vol = df['volume'].rolling(
                self.vwap_config['rolling_periods'], min_periods=1
            ).sum()
            
            vwap_data['rolling_vwap'] = rolling_pv / rolling_vol.replace(0, np.nan)
            
            # 3. Overnight VWAP (simplified - from previous day's close)
            # This is a placeholder - in production, use actual overnight data
            vwap_data['overnight_vwap'] = vwap_data['session_vwap']
            
            # Fill any NaN values
            for key in vwap_data:
                vwap_data[key] = vwap_data[key].fillna(method='ffill').fillna(df['close'])
            
        except Exception as e:
            logger.warning(f"Error in multi-VWAP calculation: {e}")
            return self._get_default_vwap_data(df)
        
        return vwap_data
    
    def _calculate_simple_vwap(self, df: pd.DataFrame) -> pd.Series:
        """Calculate simple cumulative VWAP"""
        cumulative_volume = df['volume'].cumsum()
        cumulative_pv = (df['close'] * df['volume']).cumsum()
        return cumulative_pv / cumulative_volume.replace(0, np.nan)
    
    def _get_default_vwap_data(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """Return default VWAP data when calculation fails"""
        default_vwap = df['close'] if 'close' in df.columns else pd.Series([500.0] * len(df), index=df.index)
        return {
            'session_vwap': default_vwap,
            'rolling_vwap': default_vwap,
            'overnight_vwap': default_vwap
        }
    
    def _calculate_vwap_zones(self, vwap_value: float, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate dynamic support/resistance zones around VWAP"""
        
        try:
            # Calculate VWAP standard deviation using recent price deviations
            if 'close' in df.columns and len(df) >= 20:
                recent_data = df.tail(20)
                price_deviations = recent_data['close'] - vwap_value
                vwap_std = price_deviations.std()
                
                # Ensure minimum standard deviation
                vwap_std = max(vwap_std, vwap_value * 0.001)  # Min 0.1% of price
            else:
                # Fallback standard deviation
                vwap_std = vwap_value * 0.005  # 0.5% of price
            
            zones = {
                'strong_resistance': vwap_value + (2.0 * vwap_std),
                'resistance': vwap_value + (1.0 * vwap_std),
                'vwap_center': vwap_value,
                'support': vwap_value - (1.0 * vwap_std),
                'strong_support': vwap_value - (2.0 * vwap_std),
                'vwap_std': vwap_std
            }
            
        except Exception as e:
            logger.warning(f"Error calculating VWAP zones: {e}")
            # Fallback zones
            zones = {
                'strong_resistance': vwap_value * 1.01,
                'resistance': vwap_value * 1.005,
                'vwap_center': vwap_value,
                'support': vwap_value * 0.995,
                'strong_support': vwap_value * 0.99,
                'vwap_std': vwap_value * 0.005
            }
        
        return zones
    
    def _detect_vwap_breakout(
        self, 
        current_price: float, 
        vwap_data: Dict[str, pd.Series], 
        volume_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """Detect and validate VWAP breakouts with volume confirmation"""
        
        try:
            session_vwap = vwap_data['session_vwap'].iloc[-1]
            zones = self._calculate_vwap_zones(session_vwap, volume_data)
            
            # Volume confirmation
            volume_confirmed = False
            if 'volume' in volume_data.columns and len(volume_data) >= 20:
                avg_volume = volume_data['volume'].rolling(20).mean().iloc[-1]
                current_volume = volume_data['volume'].iloc[-1]
                volume_confirmed = current_volume > (avg_volume * self.vwap_config['volume_threshold'])
            
            # Breakout detection logic
            breakout_signal = None
            confidence = 50
            
            if current_price > zones['resistance']:
                if current_price > zones['strong_resistance']:
                    breakout_signal = "STRONG_BULLISH_BREAKOUT"
                    confidence = self.confidence_thresholds['strong_breakout']
                else:
                    breakout_signal = "BULLISH_BREAKOUT"
                    confidence = self.confidence_thresholds['weak_breakout']
                    
                # Reduce confidence if no volume confirmation
                if not volume_confirmed:
                    confidence *= 0.7
                    
            elif current_price < zones['support']:
                if current_price < zones['strong_support']:
                    breakout_signal = "STRONG_BEARISH_BREAKDOWN"
                    confidence = self.confidence_thresholds['strong_breakout']
                else:
                    breakout_signal = "BEARISH_BREAKDOWN"
                    confidence = self.confidence_thresholds['weak_breakout']
                    
                # Reduce confidence if no volume confirmation
                if not volume_confirmed:
                    confidence *= 0.7
                    
            # Mean reversion signals
            elif zones['support'] < current_price < zones['vwap_center']:
                breakout_signal = "MEAN_REVERSION_BULLISH"
                confidence = self.confidence_thresholds['mean_reversion']
                
            elif zones['vwap_center'] < current_price < zones['resistance']:
                breakout_signal = "MEAN_REVERSION_BEARISH"
                confidence = self.confidence_thresholds['mean_reversion']
                
            else:
                breakout_signal = "NEUTRAL"
                confidence = 50
            
            return {
                'signal': breakout_signal,
                'confidence': min(95, confidence),
                'zones': zones,
                'volume_confirmed': volume_confirmed,
                'session_vwap': session_vwap
            }
            
        except Exception as e:
            logger.warning(f"Error in breakout detection: {e}")
            return {
                'signal': 'NEUTRAL',
                'confidence': 50,
                'zones': {},
                'volume_confirmed': False,
                'session_vwap': current_price
            }
    
    def _calculate_trend_strength(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate volume-weighted trend strength"""
        
        try:
            if not all(col in df.columns for col in ['close', 'volume']) or len(df) < 20:
                return {'trend_direction': 'SIDEWAYS', 'confidence': 50}
            
            lookback = min(self.vwap_config['trend_lookback'], len(df))
            recent_data = df.tail(lookback)
            
            # Calculate volume-weighted price momentum
            price_changes = recent_data['close'].pct_change()
            volume_weights = recent_data['volume'] / recent_data['volume'].rolling(lookback).mean()
            
            # Volume-weighted momentum
            vw_momentum = (price_changes * volume_weights).sum()
            
            # Determine trend strength and direction
            if vw_momentum > 0.02:  # 2% volume-weighted gain
                trend_direction = "STRONG_UPTREND"
                confidence = min(90, abs(vw_momentum) * 1000)
            elif vw_momentum > 0.005:  # 0.5% gain
                trend_direction = "WEAK_UPTREND"
                confidence = min(70, abs(vw_momentum) * 1000)
            elif vw_momentum < -0.02:
                trend_direction = "STRONG_DOWNTREND"
                confidence = min(90, abs(vw_momentum) * 1000)
            elif vw_momentum < -0.005:
                trend_direction = "WEAK_DOWNTREND"
                confidence = min(70, abs(vw_momentum) * 1000)
            else:
                trend_direction = "SIDEWAYS"
                confidence = 50
            
            return {
                'trend_direction': trend_direction,
                'confidence': confidence,
                'vw_momentum': vw_momentum
            }
            
        except Exception as e:
            logger.warning(f"Error calculating trend strength: {e}")
            return {'trend_direction': 'SIDEWAYS', 'confidence': 50}
    
    def _detect_institutional_flow(
        self, 
        df: pd.DataFrame, 
        vwap_zones: Dict[str, float], 
        current_price: float
    ) -> Dict[str, Any]:
        """Detect institutional buying/selling patterns"""
        
        try:
            if not all(col in df.columns for col in ['close', 'volume']) or len(df) < 50:
                return {'flow_type': 'NO_INSTITUTIONAL_FLOW', 'confidence': 50}
            
            # Calculate volume metrics
            recent_volume = df['volume'].rolling(5).mean().iloc[-1]
            avg_volume = df['volume'].rolling(50).mean().iloc[-1]
            
            # Check if near VWAP with high volume
            near_vwap = abs(current_price - vwap_zones['vwap_center']) < (vwap_zones['vwap_center'] * 0.002)
            high_volume = recent_volume > (avg_volume * 2.0)
            
            if near_vwap and high_volume:
                # Determine direction based on price momentum
                price_momentum = df['close'].pct_change(5).iloc[-1]
                
                if price_momentum > 0.001:  # 0.1% up with volume
                    return {
                        'flow_type': 'INSTITUTIONAL_BUYING',
                        'confidence': self.confidence_thresholds['institutional_flow']
                    }
                elif price_momentum < -0.001:  # 0.1% down with volume
                    return {
                        'flow_type': 'INSTITUTIONAL_SELLING',
                        'confidence': self.confidence_thresholds['institutional_flow']
                    }
            
            return {'flow_type': 'NO_INSTITUTIONAL_FLOW', 'confidence': 50}
            
        except Exception as e:
            logger.warning(f"Error detecting institutional flow: {e}")
            return {'flow_type': 'NO_INSTITUTIONAL_FLOW', 'confidence': 50}
    
    def _check_vwap_alignment(
        self, 
        df_main: pd.DataFrame,
        multi_timeframe_data: Optional[Dict[str, pd.DataFrame]],
        current_price: float
    ) -> Dict[str, Any]:
        """Check VWAP alignment across timeframes"""
        
        try:
            if not multi_timeframe_data:
                # Single timeframe - use rolling VWAP comparison
                if 'close' in df_main.columns and len(df_main) >= 20:
                    vwap_1m = self._calculate_simple_vwap(df_main.tail(20)).iloc[-1]
                    vwap_5m = self._calculate_simple_vwap(df_main.tail(100)).iloc[-1] if len(df_main) >= 100 else vwap_1m
                    
                    if current_price > vwap_1m and current_price > vwap_5m:
                        return {'alignment': 'BULLISH_ALIGNMENT', 'confidence': 70}
                    elif current_price < vwap_1m and current_price < vwap_5m:
                        return {'alignment': 'BEARISH_ALIGNMENT', 'confidence': 70}
                    else:
                        return {'alignment': 'MIXED_ALIGNMENT', 'confidence': 40}
                else:
                    return {'alignment': 'NEUTRAL_ALIGNMENT', 'confidence': 50}
            
            # Multi-timeframe analysis
            vwap_1m = self._calculate_simple_vwap(df_main).iloc[-1]
            vwap_5m = self._calculate_simple_vwap(multi_timeframe_data.get('5m', df_main)).iloc[-1]
            vwap_15m = self._calculate_simple_vwap(multi_timeframe_data.get('15m', df_main)).iloc[-1]
            
            # Check alignment
            above_all = current_price > vwap_1m and current_price > vwap_5m and current_price > vwap_15m
            below_all = current_price < vwap_1m and current_price < vwap_5m and current_price < vwap_15m
            
            if above_all:
                return {'alignment': 'BULLISH_ALIGNMENT', 'confidence': 80}
            elif below_all:
                return {'alignment': 'BEARISH_ALIGNMENT', 'confidence': 80}
            else:
                return {'alignment': 'MIXED_ALIGNMENT', 'confidence': 40}
                
        except Exception as e:
            logger.warning(f"Error checking VWAP alignment: {e}")
            return {'alignment': 'NEUTRAL_ALIGNMENT', 'confidence': 50}
    
    def _synthesize_vwap_intelligence(
        self,
        vwap_data: Dict[str, pd.Series],
        vwap_zones: Dict[str, float],
        breakout_analysis: Dict[str, Any],
        trend_analysis: Dict[str, Any],
        institutional_analysis: Dict[str, Any],
        alignment_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Synthesize all VWAP components into final intelligence"""
        
        # Signal weights for composite scoring
        signal_weights = {
            'vwap_breakout': 40,      # Highest weight
            'trend_strength': 30,     # Strong secondary
            'institutional_flow': 20,  # Important confirmation
            'vwap_alignment': 10      # Fine-tuning
        }
        
        # Calculate composite confidence score
        composite_confidence = (
            (breakout_analysis['confidence'] * signal_weights['vwap_breakout']) +
            (trend_analysis['confidence'] * signal_weights['trend_strength']) +
            (institutional_analysis['confidence'] * signal_weights['institutional_flow']) +
            (alignment_analysis['confidence'] * signal_weights['vwap_alignment'])
        ) / 100
        
        # Determine primary signal and bull/bear contributions
        primary_signal = breakout_analysis['signal']
        
        # Calculate bull/bear contributions based on signals
        bull_contribution, bear_contribution = self._calculate_vwap_contributions(
            breakout_analysis, trend_analysis, institutional_analysis, alignment_analysis
        )
        
        # Generate trade recommendation
        trade_recommendation = self._generate_trade_recommendation(
            breakout_analysis, vwap_zones, trend_analysis
        )
        
        return {
            'primary_signal': primary_signal,
            'confidence': min(95, composite_confidence),
            'bull_contribution': bull_contribution,
            'bear_contribution': bear_contribution,
            'vwap_zones': vwap_zones,
            'breakout_analysis': breakout_analysis,
            'trend_analysis': trend_analysis,
            'institutional_analysis': institutional_analysis,
            'alignment_analysis': alignment_analysis,
            'trade_recommendation': trade_recommendation,
            'supporting_factors': [
                trend_analysis['trend_direction'],
                institutional_analysis['flow_type'],
                alignment_analysis['alignment']
            ]
        }
    
    def _calculate_vwap_contributions(
        self,
        breakout_analysis: Dict[str, Any],
        trend_analysis: Dict[str, Any],
        institutional_analysis: Dict[str, Any],
        alignment_analysis: Dict[str, Any]
    ) -> Tuple[float, float]:
        """Calculate bull/bear contributions from VWAP signals"""
        
        bull_score = 50.0
        bear_score = 50.0
        
        # Breakout signal contributions
        signal = breakout_analysis['signal']
        confidence = breakout_analysis['confidence']
        
        if 'BULLISH' in signal or 'MEAN_REVERSION_BULLISH' in signal:
            bull_score += (confidence - 50) * 0.4
            bear_score -= (confidence - 50) * 0.4
        elif 'BEARISH' in signal or 'MEAN_REVERSION_BEARISH' in signal:
            bear_score += (confidence - 50) * 0.4
            bull_score -= (confidence - 50) * 0.4
        
        # Trend strength contributions
        trend_dir = trend_analysis['trend_direction']
        trend_conf = trend_analysis['confidence']
        
        if 'UPTREND' in trend_dir:
            bull_score += (trend_conf - 50) * 0.3
            bear_score -= (trend_conf - 50) * 0.3
        elif 'DOWNTREND' in trend_dir:
            bear_score += (trend_conf - 50) * 0.3
            bull_score -= (trend_conf - 50) * 0.3
        
        # Institutional flow contributions
        flow_type = institutional_analysis['flow_type']
        flow_conf = institutional_analysis['confidence']
        
        if 'BUYING' in flow_type:
            bull_score += (flow_conf - 50) * 0.2
            bear_score -= (flow_conf - 50) * 0.2
        elif 'SELLING' in flow_type:
            bear_score += (flow_conf - 50) * 0.2
            bull_score -= (flow_conf - 50) * 0.2
        
        # Alignment contributions
        alignment = alignment_analysis['alignment']
        align_conf = alignment_analysis['confidence']
        
        if 'BULLISH' in alignment:
            bull_score += (align_conf - 50) * 0.1
            bear_score -= (align_conf - 50) * 0.1
        elif 'BEARISH' in alignment:
            bear_score += (align_conf - 50) * 0.1
            bull_score -= (align_conf - 50) * 0.1
        
        # Ensure scores are within bounds
        bull_score = max(10, min(90, bull_score))
        bear_score = max(10, min(90, bear_score))
        
        return bull_score, bear_score
    
    def _generate_trade_recommendation(
        self,
        breakout_analysis: Dict[str, Any],
        vwap_zones: Dict[str, float],
        trend_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate specific trade recommendations based on VWAP analysis"""
        
        signal = breakout_analysis['signal']
        zones = vwap_zones
        
        recommendation = {
            'action': 'HOLD',
            'entry_level': zones['vwap_center'],
            'stop_loss': zones['vwap_center'],
            'target': zones['vwap_center'],
            'risk_reward': 1.0
        }
        
        try:
            if 'BULLISH_BREAKOUT' in signal:
                recommendation.update({
                    'action': 'BUY_BULL_PUT_SPREAD',
                    'entry_level': zones['resistance'],
                    'stop_loss': zones['support'],
                    'target': zones['strong_resistance'],
                    'risk_reward': (zones['strong_resistance'] - zones['resistance']) / (zones['resistance'] - zones['support'])
                })
                
            elif 'BEARISH_BREAKDOWN' in signal:
                recommendation.update({
                    'action': 'BUY_BEAR_CALL_SPREAD',
                    'entry_level': zones['support'],
                    'stop_loss': zones['resistance'],
                    'target': zones['strong_support'],
                    'risk_reward': (zones['support'] - zones['strong_support']) / (zones['resistance'] - zones['support'])
                })
                
            elif 'MEAN_REVERSION_BULLISH' in signal:
                recommendation.update({
                    'action': 'BUY_BULL_PUT_SPREAD',
                    'entry_level': zones['support'],
                    'stop_loss': zones['strong_support'],
                    'target': zones['vwap_center'],
                    'risk_reward': (zones['vwap_center'] - zones['support']) / (zones['support'] - zones['strong_support'])
                })
                
            elif 'MEAN_REVERSION_BEARISH' in signal:
                recommendation.update({
                    'action': 'BUY_BEAR_CALL_SPREAD',
                    'entry_level': zones['resistance'],
                    'stop_loss': zones['strong_resistance'],
                    'target': zones['vwap_center'],
                    'risk_reward': (zones['resistance'] - zones['vwap_center']) / (zones['strong_resistance'] - zones['resistance'])
                })
        
        except Exception as e:
            logger.warning(f"Error generating trade recommendation: {e}")
        
        return recommendation
    
    def _get_neutral_analysis(self) -> Dict[str, Any]:
        """Return neutral analysis when VWAP calculation fails"""
        return {
            'primary_signal': 'NEUTRAL',
            'confidence': 50.0,
            'bull_contribution': 50.0,
            'bear_contribution': 50.0,
            'vwap_zones': {},
            'breakout_analysis': {'signal': 'NEUTRAL', 'confidence': 50},
            'trend_analysis': {'trend_direction': 'SIDEWAYS', 'confidence': 50},
            'institutional_analysis': {'flow_type': 'NO_INSTITUTIONAL_FLOW', 'confidence': 50},
            'alignment_analysis': {'alignment': 'NEUTRAL_ALIGNMENT', 'confidence': 50},
            'trade_recommendation': {'action': 'HOLD'},
            'supporting_factors': ['NEUTRAL', 'NEUTRAL', 'NEUTRAL']
        }

def main():
    """Test the Dynamic VWAP Analyzer"""
    
    print("🎯 TESTING DYNAMIC VWAP ANALYZER")
    print("=" * 70)
    
    # Initialize analyzer
    analyzer = DynamicVWAPAnalyzer()
    
    # Create sample price data
    dates = pd.date_range('2024-01-01 09:30:00', periods=100, freq='1min')
    sample_data = pd.DataFrame({
        'close': np.random.normal(545, 2, 100).cumsum() / 100 + 540,
        'volume': np.random.normal(1000, 200, 100)
    }, index=dates)
    
    # Add some trend
    sample_data['close'] = sample_data['close'] + np.linspace(0, 5, 100)
    
    # Test VWAP analysis
    current_price = sample_data['close'].iloc[-1]
    
    print(f"\n🎯 RUNNING VWAP ANALYSIS:")
    print(f"   Current Price: ${current_price:.2f}")
    print(f"   Data Points: {len(sample_data)}")
    
    vwap_intelligence = analyzer.analyze_vwap_intelligence(sample_data, current_price)
    
    print(f"\n📊 VWAP INTELLIGENCE SUMMARY:")
    print(f"   Primary Signal: {vwap_intelligence['primary_signal']}")
    print(f"   Confidence: {vwap_intelligence['confidence']:.1f}%")
    print(f"   Bull Contribution: {vwap_intelligence['bull_contribution']:.1f}")
    print(f"   Bear Contribution: {vwap_intelligence['bear_contribution']:.1f}")
    
    print(f"\n🎯 TRADE RECOMMENDATION:")
    rec = vwap_intelligence['trade_recommendation']
    print(f"   Action: {rec['action']}")
    print(f"   Entry: ${rec['entry_level']:.2f}")
    print(f"   Target: ${rec['target']:.2f}")
    print(f"   Stop: ${rec['stop_loss']:.2f}")
    
    print(f"\n🔍 SUPPORTING FACTORS:")
    for factor in vwap_intelligence['supporting_factors']:
        print(f"   • {factor}")

if __name__ == "__main__":
    main()
