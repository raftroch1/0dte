#!/usr/bin/env python3
"""
Market Intelligence Engine - Advanced 0DTE Market Analysis
=========================================================

MULTI-LAYER INTELLIGENCE SYSTEM:
1. Technical Layer: RSI, VWAP, Price Action
2. Internals Layer: VIX Structure, GEX, P/C Ratio  
3. Flow Layer: Options Activity, Sector Rotation
4. ML Layer: Trained Model Predictions

This provides comprehensive market bias detection for fast-paced 0DTE trading.

Location: src/strategies/market_intelligence/ (following .cursorrules structure)
Author: Advanced Options Trading System - Market Intelligence
"""

import sys
import os
# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import warnings
warnings.filterwarnings('ignore')

# Import GEX analyzer and VWAP analyzer
try:
    from .gamma_exposure_analyzer import GammaExposureAnalyzer
    from .moving_average_shift_analyzer import MovingAverageShiftAnalyzer
except ImportError:
    from gamma_exposure_analyzer import GammaExposureAnalyzer
    from moving_average_shift_analyzer import MovingAverageShiftAnalyzer

@dataclass
class MarketIntelligence:
    """Comprehensive market intelligence analysis"""
    # Overall Bias Scores (0-100)
    bull_score: float
    bear_score: float
    neutral_score: float
    
    # Layer Scores
    technical_score: float
    internals_score: float
    flow_score: float
    ml_score: float
    
    # Specific Indicators
    vix_term_structure: Dict[str, float]
    vwap_analysis: Dict[str, float]
    rsi_analysis: Dict[str, float]
    put_call_analysis: Dict[str, float]
    ma_shift_intelligence: Dict[str, Any]  # NEW: Complete MA Shift analysis
    
    # Market Regime
    primary_regime: str  # 'BULLISH', 'BEARISH', 'NEUTRAL'
    regime_confidence: float
    volatility_environment: str  # 'LOW', 'MEDIUM', 'HIGH'
    
    # Strategy Recommendations
    optimal_strategies: List[str]
    avoid_strategies: List[str]
    
    # Reasoning
    key_factors: List[str]
    warnings: List[str]

class MarketIntelligenceEngine:
    """
    Advanced Market Intelligence Engine for 0DTE Trading
    
    Provides multi-layer analysis:
    - Technical indicators (RSI, VWAP, momentum)
    - Market internals (VIX structure, P/C ratio)
    - Options flow analysis
    - ML model integration
    """
    
    def __init__(self):
        # Initialize GEX analyzer and VWAP analyzer
        self.gex_analyzer = GammaExposureAnalyzer()
        self.ma_shift_analyzer = MovingAverageShiftAnalyzer()
        
        # ENHANCED: Rebalanced layer weights with MA Shift system
        self.layer_weights = {
            'flow': 0.35,         # Most reliable - options flow
            'ma_shift': 0.35,     # NEW: MA Shift system (replaces VWAP)
            'technical': 0.15,    # Reduced - context-aware RSI
            'internals': 0.10,    # Reduced - put/call ratio
            'gex': 0.05           # Further reduced - GEX environment
        }
        
        # VIX thresholds
        self.vix_thresholds = {
            'low_vol': 15,
            'medium_vol': 25,
            'high_vol': 35,
            'extreme_vol': 50
        }
        
        # VWAP deviation thresholds
        self.vwap_thresholds = {
            'strong_above': 0.005,  # 0.5% above VWAP
            'weak_above': 0.002,    # 0.2% above VWAP
            'neutral': 0.002,       # Within 0.2% of VWAP
            'weak_below': -0.002,   # 0.2% below VWAP
            'strong_below': -0.005  # 0.5% below VWAP
        }
        
        # RSI thresholds
        self.rsi_thresholds = {
            'oversold': 30,
            'neutral_low': 40,
            'neutral_high': 60,
            'overbought': 70
        }
        
        # Logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("🧠 MARKET INTELLIGENCE ENGINE INITIALIZED")
        self.logger.info(f"   Layer Weights: {self.layer_weights}")
        self.logger.info("   🎯 ENHANCED: Dynamic VWAP system integrated")
    
    def analyze_market_intelligence(
        self, 
        options_data: pd.DataFrame,
        spy_price: Optional[float] = None,
        vix_data: Optional[pd.DataFrame] = None,
        historical_prices: Optional[pd.DataFrame] = None
    ) -> MarketIntelligence:
        """
        Comprehensive market intelligence analysis
        
        Args:
            options_data: Current options chain data
            spy_price: Current SPY price (if available)
            vix_data: VIX and VIX9D data for term structure
            historical_prices: Historical price data for VWAP calculation
        """
        
        self.logger.info("🧠 RUNNING COMPREHENSIVE MARKET INTELLIGENCE ANALYSIS")
        
        # Layer 1: MA Shift Analysis (NEW - Primary trend detection)
        ma_shift_analysis = self._analyze_ma_shift_layer(options_data, spy_price, historical_prices)
        
        # Layer 2: Technical Analysis (Reduced weight)
        technical_analysis = self._analyze_technical_layer(
            options_data, spy_price, historical_prices
        )
        
        # Layer 3: Market Internals (with VWAP context)
        internals_analysis = self._analyze_internals_layer(
            options_data, vix_data, ma_shift_analysis.get('trend_analysis', {})
        )
        
        # Layer 4: Options Flow Analysis
        flow_analysis = self._analyze_flow_layer(options_data)
        
        # Layer 5: ML Integration (placeholder for now)
        ml_analysis = self._analyze_ml_layer(options_data)
        
        # Layer 6: GEX Analysis (Reduced weight)
        gex_analysis = self._analyze_gex_layer(options_data, spy_price)
        
        # Combine all layers with MA Shift-enhanced synthesis
        intelligence = self._synthesize_intelligence_with_vwap(
            ma_shift_analysis,
            technical_analysis,
            internals_analysis,
            flow_analysis,
            ml_analysis,
            gex_analysis
        )
        
        self.logger.info(f"🎯 INTELLIGENCE SYNTHESIS COMPLETE:")
        self.logger.info(f"   Primary Regime: {intelligence.primary_regime} ({intelligence.regime_confidence:.1f}%)")
        self.logger.info(f"   Bull Score: {intelligence.bull_score:.1f}")
        self.logger.info(f"   Bear Score: {intelligence.bear_score:.1f}")
        self.logger.info(f"   Neutral Score: {intelligence.neutral_score:.1f}")
        
        return intelligence
    
    def _analyze_ma_shift_layer(
        self,
        options_data: pd.DataFrame,
        spy_price: Optional[float],
        historical_prices: Optional[pd.DataFrame]
    ) -> Dict[str, Any]:
        """Analyze MA Shift layer - Primary trend detection system"""
        
        analysis = {
            'bull_score': 50.0,
            'bear_score': 50.0,
            'neutral_score': 50.0,
            'ma_shift_intelligence': {},
            'trend_analysis': {}
        }
        
        try:
            # Estimate current price if not provided
            if spy_price is None:
                spy_price = self._estimate_current_price(options_data)
            
            # Create price data for VWAP analysis
            if historical_prices is not None and not historical_prices.empty:
                price_data = historical_prices.copy()
                # Ensure we have required columns
                if 'close' not in price_data.columns and 'Close' in price_data.columns:
                    price_data['close'] = price_data['Close']
                if 'volume' not in price_data.columns and 'Volume' in price_data.columns:
                    price_data['volume'] = price_data['Volume']
            else:
                # Create minimal price data from current price
                price_data = pd.DataFrame({
                    'close': [spy_price] * 50,
                    'volume': [1000] * 50
                })
            
            # Run MA Shift analysis
            ma_shift_signal = self.ma_shift_analyzer.analyze_ma_shift_intelligence(
                price_data, spy_price
            )
            
            analysis['ma_shift_intelligence'] = {
                'signal': ma_shift_signal,
                'trend': ma_shift_signal.ma_trend,
                'confidence': ma_shift_signal.signal_confidence * 100,
                'momentum_score': ma_shift_signal.momentum_score,
                'breakout_potential': ma_shift_signal.breakout_potential
            }
            
            # Convert MA Shift signal to bull/bear scores
            if ma_shift_signal.ma_trend == 'BULLISH':
                bull_contribution = 60 + (ma_shift_signal.trend_strength * 30)
                bear_contribution = 40 - (ma_shift_signal.trend_strength * 30)
            elif ma_shift_signal.ma_trend == 'BEARISH':
                bull_contribution = 40 - (ma_shift_signal.trend_strength * 30)
                bear_contribution = 60 + (ma_shift_signal.trend_strength * 30)
            else:  # NEUTRAL
                bull_contribution = 50 + (ma_shift_signal.momentum_score * 10)
                bear_contribution = 50 - (ma_shift_signal.momentum_score * 10)
            
            analysis['bull_score'] = max(0, min(100, bull_contribution))
            analysis['bear_score'] = max(0, min(100, bear_contribution))
            analysis['neutral_score'] = 100 - analysis['bull_score'] - analysis['bear_score']
            
            # Create trend analysis for other layers
            if ma_shift_signal.ma_trend == 'BULLISH':
                trend_direction = 'UPTREND'
            elif ma_shift_signal.ma_trend == 'BEARISH':
                trend_direction = 'DOWNTREND'
            else:
                trend_direction = 'SIDEWAYS'
            
            # Determine trend strength
            if ma_shift_signal.trend_strength > 0.7:
                trend_strength = 'STRONG'
            elif ma_shift_signal.trend_strength > 0.4:
                trend_strength = 'MODERATE'
            else:
                trend_strength = 'WEAK'
            
            analysis['trend_analysis'] = {
                'trend_direction': trend_direction,
                'trend_strength': trend_strength,
                'trend_confidence': ma_shift_signal.signal_confidence * 100,
                'bull_contribution': analysis['bull_score'],
                'bear_contribution': analysis['bear_score']
            }
            
            self.logger.info(f"🎯 MA SHIFT LAYER ANALYSIS:")
            self.logger.info(f"   Signal Type: {ma_shift_signal.signal_type}")
            self.logger.info(f"   Trend Direction: {trend_direction}")
            self.logger.info(f"   Confidence: {ma_shift_signal.signal_confidence * 100:.1f}%")
            
        except Exception as e:
            self.logger.warning(f"MA Shift layer analysis failed: {e}")
            # Return neutral analysis on failure
            analysis['trend_analysis'] = {
                'trend_direction': 'SIDEWAYS',
                'trend_strength': 'WEAK',
                'trend_confidence': 50.0,
                'bull_contribution': 50.0,
                'bear_contribution': 50.0
            }
        
        return analysis
    
    def _analyze_technical_layer(
        self, 
        options_data: pd.DataFrame,
        spy_price: Optional[float],
        historical_prices: Optional[pd.DataFrame]
    ) -> Dict[str, Any]:
        """Analyze technical indicators layer with TREND CONTEXT"""
        
        analysis = {
            'bull_score': 50.0,
            'bear_score': 50.0,
            'neutral_score': 50.0,
            'rsi_analysis': {},
            'vwap_analysis': {},
            'momentum_analysis': {},
            'trend_analysis': {}  # NEW: Critical trend context
        }
        
        # Estimate current price if not provided
        if spy_price is None:
            spy_price = self._estimate_current_price(options_data)
        
        # CRITICAL: Trend Context Analysis (Foundation for all other indicators)
        trend_analysis = self._analyze_trend_context(spy_price, historical_prices, options_data)
        analysis['trend_analysis'] = trend_analysis
        
        # Context-Aware RSI Analysis (REAL FIX)
        rsi_score = self._calculate_rsi_from_options(options_data)
        rsi_analysis = self._analyze_context_aware_rsi(rsi_score, trend_analysis)
        analysis['rsi_analysis'] = rsi_analysis
        
        # VWAP Analysis
        vwap_analysis = self._calculate_vwap_deviation(spy_price, historical_prices, options_data)
        analysis['vwap_analysis'] = vwap_analysis
        
        # Momentum Analysis from options moneyness
        momentum_analysis = self._analyze_options_momentum(options_data)
        analysis['momentum_analysis'] = momentum_analysis
        
        # ENHANCED: Combine technical scores with MOMENTUM emphasis
        rsi_weight = 0.30      # Reduced - was causing bearish bias
        vwap_weight = 0.25     # Reduced 
        momentum_weight = 0.45 # INCREASED - momentum is key for trend detection
        
        analysis['bull_score'] = (
            analysis['rsi_analysis']['bull_contribution'] * rsi_weight +
            vwap_analysis['bull_contribution'] * vwap_weight +
            momentum_analysis['bull_contribution'] * momentum_weight
        )
        
        analysis['bear_score'] = (
            analysis['rsi_analysis']['bear_contribution'] * rsi_weight +
            vwap_analysis['bear_contribution'] * vwap_weight +
            momentum_analysis['bear_contribution'] * momentum_weight
        )
        
        analysis['neutral_score'] = 100 - analysis['bull_score'] - analysis['bear_score']
        
        return analysis
    
    def _analyze_internals_layer(
        self, 
        options_data: pd.DataFrame,
        vix_data: Optional[pd.DataFrame],
        trend_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze market internals layer"""
        
        analysis = {
            'bull_score': 50.0,
            'bear_score': 50.0,
            'neutral_score': 50.0,
            'vix_term_structure': {},
            'put_call_analysis': {},
            'volatility_analysis': {}
        }
        
        # VIX Term Structure Analysis
        vix_analysis = self._analyze_vix_term_structure(vix_data, options_data)
        analysis['vix_term_structure'] = vix_analysis
        
        # Context-Aware Put/Call Ratio Analysis (REAL FIX)
        if trend_analysis is not None:
            market_regime = 'BULLISH' if trend_analysis['trend_direction'] == 'UPTREND' else 'BEARISH' if trend_analysis['trend_direction'] == 'DOWNTREND' else 'NEUTRAL'
        else:
            market_regime = 'NEUTRAL'
        pc_analysis = self._analyze_context_aware_put_call_ratio(options_data, market_regime)
        analysis['put_call_analysis'] = pc_analysis
        
        # Volatility Environment Analysis
        vol_analysis = self._analyze_volatility_environment(options_data, vix_data)
        analysis['volatility_analysis'] = vol_analysis
        
        # Combine internals scores
        vix_weight = 0.4
        pc_weight = 0.35
        vol_weight = 0.25
        
        analysis['bull_score'] = (
            vix_analysis['bull_contribution'] * vix_weight +
            pc_analysis['bull_contribution'] * pc_weight +
            vol_analysis['bull_contribution'] * vol_weight
        )
        
        analysis['bear_score'] = (
            vix_analysis['bear_contribution'] * vix_weight +
            pc_analysis['bear_contribution'] * pc_weight +
            vol_analysis['bear_contribution'] * vol_weight
        )
        
        analysis['neutral_score'] = 100 - analysis['bull_score'] - analysis['bear_score']
        
        return analysis
    
    def _analyze_flow_layer(self, options_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze options flow layer"""
        
        analysis = {
            'bull_score': 50.0,
            'bear_score': 50.0,
            'neutral_score': 50.0,
            'volume_analysis': {},
            'activity_analysis': {},
            'liquidity_analysis': {}
        }
        
        # Volume Analysis
        volume_analysis = self._analyze_options_volume(options_data)
        analysis['volume_analysis'] = volume_analysis
        
        # Activity Analysis (transactions, open interest)
        activity_analysis = self._analyze_options_activity(options_data)
        analysis['activity_analysis'] = activity_analysis
        
        # Liquidity Analysis
        liquidity_analysis = self._analyze_options_liquidity(options_data)
        analysis['liquidity_analysis'] = liquidity_analysis
        
        # Combine flow scores
        volume_weight = 0.4
        activity_weight = 0.35
        liquidity_weight = 0.25
        
        analysis['bull_score'] = (
            volume_analysis['bull_contribution'] * volume_weight +
            activity_analysis['bull_contribution'] * activity_weight +
            liquidity_analysis['bull_contribution'] * liquidity_weight
        )
        
        analysis['bear_score'] = (
            volume_analysis['bear_contribution'] * volume_weight +
            activity_analysis['bear_contribution'] * activity_weight +
            liquidity_analysis['bear_contribution'] * liquidity_weight
        )
        
        analysis['neutral_score'] = 100 - analysis['bull_score'] - analysis['bear_score']
        
        return analysis
    
    def _analyze_ml_layer(self, options_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze ML predictions layer (placeholder)"""
        
        # This will be integrated with our existing ML models
        analysis = {
            'bull_score': 50.0,
            'bear_score': 50.0,
            'neutral_score': 50.0,
            'model_predictions': {},
            'confidence_scores': {}
        }
        
        # TODO: Integrate with existing ML models from Phase 3
        # For now, return neutral scores
        
        return analysis
    
    def _analyze_gex_layer(self, options_data: pd.DataFrame, spy_price: Optional[float]) -> Dict[str, Any]:
        """Analyze Gamma Exposure layer - addresses direction detection issues"""
        
        if spy_price is None:
            spy_price = self._estimate_current_price(options_data)
        
        # Get GEX analysis
        gex_analysis = self.gex_analyzer.analyze_gamma_exposure(
            options_data, spy_price, time_to_expiry=0.25  # 0DTE = ~6 hours
        )
        
        # Convert GEX analysis to layer format
        analysis = {
            'bull_score': 50.0,  # GEX doesn't predict direction
            'bear_score': 50.0,  # GEX doesn't predict direction
            'neutral_score': 50.0,  # GEX doesn't predict direction
            'gex_analysis': gex_analysis,
            'direction_reliability': gex_analysis.direction_reliability,
            'confidence_multiplier': gex_analysis.confidence_multiplier,
            'signal_quality_score': gex_analysis.signal_quality_score
        }
        
        return analysis
    
    def _calculate_vwap_deviation(
        self, 
        current_price: float,
        historical_prices: Optional[pd.DataFrame],
        options_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """Calculate VWAP deviation analysis"""
        
        analysis = {
            'vwap_price': current_price,
            'current_price': current_price,
            'deviation_pct': 0.0,
            'deviation_interpretation': 'NEUTRAL',
            'bull_contribution': 50.0,
            'bear_contribution': 50.0
        }
        
        # If we have historical data, calculate proper VWAP
        if historical_prices is not None and not historical_prices.empty:
            # Calculate VWAP from historical data (simplified)
            if 'volume' in historical_prices.columns and 'close' in historical_prices.columns:
                vwap = (historical_prices['close'] * historical_prices['volume']).sum() / historical_prices['volume'].sum()
                analysis['vwap_price'] = vwap
            else:
                # Use simple average if no volume data
                analysis['vwap_price'] = historical_prices['close'].mean() if 'close' in historical_prices.columns else current_price
        else:
            # Estimate VWAP from options data volume-weighted strikes
            if 'volume' in options_data.columns and 'strike' in options_data.columns:
                total_volume = options_data['volume'].sum()
                if total_volume > 0:
                    volume_weighted_strike = (options_data['strike'] * options_data['volume']).sum() / total_volume
                    analysis['vwap_price'] = volume_weighted_strike
        
        # Calculate deviation
        deviation_pct = (current_price - analysis['vwap_price']) / analysis['vwap_price']
        analysis['deviation_pct'] = deviation_pct
        
        # Interpret deviation
        if deviation_pct > self.vwap_thresholds['strong_above']:
            analysis['deviation_interpretation'] = 'STRONG_ABOVE'
            analysis['bull_contribution'] = 85.0
            analysis['bear_contribution'] = 15.0
        elif deviation_pct > self.vwap_thresholds['weak_above']:
            analysis['deviation_interpretation'] = 'WEAK_ABOVE'
            analysis['bull_contribution'] = 65.0
            analysis['bear_contribution'] = 35.0
        elif deviation_pct < self.vwap_thresholds['strong_below']:
            analysis['deviation_interpretation'] = 'STRONG_BELOW'
            analysis['bull_contribution'] = 15.0
            analysis['bear_contribution'] = 85.0
        elif deviation_pct < self.vwap_thresholds['weak_below']:
            analysis['deviation_interpretation'] = 'WEAK_BELOW'
            analysis['bull_contribution'] = 35.0
            analysis['bear_contribution'] = 65.0
        else:
            analysis['deviation_interpretation'] = 'NEUTRAL'
            analysis['bull_contribution'] = 50.0
            analysis['bear_contribution'] = 50.0
        
        return analysis
    
    def _analyze_vix_term_structure(
        self, 
        vix_data: Optional[pd.DataFrame],
        options_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """Analyze VIX term structure"""
        
        analysis = {
            'vix_level': 20.0,  # Default
            'vix9d_level': 20.0,  # Default
            'term_structure_ratio': 1.0,
            'term_structure_interpretation': 'NEUTRAL',
            'bull_contribution': 50.0,
            'bear_contribution': 50.0
        }
        
        # If we have VIX data, use it
        if vix_data is not None and not vix_data.empty:
            if 'vix' in vix_data.columns:
                analysis['vix_level'] = vix_data['vix'].iloc[-1]  # Most recent
            if 'vix9d' in vix_data.columns:
                analysis['vix9d_level'] = vix_data['vix9d'].iloc[-1]  # Most recent
        else:
            # Estimate VIX from options data implied volatility
            if 'volume' in options_data.columns:
                avg_volume = options_data['volume'].mean()
                # Simple heuristic: higher volume = higher volatility
                estimated_vix = min(50, max(10, 15 + (avg_volume - 100) / 50))
                analysis['vix_level'] = estimated_vix
                analysis['vix9d_level'] = estimated_vix * 0.95  # Assume slight backwardation
        
        # Calculate term structure ratio
        if analysis['vix9d_level'] > 0:
            analysis['term_structure_ratio'] = analysis['vix_level'] / analysis['vix9d_level']
        
        # Interpret term structure
        if analysis['term_structure_ratio'] > 1.05:  # VIX > VIX9D (backwardation)
            analysis['term_structure_interpretation'] = 'BACKWARDATION'
            analysis['bear_contribution'] = 75.0  # Fear/stress
            analysis['bull_contribution'] = 25.0
        elif analysis['term_structure_ratio'] < 0.95:  # VIX < VIX9D (contango)
            analysis['term_structure_interpretation'] = 'CONTANGO'
            analysis['bull_contribution'] = 70.0  # Complacency
            analysis['bear_contribution'] = 30.0
        else:
            analysis['term_structure_interpretation'] = 'NEUTRAL'
            analysis['bull_contribution'] = 50.0
            analysis['bear_contribution'] = 50.0
        
        # Adjust based on absolute VIX level
        if analysis['vix_level'] > self.vix_thresholds['high_vol']:
            # High VIX = bearish bias
            analysis['bear_contribution'] = min(90, analysis['bear_contribution'] + 20)
            analysis['bull_contribution'] = max(10, analysis['bull_contribution'] - 20)
        elif analysis['vix_level'] < self.vix_thresholds['low_vol']:
            # Low VIX = bullish bias
            analysis['bull_contribution'] = min(90, analysis['bull_contribution'] + 15)
            analysis['bear_contribution'] = max(10, analysis['bear_contribution'] - 15)
        
        return analysis
    
    def _calculate_rsi_from_options(self, options_data: pd.DataFrame) -> float:
        """Calculate RSI-like indicator from options data - SIMPLIFIED"""
        
        if options_data.empty:
            return 50.0
        
        # Use put/call volume ratio as RSI proxy
        puts = options_data[options_data['option_type'] == 'put']
        calls = options_data[options_data['option_type'] == 'call']
        
        put_volume = puts['volume'].sum() if 'volume' in puts.columns and not puts.empty else 100
        call_volume = calls['volume'].sum() if 'volume' in calls.columns and not calls.empty else 100
        
        # Convert P/C ratio to RSI-like scale (0-100)
        pc_ratio = put_volume / max(call_volume, 1)
        
        # SIMPLIFIED: Direct mapping without double inversion
        # P/C ratio 0.5 = RSI 70 (bullish)
        # P/C ratio 1.0 = RSI 50 (neutral)
        # P/C ratio 2.0 = RSI 30 (bearish)
        rsi = max(20, min(80, 50 + (1.0 - pc_ratio) * 15))
        
        return rsi
    
    def _interpret_rsi(self, rsi: float) -> str:
        """Interpret RSI value"""
        if rsi <= self.rsi_thresholds['oversold']:
            return 'OVERSOLD'
        elif rsi <= self.rsi_thresholds['neutral_low']:
            return 'WEAK'
        elif rsi >= self.rsi_thresholds['overbought']:
            return 'OVERBOUGHT'
        elif rsi >= self.rsi_thresholds['neutral_high']:
            return 'STRONG'
        else:
            return 'NEUTRAL'
    
    def _analyze_options_momentum(self, options_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze momentum from options positioning"""
        
        analysis = {
            'momentum_direction': 'NEUTRAL',
            'momentum_strength': 'WEAK',
            'bull_contribution': 50.0,
            'bear_contribution': 50.0
        }
        
        if options_data.empty or 'moneyness' not in options_data.columns:
            return analysis
        
        # ENHANCED: Analyze moneyness distribution with VOLUME weighting
        if 'volume' in options_data.columns:
            # Volume-weighted moneyness for better momentum detection
            total_volume = options_data['volume'].sum()
            if total_volume > 0:
                weighted_moneyness = (options_data['moneyness'] * options_data['volume']).sum() / total_volume
            else:
                weighted_moneyness = options_data['moneyness'].mean()
        else:
            weighted_moneyness = options_data['moneyness'].mean()
        
        moneyness_std = options_data['moneyness'].std()
        
        # FIXED: Strong momentum detection with volume weighting
        if abs(weighted_moneyness) > 0.015:  # 1.5% volume-weighted moneyness
            analysis['momentum_strength'] = 'STRONG'
            if weighted_moneyness > 0:
                analysis['momentum_direction'] = 'BULLISH'
                analysis['bull_contribution'] = 75.0  # Reduced from 80 for balance
                analysis['bear_contribution'] = 25.0
            else:
                analysis['momentum_direction'] = 'BEARISH'
                analysis['bull_contribution'] = 25.0
                analysis['bear_contribution'] = 75.0
        elif moneyness_std > 0.05:  # High volatility in moneyness
            analysis['momentum_strength'] = 'MIXED'
            analysis['momentum_direction'] = 'SIDEWAYS'
            analysis['bull_contribution'] = 45.0
            analysis['bear_contribution'] = 45.0
        else:
            analysis['momentum_strength'] = 'WEAK'
            analysis['momentum_direction'] = 'NEUTRAL'
            analysis['bull_contribution'] = 50.0
            analysis['bear_contribution'] = 50.0
        
        return analysis
    
    def _analyze_put_call_ratio(self, options_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze put/call ratio"""
        
        analysis = {
            'put_call_ratio': 1.0,
            'interpretation': 'NEUTRAL',
            'bull_contribution': 50.0,
            'bear_contribution': 50.0
        }
        
        if options_data.empty:
            return analysis
        
        puts = options_data[options_data['option_type'] == 'put']
        calls = options_data[options_data['option_type'] == 'call']
        
        # FIXED: Use VOLUME instead of COUNT for accurate P/C ratio
        put_volume = puts['volume'].sum() if 'volume' in puts.columns and not puts.empty else 0
        call_volume = calls['volume'].sum() if 'volume' in calls.columns and not calls.empty else 1
        
        pc_ratio = put_volume / max(call_volume, 1)
        analysis['put_call_ratio'] = pc_ratio
        
        # RESTORED: Tighter thresholds for 0DTE
        if pc_ratio > 1.3:  # Back to 1.3 from 1.5
            analysis['interpretation'] = 'BEARISH'
            analysis['bear_contribution'] = 75.0
            analysis['bull_contribution'] = 25.0
        elif pc_ratio > 1.1:  # Back to 1.1 from 1.5
            analysis['interpretation'] = 'WEAK_BEARISH'
            analysis['bear_contribution'] = 60.0
            analysis['bull_contribution'] = 40.0
        elif pc_ratio < 0.7:  # Back to 0.7 from 0.6
            analysis['interpretation'] = 'BULLISH'
            analysis['bull_contribution'] = 75.0
            analysis['bear_contribution'] = 25.0
        elif pc_ratio < 0.9:  # Back to 0.9 from 0.8
            analysis['interpretation'] = 'WEAK_BULLISH'
            analysis['bull_contribution'] = 65.0
            analysis['bear_contribution'] = 35.0
        else:
            # Neutral zone: 0.9-1.1 (was 0.8-1.5)
            analysis['interpretation'] = 'NEUTRAL'
            analysis['bull_contribution'] = 50.0
            analysis['bear_contribution'] = 50.0
        
        return analysis
    
    def _analyze_volatility_environment(
        self, 
        options_data: pd.DataFrame,
        vix_data: Optional[pd.DataFrame]
    ) -> Dict[str, Any]:
        """Analyze volatility environment"""
        
        analysis = {
            'volatility_level': 'MEDIUM',
            'vol_percentile': 50.0,
            'bull_contribution': 50.0,
            'bear_contribution': 50.0
        }
        
        # Estimate volatility from options volume
        if not options_data.empty and 'volume' in options_data.columns:
            avg_volume = options_data['volume'].mean()
            
            if avg_volume > 500:
                analysis['volatility_level'] = 'HIGH'
                analysis['vol_percentile'] = 80.0
                analysis['bear_contribution'] = 70.0
                analysis['bull_contribution'] = 30.0
            elif avg_volume < 50:
                analysis['volatility_level'] = 'LOW'
                analysis['vol_percentile'] = 20.0
                analysis['bull_contribution'] = 70.0
                analysis['bear_contribution'] = 30.0
            else:
                analysis['volatility_level'] = 'MEDIUM'
                analysis['vol_percentile'] = 50.0
        
        return analysis
    
    def _analyze_options_volume(self, options_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze options volume patterns"""
        
        analysis = {
            'total_volume': 0,
            'call_volume': 0,
            'put_volume': 0,
            'volume_interpretation': 'NEUTRAL',
            'bull_contribution': 50.0,
            'bear_contribution': 50.0
        }
        
        if options_data.empty or 'volume' not in options_data.columns:
            return analysis
        
        calls = options_data[options_data['option_type'] == 'call']
        puts = options_data[options_data['option_type'] == 'put']
        
        analysis['call_volume'] = calls['volume'].sum() if not calls.empty else 0
        analysis['put_volume'] = puts['volume'].sum() if not puts.empty else 0
        analysis['total_volume'] = analysis['call_volume'] + analysis['put_volume']
        
        # Analyze volume bias
        if analysis['total_volume'] > 0:
            call_pct = analysis['call_volume'] / analysis['total_volume']
            
            if call_pct > 0.65:  # Heavy call volume
                analysis['volume_interpretation'] = 'BULLISH'
                analysis['bull_contribution'] = 75.0
                analysis['bear_contribution'] = 25.0
            elif call_pct < 0.35:  # Heavy put volume
                analysis['volume_interpretation'] = 'BEARISH'
                analysis['bear_contribution'] = 75.0
                analysis['bull_contribution'] = 25.0
            else:
                analysis['volume_interpretation'] = 'NEUTRAL'
        
        return analysis
    
    def _analyze_options_activity(self, options_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze options activity patterns"""
        
        analysis = {
            'total_transactions': 0,
            'activity_level': 'MEDIUM',
            'bull_contribution': 50.0,
            'bear_contribution': 50.0
        }
        
        if options_data.empty:
            return analysis
        
        if 'transactions' in options_data.columns:
            analysis['total_transactions'] = options_data['transactions'].sum()
            
            if analysis['total_transactions'] > 1000:
                analysis['activity_level'] = 'HIGH'
            elif analysis['total_transactions'] < 100:
                analysis['activity_level'] = 'LOW'
        
        # High activity can indicate institutional interest
        if analysis['activity_level'] == 'HIGH':
            # Slight bullish bias for high activity (institutional interest)
            analysis['bull_contribution'] = 55.0
            analysis['bear_contribution'] = 45.0
        
        return analysis
    
    def _analyze_options_liquidity(self, options_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze options liquidity"""
        
        analysis = {
            'liquidity_score': 50.0,
            'liquidity_level': 'MEDIUM',
            'bull_contribution': 50.0,
            'bear_contribution': 50.0
        }
        
        if options_data.empty:
            return analysis
        
        # Calculate liquidity score from volume and transactions
        if 'volume' in options_data.columns:
            avg_volume = options_data['volume'].mean()
            
            if avg_volume > 200:
                analysis['liquidity_level'] = 'HIGH'
                analysis['liquidity_score'] = 80.0
                # High liquidity = slight bullish bias (healthy market)
                analysis['bull_contribution'] = 55.0
                analysis['bear_contribution'] = 45.0
            elif avg_volume < 50:
                analysis['liquidity_level'] = 'LOW'
                analysis['liquidity_score'] = 30.0
                # Low liquidity = slight bearish bias (stressed market)
                analysis['bear_contribution'] = 55.0
                analysis['bull_contribution'] = 45.0
        
        return analysis
    
    def _synthesize_intelligence_with_vwap(
        self,
        ma_shift_analysis: Dict[str, Any],
        technical_analysis: Dict[str, Any],
        internals_analysis: Dict[str, Any],
        flow_analysis: Dict[str, Any],
        ml_analysis: Dict[str, Any],
        gex_analysis: Dict[str, Any]
    ) -> MarketIntelligence:
        """Synthesize all layers into final intelligence with MA Shift-enhanced analysis"""
        
        # ENHANCED: Weighted combination using MA Shift-rebalanced layer weights
        bull_score = (
            flow_analysis['bull_score'] * self.layer_weights['flow'] +
            ma_shift_analysis['bull_score'] * self.layer_weights['ma_shift'] +
            technical_analysis['rsi_analysis']['bull_contribution'] * self.layer_weights['technical'] +
            internals_analysis['put_call_analysis']['bull_contribution'] * self.layer_weights['internals'] +
            gex_analysis['bull_score'] * self.layer_weights['gex']
        )
        
        bear_score = (
            flow_analysis['bear_score'] * self.layer_weights['flow'] +
            ma_shift_analysis['bear_score'] * self.layer_weights['ma_shift'] +
            technical_analysis['rsi_analysis']['bear_contribution'] * self.layer_weights['technical'] +
            internals_analysis['put_call_analysis']['bear_contribution'] * self.layer_weights['internals'] +
            gex_analysis['bear_score'] * self.layer_weights['gex']
        )
        
        neutral_score = 100 - bull_score - bear_score
        
        # CRITICAL FIX: Remove hardcoded bull market bias that was overriding VWAP signals
        # The previous logic was adding +10 bull score when SPY > $520, which completely
        # overrode strong VWAP bearish signals, causing the system to make wrong trades
        
        # ENHANCED: MA Shift Signal Prioritization
        # When MA Shift has high confidence (>60%), give it extra weight to override other layers
        ma_shift_intel = ma_shift_analysis.get('ma_shift_intelligence', {})
        ma_shift_confidence = ma_shift_intel.get('confidence', 0)
        ma_shift_signal = ma_shift_intel.get('trend', 'NEUTRAL')
        
        if ma_shift_confidence > 60:  # High confidence MA Shift signal
            ma_shift_boost = (ma_shift_confidence - 60) * 0.5  # Up to 20 point boost for 100% confidence
            
            if ma_shift_signal == 'BULLISH':
                bull_score += ma_shift_boost
                self.logger.info(f"🎯 HIGH CONFIDENCE MA SHIFT BOOST: +{ma_shift_boost:.1f} to BULL ({ma_shift_signal})")
            elif ma_shift_signal == 'BEARISH':
                bear_score += ma_shift_boost
                self.logger.info(f"🎯 HIGH CONFIDENCE MA SHIFT BOOST: +{ma_shift_boost:.1f} to BEAR ({ma_shift_signal})")
        
        # Ensure scores don't exceed 100
        total_score = bull_score + bear_score
        if total_score > 100:
            # Normalize scores to maintain 100% total
            bull_score = bull_score * 100 / total_score
            bear_score = bear_score * 100 / total_score
        neutral_score = max(0, 100 - bull_score - bear_score)
        
        # ENHANCED: MA Shift Override Logic for Very High Confidence Signals
        # If MA Shift has extremely high confidence (>80%), it can override other layers completely
        if ma_shift_confidence > 80:
            if ma_shift_signal == 'BULLISH':
                primary_regime = 'BULLISH'
                regime_confidence = min(95, ma_shift_confidence)
                self.logger.info(f"🎯 MA SHIFT OVERRIDE: Strong bullish signal ({ma_shift_confidence:.1f}% confidence)")
            elif ma_shift_signal == 'BEARISH':
                primary_regime = 'BEARISH'
                regime_confidence = min(95, ma_shift_confidence)
                self.logger.info(f"🎯 MA SHIFT OVERRIDE: Strong bearish signal ({ma_shift_confidence:.1f}% confidence)")
            else:
                # Normal regime determination
                if bull_score > bear_score and bull_score > neutral_score:
                    primary_regime = 'BULLISH'
                    regime_confidence = bull_score
                elif bear_score > bull_score and bear_score > neutral_score:
                    primary_regime = 'BEARISH'
                    regime_confidence = bear_score
                else:
                    primary_regime = 'NEUTRAL'
                    regime_confidence = neutral_score
        else:
            # Normal regime determination when VWAP confidence is not extreme
            if bull_score > bear_score and bull_score > neutral_score:
                primary_regime = 'BULLISH'
                regime_confidence = bull_score
            elif bear_score > bull_score and bear_score > neutral_score:
                primary_regime = 'BEARISH'
                regime_confidence = bear_score
            else:
                primary_regime = 'NEUTRAL'
                regime_confidence = neutral_score
        
        # REAL FIX: GEX suppresses confidence in BOTH directions equally
        gex_confidence_multiplier = gex_analysis['confidence_multiplier']
        # High GEX suppresses ALL moves, not just bullish ones
        if gex_analysis['direction_reliability'] == 'LOW':
            # In high suppression environments, reduce confidence regardless of direction
            gex_adjusted_confidence = regime_confidence * max(0.80, gex_confidence_multiplier)
        else:
            # Normal GEX environment - minimal impact
            gex_adjusted_confidence = regime_confidence * max(0.95, gex_confidence_multiplier)
        
        # Log GEX impact
        self.logger.info(f"⚡ GEX IMPACT ON DIRECTION DETECTION:")
        self.logger.info(f"   Direction Reliability: {gex_analysis['direction_reliability']}")
        self.logger.info(f"   Original Confidence: {regime_confidence:.1f}%")
        self.logger.info(f"   GEX Multiplier: {gex_confidence_multiplier:.2f}x")
        self.logger.info(f"   GEX-Adjusted Confidence: {gex_adjusted_confidence:.1f}%")
        
        # Determine volatility environment
        vix_level = internals_analysis['vix_term_structure']['vix_level']
        if vix_level > self.vix_thresholds['high_vol']:
            volatility_environment = 'HIGH'
        elif vix_level < self.vix_thresholds['low_vol']:
            volatility_environment = 'LOW'
        else:
            volatility_environment = 'MEDIUM'
        
        # Strategy recommendations based on intelligence
        optimal_strategies = self._recommend_optimal_strategies(
            primary_regime, regime_confidence, volatility_environment
        )
        
        avoid_strategies = self._identify_strategies_to_avoid(
            primary_regime, regime_confidence, volatility_environment
        )
        
        # Key factors
        key_factors = []
        key_factors.append(f"VIX Term Structure: {internals_analysis['vix_term_structure']['term_structure_interpretation']}")
        key_factors.append(f"VWAP Deviation: {technical_analysis['vwap_analysis']['deviation_interpretation']}")
        key_factors.append(f"P/C Ratio: {internals_analysis['put_call_analysis']['interpretation']}")
        key_factors.append(f"Options Volume: {flow_analysis['volume_analysis']['volume_interpretation']}")
        
        # Warnings
        warnings = []
        if volatility_environment == 'HIGH':
            warnings.append("HIGH VOLATILITY: Consider reduced position sizes")
        if regime_confidence < 60:
            warnings.append("LOW CONFIDENCE: Market regime unclear")
        
        return MarketIntelligence(
            bull_score=bull_score,
            bear_score=bear_score,
            neutral_score=neutral_score,
            technical_score=technical_analysis['bull_score'] + technical_analysis['bear_score'],
            internals_score=internals_analysis['bull_score'] + internals_analysis['bear_score'],
            flow_score=flow_analysis['bull_score'] + flow_analysis['bear_score'],
            ml_score=ml_analysis['bull_score'] + ml_analysis['bear_score'],
            vix_term_structure=internals_analysis['vix_term_structure'],
            vwap_analysis=technical_analysis['vwap_analysis'],
            rsi_analysis=technical_analysis['rsi_analysis'],
            put_call_analysis=internals_analysis['put_call_analysis'],
            ma_shift_intelligence=ma_shift_analysis.get('ma_shift_intelligence', {}),  # NEW: MA Shift intelligence
            primary_regime=primary_regime,
            regime_confidence=gex_adjusted_confidence,  # Use GEX-adjusted confidence
            volatility_environment=volatility_environment,
            optimal_strategies=optimal_strategies,
            avoid_strategies=avoid_strategies,
            key_factors=key_factors,
            warnings=warnings
        )
    
    def _recommend_optimal_strategies(
        self, 
        regime: str, 
        confidence: float, 
        volatility: str
    ) -> List[str]:
        """Recommend optimal strategies based on intelligence"""
        
        strategies = []
        
        if regime == 'BULLISH':
            if volatility == 'LOW' and confidence > 70:
                strategies.extend(['BULL_PUT_SPREAD', 'BUY_CALL'])
            elif volatility == 'HIGH':
                strategies.extend(['BUY_CALL', 'BULL_CALL_SPREAD'])
            else:
                strategies.extend(['BULL_PUT_SPREAD', 'BUY_CALL'])
        
        elif regime == 'BEARISH':
            if volatility == 'LOW' and confidence > 70:
                strategies.extend(['BEAR_CALL_SPREAD', 'BUY_PUT'])
            elif volatility == 'HIGH':
                strategies.extend(['BUY_PUT', 'BEAR_PUT_SPREAD'])
            else:
                strategies.extend(['BEAR_CALL_SPREAD', 'BUY_PUT'])
        
        else:  # NEUTRAL
            if volatility == 'LOW':
                strategies.extend(['IRON_CONDOR', 'BULL_PUT_SPREAD', 'BEAR_CALL_SPREAD'])
            else:
                strategies.extend(['BUY_STRADDLE', 'BUY_STRANGLE'])
        
        return strategies
    
    def _identify_strategies_to_avoid(
        self, 
        regime: str, 
        confidence: float, 
        volatility: str
    ) -> List[str]:
        """Identify strategies to avoid"""
        
        avoid = []
        
        if volatility == 'HIGH':
            avoid.extend(['IRON_CONDOR', 'SHORT_STRADDLE'])
        
        if confidence < 50:
            avoid.extend(['BUY_CALL', 'BUY_PUT'])  # Avoid directional bets
        
        if regime == 'BULLISH' and confidence > 70:
            avoid.extend(['BUY_PUT', 'BEAR_CALL_SPREAD', 'BEAR_PUT_SPREAD'])
        
        if regime == 'BEARISH' and confidence > 70:
            avoid.extend(['BUY_CALL', 'BULL_PUT_SPREAD', 'BULL_CALL_SPREAD'])
        
        return avoid
    
    def _estimate_current_price(self, options_data: pd.DataFrame) -> float:
        """Estimate current underlying price from options data"""
        if options_data.empty:
            return 640.0  # Default SPY price
        
        # Use the same logic as other components for consistency
        if 'strike' in options_data.columns and 'moneyness' in options_data.columns:
            # Find ATM options (moneyness closest to 0)
            atm_options = options_data[abs(options_data['moneyness']) < 0.02]  # Within 2%
            
            if not atm_options.empty:
                # Use the strike of the most ATM option
                closest_atm = atm_options.loc[abs(atm_options['moneyness']).idxmin()]
                estimated_price = closest_atm['strike'] / (1 + closest_atm['moneyness'])
                return float(estimated_price)
        
        # Fallback: use median strike as approximation
        if 'strike' in options_data.columns:
            strikes = options_data['strike'].values
            return float(np.median(strikes))
        
        # Last resort - return default
        return 640.0
    
    def _analyze_trend_context(
        self, 
        current_price: float, 
        historical_prices: Optional[pd.DataFrame],
        options_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        CRITICAL: Analyze trend context - the foundation for all other indicators
        This fixes the systematic bearish bias by providing market direction context
        """
        
        analysis = {
            'trend_direction': 'SIDEWAYS',
            'trend_strength': 'WEAK',
            'trend_confidence': 50.0,
            'bull_contribution': 50.0,
            'bear_contribution': 50.0,
            'sma_deviation': 0.0
        }
        
        # Method 1: Use historical prices if available
        if historical_prices is not None and not historical_prices.empty and len(historical_prices) >= 20:
            try:
                if 'close' in historical_prices.columns:
                    prices = historical_prices['close'].values
                    sma_20 = np.mean(prices[-20:])  # 20-period SMA
                    sma_deviation = (current_price - sma_20) / sma_20
                    analysis['sma_deviation'] = sma_deviation
                    
                    # Trend determination based on SMA deviation
                    if sma_deviation > 0.002:  # 0.2% above SMA = UPTREND
                        analysis['trend_direction'] = 'UPTREND'
                        analysis['trend_strength'] = 'STRONG' if sma_deviation > 0.005 else 'MODERATE'
                        analysis['bull_contribution'] = min(85.0, 50 + (sma_deviation * 5000))  # Scale to 0-85
                        analysis['bear_contribution'] = max(15.0, 50 - (sma_deviation * 5000))
                        analysis['trend_confidence'] = min(90.0, 60 + abs(sma_deviation) * 3000)
                        
                    elif sma_deviation < -0.002:  # 0.2% below SMA = DOWNTREND
                        analysis['trend_direction'] = 'DOWNTREND'
                        analysis['trend_strength'] = 'STRONG' if sma_deviation < -0.005 else 'MODERATE'
                        analysis['bear_contribution'] = min(85.0, 50 + abs(sma_deviation) * 5000)
                        analysis['bull_contribution'] = max(15.0, 50 - abs(sma_deviation) * 5000)
                        analysis['trend_confidence'] = min(90.0, 60 + abs(sma_deviation) * 3000)
                        
                    else:  # Within 0.2% of SMA = SIDEWAYS
                        analysis['trend_direction'] = 'SIDEWAYS'
                        analysis['trend_strength'] = 'WEAK'
                        analysis['bull_contribution'] = 50.0
                        analysis['bear_contribution'] = 50.0
                        analysis['trend_confidence'] = 40.0
                        
            except Exception as e:
                self.logger.warning(f"Error in historical trend analysis: {e}")
        
        # Method 2: Fallback using options volume-weighted price momentum
        if analysis['trend_direction'] == 'SIDEWAYS':
            try:
                if 'volume' in options_data.columns and 'strike' in options_data.columns:
                    # Calculate volume-weighted average strike
                    total_volume = options_data['volume'].sum()
                    if total_volume > 0:
                        vw_strike = (options_data['strike'] * options_data['volume']).sum() / total_volume
                        strike_deviation = (current_price - vw_strike) / vw_strike
                        
                        if strike_deviation > 0.003:  # 0.3% above volume-weighted strikes
                            analysis['trend_direction'] = 'UPTREND'
                            analysis['trend_strength'] = 'MODERATE'
                            analysis['bull_contribution'] = 70.0
                            analysis['bear_contribution'] = 30.0
                            analysis['trend_confidence'] = 65.0
                            
                        elif strike_deviation < -0.003:  # 0.3% below volume-weighted strikes
                            analysis['trend_direction'] = 'DOWNTREND'
                            analysis['trend_strength'] = 'MODERATE'
                            analysis['bear_contribution'] = 70.0
                            analysis['bull_contribution'] = 30.0
                            analysis['trend_confidence'] = 65.0
                            
            except Exception as e:
                self.logger.warning(f"Error in options-based trend analysis: {e}")
        
        return analysis
    
    def _analyze_context_aware_rsi(self, rsi_score: float, trend_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        REAL FIX: Context-aware RSI interpretation based on trend direction
        In uptrends, RSI >70 is bullish continuation, not bearish reversal
        """
        
        trend_direction = trend_analysis['trend_direction']
        
        analysis = {
            'rsi_value': rsi_score,
            'trend_context': trend_direction,
            'interpretation': 'NEUTRAL',
            'bull_contribution': 50.0,
            'bear_contribution': 50.0
        }
        
        if trend_direction == 'UPTREND':
            # In uptrends, RSI stays "overbought" - this is BULLISH continuation
            if rsi_score > 80:  # Extreme overbought in uptrend
                analysis['interpretation'] = 'BEARISH_REVERSAL'
                analysis['bull_contribution'] = 20.0
                analysis['bear_contribution'] = 80.0
            elif rsi_score > 60:  # Strong but not extreme - BULLISH continuation
                analysis['interpretation'] = 'BULLISH_CONTINUATION'
                analysis['bull_contribution'] = 75.0
                analysis['bear_contribution'] = 25.0
            elif rsi_score > 40:  # Normal in uptrend
                analysis['interpretation'] = 'BULLISH_NORMAL'
                analysis['bull_contribution'] = 65.0
                analysis['bear_contribution'] = 35.0
            else:  # RSI <40 in uptrend = potential reversal
                analysis['interpretation'] = 'BEARISH_DIVERGENCE'
                analysis['bull_contribution'] = 30.0
                analysis['bear_contribution'] = 70.0
                
        elif trend_direction == 'DOWNTREND':
            # In downtrends, RSI stays "oversold" - this is BEARISH continuation
            if rsi_score < 20:  # Extreme oversold in downtrend
                analysis['interpretation'] = 'BULLISH_REVERSAL'
                analysis['bull_contribution'] = 80.0
                analysis['bear_contribution'] = 20.0
            elif rsi_score < 40:  # Strong but not extreme - BEARISH continuation
                analysis['interpretation'] = 'BEARISH_CONTINUATION'
                analysis['bull_contribution'] = 25.0
                analysis['bear_contribution'] = 75.0
            elif rsi_score < 60:  # Normal in downtrend
                analysis['interpretation'] = 'BEARISH_NORMAL'
                analysis['bull_contribution'] = 35.0
                analysis['bear_contribution'] = 65.0
            else:  # RSI >60 in downtrend = potential reversal
                analysis['interpretation'] = 'BULLISH_DIVERGENCE'
                analysis['bull_contribution'] = 70.0
                analysis['bear_contribution'] = 30.0
                
        else:  # SIDEWAYS - use traditional RSI interpretation
            if rsi_score > 70:
                analysis['interpretation'] = 'OVERBOUGHT'
                analysis['bull_contribution'] = 30.0
                analysis['bear_contribution'] = 70.0
            elif rsi_score < 30:
                analysis['interpretation'] = 'OVERSOLD'
                analysis['bull_contribution'] = 70.0
                analysis['bear_contribution'] = 30.0
            else:
                analysis['interpretation'] = 'NEUTRAL'
                analysis['bull_contribution'] = 50.0
                analysis['bear_contribution'] = 50.0
        
        return analysis
    
    def _analyze_context_aware_put_call_ratio(self, options_data: pd.DataFrame, market_regime: str) -> Dict[str, Any]:
        """
        REAL FIX: Context-aware P/C ratio interpretation based on market regime
        In up markets, P/C 0.8-1.2 is normal hedging, not bearish sentiment
        """
        
        analysis = {
            'put_call_ratio': 1.0,
            'market_context': market_regime,
            'interpretation': 'NEUTRAL',
            'bull_contribution': 50.0,
            'bear_contribution': 50.0
        }
        
        if options_data.empty:
            return analysis
        
        puts = options_data[options_data['option_type'] == 'put']
        calls = options_data[options_data['option_type'] == 'call']
        
        put_volume = puts['volume'].sum() if 'volume' in puts.columns and not puts.empty else 0
        call_volume = calls['volume'].sum() if 'volume' in calls.columns and not calls.empty else 1
        
        pc_ratio = put_volume / max(call_volume, 1)
        analysis['put_call_ratio'] = pc_ratio
        
        if market_regime == 'BULLISH':
            # In bull markets, higher P/C is normal hedging, not panic
            if pc_ratio > 1.5:  # Very heavy put activity = potential reversal
                analysis['interpretation'] = 'BEARISH_REVERSAL'
                analysis['bear_contribution'] = 75.0
                analysis['bull_contribution'] = 25.0
            elif pc_ratio > 1.2:  # Heavy hedging = still bullish but cautious
                analysis['interpretation'] = 'BULLISH_HEDGED'
                analysis['bull_contribution'] = 60.0
                analysis['bear_contribution'] = 40.0
            elif pc_ratio > 0.8:  # Normal bull market range
                analysis['interpretation'] = 'BULLISH_NORMAL'
                analysis['bull_contribution'] = 70.0
                analysis['bear_contribution'] = 30.0
            else:  # P/C < 0.8 = very bullish (low hedging)
                analysis['interpretation'] = 'VERY_BULLISH'
                analysis['bull_contribution'] = 80.0
                analysis['bear_contribution'] = 20.0
                
        elif market_regime == 'BEARISH':
            # In bear markets, lower P/C is unusual (not enough hedging)
            if pc_ratio < 0.8:  # Low put activity in bear market = potential reversal
                analysis['interpretation'] = 'BULLISH_REVERSAL'
                analysis['bull_contribution'] = 75.0
                analysis['bear_contribution'] = 25.0
            elif pc_ratio < 1.2:  # Not enough hedging = still bearish but vulnerable
                analysis['interpretation'] = 'BEARISH_VULNERABLE'
                analysis['bear_contribution'] = 60.0
                analysis['bull_contribution'] = 40.0
            elif pc_ratio < 1.8:  # Normal bear market range
                analysis['interpretation'] = 'BEARISH_NORMAL'
                analysis['bear_contribution'] = 70.0
                analysis['bull_contribution'] = 30.0
            else:  # P/C > 1.8 = very bearish (heavy hedging/panic)
                analysis['interpretation'] = 'VERY_BEARISH'
                analysis['bear_contribution'] = 80.0
                analysis['bull_contribution'] = 20.0
                
        else:  # NEUTRAL market - use traditional interpretation
            if pc_ratio > 1.3:
                analysis['interpretation'] = 'BEARISH'
                analysis['bear_contribution'] = 70.0
                analysis['bull_contribution'] = 30.0
            elif pc_ratio > 1.1:
                analysis['interpretation'] = 'WEAK_BEARISH'
                analysis['bear_contribution'] = 60.0
                analysis['bull_contribution'] = 40.0
            elif pc_ratio < 0.7:
                analysis['interpretation'] = 'BULLISH'
                analysis['bull_contribution'] = 70.0
                analysis['bear_contribution'] = 30.0
            elif pc_ratio < 0.9:
                analysis['interpretation'] = 'WEAK_BULLISH'
                analysis['bull_contribution'] = 60.0
                analysis['bear_contribution'] = 40.0
            else:
                analysis['interpretation'] = 'NEUTRAL'
                analysis['bull_contribution'] = 50.0
                analysis['bear_contribution'] = 50.0
        
        return analysis

def main():
    """Test the Market Intelligence Engine"""
    
    print("🧠 TESTING MARKET INTELLIGENCE ENGINE")
    print("=" * 70)
    
    # Initialize engine
    engine = MarketIntelligenceEngine()
    
    # Create sample options data
    sample_data = pd.DataFrame({
        'strike': [630, 635, 640, 645, 650, 625, 640, 650, 655, 660],
        'option_type': ['put', 'put', 'call', 'call', 'call', 'put', 'call', 'call', 'call', 'call'],
        'volume': [150, 200, 300, 180, 120, 100, 250, 160, 90, 70],
        'transactions': [50, 80, 120, 70, 40, 30, 100, 60, 30, 25],
        'moneyness': [-0.015, -0.008, 0.002, 0.008, 0.015, -0.023, 0.002, 0.015, 0.023, 0.031]
    })
    
    # Test intelligence analysis
    print(f"\n🧠 RUNNING MARKET INTELLIGENCE ANALYSIS:")
    intelligence = engine.analyze_market_intelligence(sample_data)
    
    print(f"\n📊 INTELLIGENCE SUMMARY:")
    print(f"   Primary Regime: {intelligence.primary_regime} ({intelligence.regime_confidence:.1f}%)")
    print(f"   Bull Score: {intelligence.bull_score:.1f}")
    print(f"   Bear Score: {intelligence.bear_score:.1f}")
    print(f"   Neutral Score: {intelligence.neutral_score:.1f}")
    print(f"   Volatility Environment: {intelligence.volatility_environment}")
    
    print(f"\n🎯 STRATEGY RECOMMENDATIONS:")
    print(f"   Optimal Strategies: {', '.join(intelligence.optimal_strategies)}")
    print(f"   Avoid Strategies: {', '.join(intelligence.avoid_strategies)}")
    
    print(f"\n🔍 KEY FACTORS:")
    for factor in intelligence.key_factors:
        print(f"   • {factor}")
    
    if intelligence.warnings:
        print(f"\n⚠️  WARNINGS:")
        for warning in intelligence.warnings:
            print(f"   • {warning}")

if __name__ == "__main__":
    main()
