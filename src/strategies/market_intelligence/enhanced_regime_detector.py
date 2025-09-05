#!/usr/bin/env python3
"""
Enhanced Market Regime Detection System
======================================

Multi-timeframe, adaptive regime detection with transition analysis.
Fixes the single-regime bias and static VWAP issues.

Location: src/strategies/market_intelligence/ (following .cursorrules structure)
Author: Advanced Options Trading System - Market Intelligence Enhancement
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class RegimeType(Enum):
    """Market regime types with confidence levels"""
    STRONG_BULLISH = "STRONG_BULLISH"
    BULLISH = "BULLISH"
    NEUTRAL = "NEUTRAL"
    BEARISH = "BEARISH"
    STRONG_BEARISH = "STRONG_BEARISH"
    TRANSITION = "TRANSITION"

@dataclass
class RegimeAnalysis:
    """Enhanced regime analysis with multi-timeframe data"""
    primary_regime: RegimeType
    confidence: float
    short_term_regime: RegimeType  # 1-hour
    medium_term_regime: RegimeType  # 4-hour
    transition_probability: float
    regime_strength: float
    supporting_factors: List[str]
    risk_factors: List[str]
    recommended_strategy: str

class EnhancedRegimeDetector:
    """
    Enhanced multi-timeframe regime detection system
    
    Features:
    - Multi-timeframe analysis (1H, 4H, daily)
    - Regime transition detection
    - Confidence-based filtering
    - Adaptive sensitivity
    - Cross-validation with price action
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Regime detection parameters
        self.confidence_threshold = 60.0  # Minimum confidence to trade
        self.transition_threshold = 0.3   # Transition probability threshold
        
        # Multi-timeframe weights
        self.timeframe_weights = {
            'short_term': 0.50,   # 1-hour (most important for 0DTE)
            'medium_term': 0.30,  # 4-hour (trend confirmation)
            'long_term': 0.20     # Daily (overall context)
        }
        
        # Recent performance tracking for adaptive sensitivity
        self.recent_accuracy = []
        self.max_history = 20
        
        logger.info("🎯 ENHANCED REGIME DETECTOR INITIALIZED")
        logger.info(f"   Confidence Threshold: {self.confidence_threshold}%")
        logger.info(f"   Timeframe Weights: {self.timeframe_weights}")
    
    def analyze_enhanced_regime(self, 
                              spy_data: pd.DataFrame,
                              options_data: pd.DataFrame,
                              spy_price: float,
                              vwap_intelligence: Dict) -> RegimeAnalysis:
        """
        Comprehensive multi-timeframe regime analysis
        """
        
        # 1. Multi-timeframe trend analysis
        short_term_trend = self._analyze_short_term_trend(spy_data, spy_price)
        medium_term_trend = self._analyze_medium_term_trend(spy_data, spy_price)
        long_term_trend = self._analyze_long_term_trend(spy_data, spy_price)
        
        # 2. Regime transition detection
        transition_analysis = self._detect_regime_transitions(
            spy_data, short_term_trend, medium_term_trend
        )
        
        # 3. VWAP validation with price action
        vwap_validation = self._validate_vwap_with_price_action(
            vwap_intelligence, spy_data, spy_price
        )
        
        # 4. Options flow confirmation
        flow_confirmation = self._analyze_options_flow_regime(options_data)
        
        # 5. Synthesize multi-timeframe regime
        regime_synthesis = self._synthesize_multi_timeframe_regime(
            short_term_trend, medium_term_trend, long_term_trend,
            transition_analysis, vwap_validation, flow_confirmation
        )
        
        # 6. Apply confidence filtering
        final_regime = self._apply_confidence_filtering(regime_synthesis)
        
        return final_regime
    
    def _analyze_short_term_trend(self, spy_data: pd.DataFrame, spy_price: float) -> Dict:
        """Analyze 1-hour trend for immediate 0DTE decisions"""
        
        if len(spy_data) < 60:  # Need at least 1 hour of data
            return {'regime': RegimeType.NEUTRAL, 'confidence': 30.0, 'strength': 0.0}
        
        # Get last 60 minutes (1 hour)
        recent_data = spy_data.tail(60)
        
        # Ensure we have the required columns
        if 'close' not in recent_data.columns or 'volume' not in recent_data.columns:
            logger.warning(f"Missing required columns in SPY data. Available: {list(recent_data.columns)}")
            return {'regime': RegimeType.NEUTRAL, 'confidence': 30.0, 'strength': 0.0}
        
        # Price momentum
        price_change = (spy_price - recent_data['close'].iloc[0]) / recent_data['close'].iloc[0]
        
        # Volume-weighted price momentum
        vwap_1h = (recent_data['close'] * recent_data['volume']).sum() / recent_data['volume'].sum()
        vwap_momentum = (spy_price - vwap_1h) / vwap_1h
        
        # Trend strength (linear regression slope)
        x = np.arange(len(recent_data))
        slope = np.polyfit(x, recent_data['close'], 1)[0]
        trend_strength = abs(slope) / recent_data['close'].mean() * 100
        
        # Determine regime
        if price_change > 0.005 and vwap_momentum > 0.003:  # Strong bullish
            regime = RegimeType.STRONG_BULLISH
            confidence = min(95, 60 + trend_strength * 10)
        elif price_change > 0.002 and vwap_momentum > 0.001:  # Bullish
            regime = RegimeType.BULLISH
            confidence = min(85, 50 + trend_strength * 10)
        elif price_change < -0.005 and vwap_momentum < -0.003:  # Strong bearish
            regime = RegimeType.STRONG_BEARISH
            confidence = min(95, 60 + trend_strength * 10)
        elif price_change < -0.002 and vwap_momentum < -0.001:  # Bearish
            regime = RegimeType.BEARISH
            confidence = min(85, 50 + trend_strength * 10)
        else:  # Neutral/choppy
            regime = RegimeType.NEUTRAL
            confidence = max(40, 60 - trend_strength * 5)
        
        return {
            'regime': regime,
            'confidence': confidence,
            'strength': trend_strength,
            'price_momentum': price_change,
            'vwap_momentum': vwap_momentum
        }
    
    def _analyze_medium_term_trend(self, spy_data: pd.DataFrame, spy_price: float) -> Dict:
        """Analyze 4-hour trend for context and confirmation"""
        
        if len(spy_data) < 240:  # Need at least 4 hours of data
            return {'regime': RegimeType.NEUTRAL, 'confidence': 30.0, 'strength': 0.0}
        
        # Get last 240 minutes (4 hours)
        medium_data = spy_data.tail(240)
        
        # Ensure we have the required columns
        if 'close' not in medium_data.columns:
            logger.warning(f"Missing 'close' column in SPY data for medium-term analysis")
            return {'regime': RegimeType.NEUTRAL, 'confidence': 30.0, 'strength': 0.0}
        
        # Calculate 4-hour moving averages
        sma_20 = medium_data['close'].rolling(20).mean().iloc[-1]
        sma_50 = medium_data['close'].rolling(50).mean().iloc[-1]
        
        # Price relative to moving averages
        price_vs_sma20 = (spy_price - sma_20) / sma_20
        price_vs_sma50 = (spy_price - sma_50) / sma_50
        
        # Moving average alignment
        ma_alignment = (sma_20 - sma_50) / sma_50
        
        # Determine medium-term regime
        if price_vs_sma20 > 0.003 and price_vs_sma50 > 0.005 and ma_alignment > 0.002:
            regime = RegimeType.STRONG_BULLISH
            confidence = 80
        elif price_vs_sma20 > 0.001 and price_vs_sma50 > 0.002:
            regime = RegimeType.BULLISH
            confidence = 70
        elif price_vs_sma20 < -0.003 and price_vs_sma50 < -0.005 and ma_alignment < -0.002:
            regime = RegimeType.STRONG_BEARISH
            confidence = 80
        elif price_vs_sma20 < -0.001 and price_vs_sma50 < -0.002:
            regime = RegimeType.BEARISH
            confidence = 70
        else:
            regime = RegimeType.NEUTRAL
            confidence = 50
        
        return {
            'regime': regime,
            'confidence': confidence,
            'price_vs_sma20': price_vs_sma20,
            'price_vs_sma50': price_vs_sma50,
            'ma_alignment': ma_alignment
        }
    
    def _analyze_long_term_trend(self, spy_data: pd.DataFrame, spy_price: float) -> Dict:
        """Analyze daily trend for overall market context"""
        
        if len(spy_data) < 390:  # Need at least 1 full trading day
            return {'regime': RegimeType.NEUTRAL, 'confidence': 30.0}
        
        # Ensure we have the required columns
        required_cols = ['open', 'high', 'low', 'close']
        missing_cols = [col for col in required_cols if col not in spy_data.columns]
        if missing_cols:
            logger.warning(f"Missing columns in SPY data for long-term analysis: {missing_cols}")
            return {'regime': RegimeType.NEUTRAL, 'confidence': 30.0}
        
        # Daily open (first price of the day)
        daily_open = spy_data.iloc[0]['open']
        daily_high = spy_data['high'].max()
        daily_low = spy_data['low'].min()
        
        # Daily performance
        daily_return = (spy_price - daily_open) / daily_open
        
        # Position within daily range
        daily_range = daily_high - daily_low
        range_position = (spy_price - daily_low) / daily_range if daily_range > 0 else 0.5
        
        # Determine long-term context
        if daily_return > 0.01 and range_position > 0.7:  # Strong daily performance, near highs
            regime = RegimeType.STRONG_BULLISH
            confidence = 75
        elif daily_return > 0.003 and range_position > 0.6:
            regime = RegimeType.BULLISH
            confidence = 65
        elif daily_return < -0.01 and range_position < 0.3:  # Weak daily performance, near lows
            regime = RegimeType.STRONG_BEARISH
            confidence = 75
        elif daily_return < -0.003 and range_position < 0.4:
            regime = RegimeType.BEARISH
            confidence = 65
        else:
            regime = RegimeType.NEUTRAL
            confidence = 50
        
        return {
            'regime': regime,
            'confidence': confidence,
            'daily_return': daily_return,
            'range_position': range_position
        }
    
    def _detect_regime_transitions(self, spy_data: pd.DataFrame, 
                                 short_term: Dict, medium_term: Dict) -> Dict:
        """Detect if market is transitioning between regimes"""
        
        # Check for regime divergence (transition signal)
        short_regime = short_term['regime']
        medium_regime = medium_term['regime']
        
        # Define regime hierarchy for comparison
        regime_values = {
            RegimeType.STRONG_BEARISH: -2,
            RegimeType.BEARISH: -1,
            RegimeType.NEUTRAL: 0,
            RegimeType.BULLISH: 1,
            RegimeType.STRONG_BULLISH: 2
        }
        
        short_value = regime_values.get(short_regime, 0)
        medium_value = regime_values.get(medium_regime, 0)
        
        # Calculate transition probability
        regime_divergence = abs(short_value - medium_value)
        
        if regime_divergence >= 2:  # Strong divergence (e.g., short-term bullish, medium-term bearish)
            transition_prob = 0.8
            transition_type = "STRONG_DIVERGENCE"
        elif regime_divergence == 1:  # Moderate divergence
            transition_prob = 0.4
            transition_type = "MODERATE_DIVERGENCE"
        else:  # Alignment
            transition_prob = 0.1
            transition_type = "ALIGNED"
        
        # Recent volatility (indicates potential transitions)
        if len(spy_data) >= 30:
            recent_volatility = spy_data['close'].tail(30).std() / spy_data['close'].tail(30).mean()
            if recent_volatility > 0.02:  # High volatility
                transition_prob *= 1.5
        
        return {
            'transition_probability': min(1.0, transition_prob),
            'transition_type': transition_type,
            'regime_divergence': regime_divergence,
            'is_transitioning': transition_prob > self.transition_threshold
        }
    
    def _validate_vwap_with_price_action(self, vwap_intelligence: Dict, 
                                       spy_data: pd.DataFrame, spy_price: float) -> Dict:
        """Cross-validate VWAP signals with actual price action"""
        
        vwap_signal = vwap_intelligence.get('primary_signal', 'NEUTRAL')
        vwap_confidence = vwap_intelligence.get('confidence', 50.0)
        
        # Get recent price action (last 30 minutes)
        if len(spy_data) >= 30:
            recent_prices = spy_data['close'].tail(30)
            price_trend = (recent_prices.iloc[-1] - recent_prices.iloc[0]) / recent_prices.iloc[0]
            
            # Validate VWAP signal against price action
            if 'BULLISH' in vwap_signal and price_trend > 0.001:
                validation_score = 1.0  # VWAP and price action agree
            elif 'BEARISH' in vwap_signal and price_trend < -0.001:
                validation_score = 1.0  # VWAP and price action agree
            elif 'NEUTRAL' in vwap_signal and abs(price_trend) < 0.001:
                validation_score = 0.8  # Neutral agreement
            else:
                validation_score = 0.3  # VWAP and price action disagree
            
            # Adjust VWAP confidence based on validation
            validated_confidence = vwap_confidence * validation_score
        else:
            validated_confidence = vwap_confidence * 0.5  # Reduce confidence if insufficient data
        
        return {
            'original_signal': vwap_signal,
            'original_confidence': vwap_confidence,
            'validated_confidence': validated_confidence,
            'validation_score': validation_score if len(spy_data) >= 30 else 0.5,
            'price_trend': price_trend if len(spy_data) >= 30 else 0.0
        }
    
    def _analyze_options_flow_regime(self, options_data: pd.DataFrame) -> Dict:
        """Analyze options flow for regime confirmation"""
        
        if len(options_data) == 0:
            return {'regime': RegimeType.NEUTRAL, 'confidence': 30.0}
        
        # Separate calls and puts
        calls = options_data[options_data['option_type'] == 'call']
        puts = options_data[options_data['option_type'] == 'put']
        
        if len(calls) == 0 or len(puts) == 0:
            return {'regime': RegimeType.NEUTRAL, 'confidence': 30.0}
        
        # Volume-weighted put/call ratio
        call_volume = calls['volume'].sum()
        put_volume = puts['volume'].sum()
        
        if call_volume + put_volume == 0:
            return {'regime': RegimeType.NEUTRAL, 'confidence': 30.0}
        
        pc_ratio = put_volume / call_volume if call_volume > 0 else 2.0
        
        # Regime determination based on P/C ratio
        if pc_ratio < 0.7:  # Low put/call ratio = bullish
            regime = RegimeType.BULLISH
            confidence = min(80, 50 + (0.7 - pc_ratio) * 100)
        elif pc_ratio > 1.3:  # High put/call ratio = bearish
            regime = RegimeType.BEARISH
            confidence = min(80, 50 + (pc_ratio - 1.3) * 50)
        else:  # Neutral range
            regime = RegimeType.NEUTRAL
            confidence = 60
        
        return {
            'regime': regime,
            'confidence': confidence,
            'pc_ratio': pc_ratio,
            'call_volume': call_volume,
            'put_volume': put_volume
        }
    
    def _synthesize_multi_timeframe_regime(self, short_term: Dict, medium_term: Dict, 
                                         long_term: Dict, transition: Dict,
                                         vwap_validation: Dict, flow: Dict) -> Dict:
        """Synthesize all timeframes into final regime assessment"""
        
        # Weight each component
        components = [
            (short_term, self.timeframe_weights['short_term']),
            (medium_term, self.timeframe_weights['medium_term']),
            (long_term, self.timeframe_weights['long_term']),
            (flow, 0.15),  # Options flow weight
            ({'regime': RegimeType.NEUTRAL, 'confidence': vwap_validation['validated_confidence']}, 0.10)  # VWAP validation
        ]
        
        # Calculate weighted regime scores
        regime_scores = {
            RegimeType.STRONG_BULLISH: 0,
            RegimeType.BULLISH: 0,
            RegimeType.NEUTRAL: 0,
            RegimeType.BEARISH: 0,
            RegimeType.STRONG_BEARISH: 0
        }
        
        total_confidence = 0
        
        for component, weight in components:
            regime = component['regime']
            confidence = component['confidence']
            
            # Add weighted score
            regime_scores[regime] += weight * confidence
            total_confidence += weight * confidence
        
        # Find dominant regime
        dominant_regime = max(regime_scores, key=regime_scores.get)
        dominant_score = regime_scores[dominant_regime]
        
        # Calculate final confidence
        total_weights = sum(self.timeframe_weights.values()) + 0.15 + 0.10  # Flow + VWAP validation weights
        final_confidence = dominant_score / total_weights * 100
        
        # Adjust for transitions
        if transition['is_transitioning']:
            final_confidence *= (1 - transition['transition_probability'] * 0.5)
            if final_confidence < 50:
                dominant_regime = RegimeType.TRANSITION
        
        return {
            'regime': dominant_regime,
            'confidence': min(95, final_confidence),
            'regime_scores': regime_scores,
            'transition_analysis': transition,
            'supporting_components': self._identify_supporting_components(components, dominant_regime)
        }
    
    def _apply_confidence_filtering(self, regime_synthesis: Dict) -> RegimeAnalysis:
        """Apply confidence thresholds and create final regime analysis"""
        
        regime = regime_synthesis['regime']
        confidence = regime_synthesis['confidence']
        transition = regime_synthesis['transition_analysis']
        
        # Apply confidence threshold
        if confidence < self.confidence_threshold:
            regime = RegimeType.NEUTRAL
            confidence = max(30, confidence * 0.7)
        
        # Determine recommended strategy
        strategy_map = {
            RegimeType.STRONG_BULLISH: "BULL_PUT_SPREAD",
            RegimeType.BULLISH: "BULL_PUT_SPREAD",
            RegimeType.NEUTRAL: "IRON_CONDOR",
            RegimeType.BEARISH: "BEAR_CALL_SPREAD",
            RegimeType.STRONG_BEARISH: "BEAR_CALL_SPREAD",
            RegimeType.TRANSITION: "NO_TRADE"
        }
        
        recommended_strategy = strategy_map.get(regime, "NO_TRADE")
        
        # Generate supporting factors and risk factors
        supporting_factors = regime_synthesis.get('supporting_components', [])
        risk_factors = []
        
        if transition['is_transitioning']:
            risk_factors.append(f"Market transitioning ({transition['transition_type']})")
        
        if confidence < 70:
            risk_factors.append("Low regime confidence")
        
        return RegimeAnalysis(
            primary_regime=regime,
            confidence=confidence,
            short_term_regime=RegimeType.NEUTRAL,  # Placeholder
            medium_term_regime=RegimeType.NEUTRAL,  # Placeholder
            transition_probability=transition['transition_probability'],
            regime_strength=confidence / 100,
            supporting_factors=supporting_factors,
            risk_factors=risk_factors,
            recommended_strategy=recommended_strategy
        )
    
    def _identify_supporting_components(self, components: List, dominant_regime: RegimeType) -> List[str]:
        """Identify which components support the dominant regime"""
        
        supporting = []
        for component, weight in components:
            if component['regime'] == dominant_regime:
                supporting.append(f"{component['regime'].value} ({component['confidence']:.1f}%)")
        
        return supporting
    
    def update_performance_feedback(self, predicted_regime: RegimeType, 
                                  actual_outcome: str, trade_pnl: float):
        """Update performance tracking for adaptive sensitivity"""
        
        # Determine if prediction was accurate
        was_accurate = False
        if predicted_regime in [RegimeType.BULLISH, RegimeType.STRONG_BULLISH] and trade_pnl > 0:
            was_accurate = True
        elif predicted_regime in [RegimeType.BEARISH, RegimeType.STRONG_BEARISH] and trade_pnl > 0:
            was_accurate = True
        elif predicted_regime == RegimeType.NEUTRAL and abs(trade_pnl) < 10:
            was_accurate = True
        
        # Update recent accuracy tracking
        self.recent_accuracy.append(was_accurate)
        if len(self.recent_accuracy) > self.max_history:
            self.recent_accuracy.pop(0)
        
        # Log performance
        current_accuracy = sum(self.recent_accuracy) / len(self.recent_accuracy) if self.recent_accuracy else 0.5
        logger.debug(f"Regime prediction accuracy: {current_accuracy:.1%} (last {len(self.recent_accuracy)} trades)")
