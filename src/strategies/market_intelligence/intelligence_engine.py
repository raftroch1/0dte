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
        # Layer weights for final scoring
        self.layer_weights = {
            'technical': 0.25,
            'internals': 0.35,
            'flow': 0.25,
            'ml': 0.15
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
        
        # Layer 1: Technical Analysis
        technical_analysis = self._analyze_technical_layer(
            options_data, spy_price, historical_prices
        )
        
        # Layer 2: Market Internals
        internals_analysis = self._analyze_internals_layer(
            options_data, vix_data
        )
        
        # Layer 3: Options Flow Analysis
        flow_analysis = self._analyze_flow_layer(options_data)
        
        # Layer 4: ML Integration (placeholder for now)
        ml_analysis = self._analyze_ml_layer(options_data)
        
        # Combine all layers
        intelligence = self._synthesize_intelligence(
            technical_analysis,
            internals_analysis,
            flow_analysis,
            ml_analysis
        )
        
        self.logger.info(f"🎯 INTELLIGENCE SYNTHESIS COMPLETE:")
        self.logger.info(f"   Primary Regime: {intelligence.primary_regime} ({intelligence.regime_confidence:.1f}%)")
        self.logger.info(f"   Bull Score: {intelligence.bull_score:.1f}")
        self.logger.info(f"   Bear Score: {intelligence.bear_score:.1f}")
        self.logger.info(f"   Neutral Score: {intelligence.neutral_score:.1f}")
        
        return intelligence
    
    def _analyze_technical_layer(
        self, 
        options_data: pd.DataFrame,
        spy_price: Optional[float],
        historical_prices: Optional[pd.DataFrame]
    ) -> Dict[str, Any]:
        """Analyze technical indicators layer"""
        
        analysis = {
            'bull_score': 50.0,
            'bear_score': 50.0,
            'neutral_score': 50.0,
            'rsi_analysis': {},
            'vwap_analysis': {},
            'momentum_analysis': {}
        }
        
        # Estimate current price if not provided
        if spy_price is None:
            spy_price = self._estimate_current_price(options_data)
        
        # RSI Analysis (simplified from options data)
        rsi_score = self._calculate_rsi_from_options(options_data)
        analysis['rsi_analysis'] = {
            'rsi_value': rsi_score,
            'interpretation': self._interpret_rsi(rsi_score),
            'bull_contribution': max(0, (rsi_score - 30) / 40 * 100) if rsi_score < 70 else 0,
            'bear_contribution': max(0, (70 - rsi_score) / 40 * 100) if rsi_score > 30 else 0
        }
        
        # VWAP Analysis
        vwap_analysis = self._calculate_vwap_deviation(spy_price, historical_prices, options_data)
        analysis['vwap_analysis'] = vwap_analysis
        
        # Momentum Analysis from options moneyness
        momentum_analysis = self._analyze_options_momentum(options_data)
        analysis['momentum_analysis'] = momentum_analysis
        
        # Combine technical scores
        rsi_weight = 0.4
        vwap_weight = 0.35
        momentum_weight = 0.25
        
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
        vix_data: Optional[pd.DataFrame]
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
        
        # Put/Call Ratio Analysis
        pc_analysis = self._analyze_put_call_ratio(options_data)
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
        """Calculate RSI-like indicator from options data"""
        
        if options_data.empty:
            return 50.0
        
        # Use put/call volume ratio as RSI proxy
        puts = options_data[options_data['option_type'] == 'put']
        calls = options_data[options_data['option_type'] == 'call']
        
        put_volume = puts['volume'].sum() if 'volume' in puts.columns and not puts.empty else 100
        call_volume = calls['volume'].sum() if 'volume' in calls.columns and not calls.empty else 100
        
        # Convert P/C ratio to RSI-like scale (0-100)
        pc_ratio = put_volume / max(call_volume, 1)
        
        # Map P/C ratio to RSI scale
        # P/C ratio of 1.0 = RSI 50 (neutral)
        # P/C ratio of 2.0 = RSI 30 (oversold/bearish)
        # P/C ratio of 0.5 = RSI 70 (overbought/bullish)
        
        if pc_ratio >= 1.0:
            rsi = max(10, 50 - (pc_ratio - 1.0) * 40)
        else:
            rsi = min(90, 50 + (1.0 - pc_ratio) * 40)
        
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
        
        # Analyze moneyness distribution
        avg_moneyness = options_data['moneyness'].mean()
        moneyness_std = options_data['moneyness'].std()
        
        # Strong momentum if options are heavily skewed
        if abs(avg_moneyness) > 0.02:  # 2% average moneyness
            analysis['momentum_strength'] = 'STRONG'
            if avg_moneyness > 0:
                analysis['momentum_direction'] = 'BULLISH'
                analysis['bull_contribution'] = 80.0
                analysis['bear_contribution'] = 20.0
            else:
                analysis['momentum_direction'] = 'BEARISH'
                analysis['bull_contribution'] = 20.0
                analysis['bear_contribution'] = 80.0
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
        
        put_count = len(puts)
        call_count = max(len(calls), 1)
        
        pc_ratio = put_count / call_count
        analysis['put_call_ratio'] = pc_ratio
        
        # Interpret P/C ratio
        if pc_ratio > 1.5:  # Heavy put activity = bearish
            analysis['interpretation'] = 'BEARISH'
            analysis['bear_contribution'] = 80.0
            analysis['bull_contribution'] = 20.0
        elif pc_ratio > 1.2:
            analysis['interpretation'] = 'WEAK_BEARISH'
            analysis['bear_contribution'] = 65.0
            analysis['bull_contribution'] = 35.0
        elif pc_ratio < 0.7:  # Heavy call activity = bullish
            analysis['interpretation'] = 'BULLISH'
            analysis['bull_contribution'] = 80.0
            analysis['bear_contribution'] = 20.0
        elif pc_ratio < 0.9:
            analysis['interpretation'] = 'WEAK_BULLISH'
            analysis['bull_contribution'] = 65.0
            analysis['bear_contribution'] = 35.0
        else:
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
    
    def _synthesize_intelligence(
        self,
        technical_analysis: Dict[str, Any],
        internals_analysis: Dict[str, Any],
        flow_analysis: Dict[str, Any],
        ml_analysis: Dict[str, Any]
    ) -> MarketIntelligence:
        """Synthesize all layers into final intelligence"""
        
        # Weighted combination of layer scores
        bull_score = (
            technical_analysis['bull_score'] * self.layer_weights['technical'] +
            internals_analysis['bull_score'] * self.layer_weights['internals'] +
            flow_analysis['bull_score'] * self.layer_weights['flow'] +
            ml_analysis['bull_score'] * self.layer_weights['ml']
        )
        
        bear_score = (
            technical_analysis['bear_score'] * self.layer_weights['technical'] +
            internals_analysis['bear_score'] * self.layer_weights['internals'] +
            flow_analysis['bear_score'] * self.layer_weights['flow'] +
            ml_analysis['bear_score'] * self.layer_weights['ml']
        )
        
        neutral_score = 100 - bull_score - bear_score
        
        # Determine primary regime
        if bull_score > bear_score and bull_score > neutral_score:
            primary_regime = 'BULLISH'
            regime_confidence = bull_score
        elif bear_score > bull_score and bear_score > neutral_score:
            primary_regime = 'BEARISH'
            regime_confidence = bear_score
        else:
            primary_regime = 'NEUTRAL'
            regime_confidence = neutral_score
        
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
            primary_regime=primary_regime,
            regime_confidence=regime_confidence,
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
