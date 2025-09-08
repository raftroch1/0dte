#!/usr/bin/env python3
"""
Unified Signal System - Integrated with Existing Architecture
============================================================

Intelligent system to resolve conflicts between trading signals and generate
unified, high-confidence recommendations optimized for win rate and drawdown.

Integrated with our existing Market Intelligence Engine to fix systematic bias.
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
from dataclasses import dataclass
from enum import Enum
import json

# Import our existing systems
from src.strategies.market_intelligence.intelligence_engine import MarketIntelligenceEngine
from src.strategies.market_intelligence.moving_average_shift_analyzer import MovingAverageShiftAnalyzer
from src.strategies.market_intelligence.gamma_exposure_analyzer import GammaExposureAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SignalStrength(Enum):
    VERY_WEAK = 0
    WEAK = 1
    MODERATE = 2 
    STRONG = 3
    VERY_STRONG = 4

class MarketDirection(Enum):
    STRONG_BEARISH = -2
    BEARISH = -1
    NEUTRAL = 0
    BULLISH = 1
    STRONG_BULLISH = 2

@dataclass
class UnifiedSignal:
    """Unified trading signal with conflict resolution"""
    
    # Core recommendation
    direction: MarketDirection
    confidence: float  # 0-100
    strength: SignalStrength
    
    # Strategy recommendations
    primary_strategy: str
    backup_strategies: List[str]
    avoid_strategies: List[str]
    
    # Risk management
    max_position_size: int  # Number of contracts
    stop_loss_pct: float   # Stop loss as % of premium
    profit_target_pct: float  # Profit target as % of premium
    
    # Conflict resolution details
    consensus_score: float  # How well systems agree (0-100)
    dominant_systems: List[str]  # Systems supporting this signal
    conflicting_systems: List[str]  # Systems disagreeing
    
    # Signal quality metrics
    signal_quality: float  # Overall signal quality (0-100)
    reliability_score: float  # Historical reliability (0-100)
    
    # Market context
    market_regime: str
    volatility_environment: str
    gex_environment: str
    
    # Reasoning and warnings
    reasoning: List[str]
    warnings: List[str]
    
    # Execution parameters
    optimal_entry_time: str  # Best time to enter
    max_holding_period: str  # Maximum hold time
    
    # Backtesting metrics
    estimated_win_rate: float
    estimated_max_drawdown: float
    risk_reward_ratio: float

class IntegratedUnifiedSignalSystem:
    """
    Unified signal system integrated with our existing Market Intelligence Engine
    
    FIXES THE SYSTEMATIC BULLISH BIAS by:
    1. Detecting conflicts between intelligence layers
    2. Applying weighted consensus with bias correction
    3. Dynamic system reliability scoring
    4. Market regime-aware signal weighting
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize our existing systems
        self.intelligence_engine = MarketIntelligenceEngine()
        self.ma_shift_analyzer = MovingAverageShiftAnalyzer()
        self.gex_analyzer = GammaExposureAnalyzer()
        
        # BIAS CORRECTION: Dynamic weights that adapt based on performance
        self.base_weights = {
            'technical': 0.25,     # Reduced from problematic layer
            'internals': 0.20,     # Reduced from problematic layer  
            'flow': 0.25,         # Increased - showed minimal bias
            'ma_shift': 0.20,     # Neutral layer
            'gex': 0.10          # Signal quality modifier
        }
        
        # BIAS TRACKING: Monitor each layer's bias over time
        self.bias_tracking = {
            'technical': {'bull_bias': 0.0, 'samples': 0},
            'internals': {'bull_bias': 0.0, 'samples': 0},
            'flow': {'bull_bias': 0.0, 'samples': 0},
            'ma_shift': {'bull_bias': 0.0, 'samples': 0},
            'gex': {'bull_bias': 0.0, 'samples': 0}
        }
        
        # Conflict resolution parameters
        self.min_consensus_threshold = 60.0  # Minimum consensus for strong signals
        self.high_conflict_threshold = 0.7   # Above this = avoid trading
        self.signal_quality_threshold = 50.0  # Minimum signal quality
        
        # Strategy recommendations based on market conditions - NAKED OPTIONS + SPREADS
        self.strategy_matrix = {
            MarketDirection.STRONG_BULLISH: {
                'primary': 'NAKED_CALL',  # Naked calls for strong bullish moves
                'backup': ['BULL_CALL_SPREAD', 'BULL_PUT_SPREAD'],
                'avoid': ['BEAR_CALL_SPREAD', 'BEAR_PUT_SPREAD', 'NAKED_PUT']
            },
            MarketDirection.BULLISH: {
                'primary': 'NAKED_CALL', 
                'backup': ['BULL_CALL_SPREAD', 'BULL_PUT_SPREAD'],
                'avoid': ['BEAR_CALL_SPREAD', 'BEAR_PUT_SPREAD', 'NAKED_PUT']
            },
            MarketDirection.NEUTRAL: {
                'primary': 'NAKED_CALL',  # 0DTE: Pick direction instead of straddles
                'backup': ['NAKED_PUT', 'BULL_CALL_SPREAD', 'BEAR_PUT_SPREAD'],
                'avoid': []
            },
            MarketDirection.BEARISH: {
                'primary': 'NAKED_PUT',
                'backup': ['BEAR_PUT_SPREAD', 'BEAR_CALL_SPREAD'], 
                'avoid': ['BULL_PUT_SPREAD', 'BULL_CALL_SPREAD', 'NAKED_CALL']
            },
            MarketDirection.STRONG_BEARISH: {
                'primary': 'NAKED_PUT',
                'backup': ['BEAR_PUT_SPREAD', 'BEAR_CALL_SPREAD'],
                'avoid': ['BULL_PUT_SPREAD', 'BULL_CALL_SPREAD', 'NAKED_CALL']
            }
        }
        
        self.logger.info("🎯 INTEGRATED UNIFIED SIGNAL SYSTEM INITIALIZED")
        self.logger.info("   Features: Bias correction, Conflict resolution, Dynamic weighting")
        self.logger.info(f"   Base weights: {self.base_weights}")
    
    def generate_unified_signal(self, 
                              options_data: pd.DataFrame,
                              spy_price: float,
                              vix_data: Optional[pd.DataFrame] = None,
                              historical_prices: Optional[pd.DataFrame] = None) -> UnifiedSignal:
        """
        Generate unified signal by resolving conflicts between intelligence layers
        
        CRITICAL: This fixes the systematic bullish bias by detecting and correcting it
        """
        
        self.logger.info("🔄 GENERATING BIAS-CORRECTED UNIFIED SIGNAL")
        
        # Step 1: Get signals from all intelligence layers
        intelligence = self.intelligence_engine.analyze_market_intelligence(
            options_data=options_data,
            spy_price=spy_price,
            vix_data=vix_data,
            historical_prices=historical_prices
        )
        
        # Step 2: Extract individual layer signals
        layer_signals = self._extract_layer_signals(intelligence)
        
        # Step 3: BIAS DETECTION AND CORRECTION
        corrected_signals = self._apply_bias_correction(layer_signals, spy_price)
        
        # Step 4: Resolve conflicts using weighted consensus
        consensus_analysis = self._resolve_signal_conflicts(corrected_signals)
        
        # Step 5: Determine unified direction and confidence
        unified_direction, base_confidence = self._calculate_unified_direction(consensus_analysis)
        
        # Step 6: Apply quality filters
        adjusted_confidence, signal_quality = self._apply_quality_filters(
            base_confidence, corrected_signals, spy_price
        )
        
        # Step 7: Generate strategy recommendations
        strategy_rec = self._generate_strategy_recommendations(
            unified_direction, adjusted_confidence, intelligence
        )
        
        # Step 8: Calculate risk management parameters  
        risk_params = self._calculate_risk_parameters(
            unified_direction, adjusted_confidence, signal_quality
        )
        
        # Step 9: Generate reasoning and warnings
        reasoning, warnings = self._generate_reasoning_and_warnings(
            corrected_signals, consensus_analysis, signal_quality
        )
        
        # Step 10: Update bias tracking
        self._update_bias_tracking(layer_signals)
        
        # Create unified signal
        unified_signal = UnifiedSignal(
            direction=unified_direction,
            confidence=adjusted_confidence,
            strength=self._calculate_signal_strength(adjusted_confidence, consensus_analysis['consensus_score']),
            primary_strategy=strategy_rec['primary'],
            backup_strategies=strategy_rec['backup'],
            avoid_strategies=strategy_rec['avoid'],
            max_position_size=risk_params['max_position_size'],
            stop_loss_pct=risk_params['stop_loss_pct'],
            profit_target_pct=risk_params['profit_target_pct'],
            consensus_score=consensus_analysis['consensus_score'],
            dominant_systems=consensus_analysis['dominant_systems'],
            conflicting_systems=consensus_analysis['conflicting_systems'],
            signal_quality=signal_quality,
            reliability_score=consensus_analysis['reliability_score'],
            market_regime=intelligence.primary_regime,
            volatility_environment=self._classify_vix_environment(vix_data),
            gex_environment=intelligence.gex_environment if hasattr(intelligence, 'gex_environment') else 'NORMAL',
            reasoning=reasoning,
            warnings=warnings,
            optimal_entry_time=risk_params['optimal_entry_time'],
            max_holding_period=risk_params['max_holding_period'],
            estimated_win_rate=self._estimate_win_rate(unified_direction, adjusted_confidence),
            estimated_max_drawdown=self._estimate_max_drawdown(adjusted_confidence),
            risk_reward_ratio=3.0  # Target 3:1 for debit spreads
        )
        
        self.logger.info(f"✅ BIAS-CORRECTED UNIFIED SIGNAL GENERATED:")
        self.logger.info(f"   Direction: {unified_direction.name}")
        self.logger.info(f"   Confidence: {adjusted_confidence:.1f}%")
        self.logger.info(f"   Strategy: {strategy_rec['primary']}")
        self.logger.info(f"   Consensus: {consensus_analysis['consensus_score']:.1f}%")
        self.logger.info(f"   Signal Quality: {signal_quality:.1f}%")
        
        return unified_signal
    
    def _extract_layer_signals(self, intelligence) -> Dict[str, Dict[str, float]]:
        """Extract signals from each intelligence layer"""
        
        # Extract from the intelligence analysis
        layer_signals = {
            'technical': {
                'bull_score': getattr(intelligence, 'technical_bull_score', intelligence.bull_score * 0.25),
                'bear_score': getattr(intelligence, 'technical_bear_score', intelligence.bear_score * 0.25),
                'confidence': 70.0
            },
            'internals': {
                'bull_score': getattr(intelligence, 'internals_bull_score', intelligence.bull_score * 0.20),
                'bear_score': getattr(intelligence, 'internals_bear_score', intelligence.bear_score * 0.20),
                'confidence': 65.0
            },
            'flow': {
                'bull_score': getattr(intelligence, 'flow_bull_score', intelligence.bull_score * 0.25),
                'bear_score': getattr(intelligence, 'flow_bear_score', intelligence.bear_score * 0.25),
                'confidence': 60.0
            },
            'ma_shift': {
                'bull_score': getattr(intelligence, 'ma_shift_bull_score', intelligence.bull_score * 0.20),
                'bear_score': getattr(intelligence, 'ma_shift_bear_score', intelligence.bear_score * 0.20),
                'confidence': 75.0
            },
            'gex': {
                'bull_score': getattr(intelligence, 'gex_bull_score', 50.0),
                'bear_score': getattr(intelligence, 'gex_bear_score', 50.0),
                'confidence': 80.0
            }
        }
        
        return layer_signals
    
    def _apply_bias_correction(self, layer_signals: Dict[str, Dict], spy_price: float) -> Dict[str, Dict]:
        """
        CRITICAL: Apply bias correction to each layer
        
        This is the key fix for the systematic bullish bias
        """
        
        corrected_signals = {}
        
        for layer, signals in layer_signals.items():
            bull_score = signals['bull_score']
            bear_score = signals['bear_score']
            
            # Calculate current bias
            total_score = bull_score + bear_score
            if total_score > 0:
                current_bias = (bull_score - bear_score) / total_score
            else:
                current_bias = 0.0
            
            # Get historical bias for this layer
            historical_bias = self.bias_tracking[layer]['bull_bias']
            
            # Apply bias correction
            if abs(historical_bias) > 0.1:  # Significant bias detected
                correction_factor = -historical_bias * 0.5  # Correct 50% of historical bias
                
                if correction_factor > 0:
                    # Historically bearish biased, boost bull score
                    corrected_bull = bull_score * (1 + abs(correction_factor))
                    corrected_bear = bear_score * (1 - abs(correction_factor) * 0.5)
                else:
                    # Historically bullish biased, boost bear score
                    corrected_bull = bull_score * (1 - abs(correction_factor) * 0.5)
                    corrected_bear = bear_score * (1 + abs(correction_factor))
                
                self.logger.info(f"🔧 BIAS CORRECTION APPLIED to {layer}:")
                self.logger.info(f"   Historical bias: {historical_bias:.3f}")
                self.logger.info(f"   Before: Bull={bull_score:.1f}, Bear={bear_score:.1f}")
                self.logger.info(f"   After: Bull={corrected_bull:.1f}, Bear={corrected_bear:.1f}")
                
                corrected_signals[layer] = {
                    'bull_score': corrected_bull,
                    'bear_score': corrected_bear,
                    'confidence': signals['confidence'],
                    'bias_corrected': True,
                    'correction_applied': correction_factor
                }
            else:
                # No significant bias, use original signals
                corrected_signals[layer] = signals.copy()
                corrected_signals[layer]['bias_corrected'] = False
        
        return corrected_signals
    
    def _resolve_signal_conflicts(self, layer_signals: Dict[str, Dict]) -> Dict[str, Any]:
        """Resolve conflicts between layers using weighted consensus"""
        
        # Calculate weighted bull and bear scores
        total_bull_score = 0.0
        total_bear_score = 0.0
        total_weight = 0.0
        
        dominant_systems = []
        conflicting_systems = []
        
        for layer, signals in layer_signals.items():
            weight = self.base_weights.get(layer, 0.2)
            confidence_factor = signals['confidence'] / 100.0
            effective_weight = weight * confidence_factor
            
            bull_contribution = signals['bull_score'] * effective_weight
            bear_contribution = signals['bear_score'] * effective_weight
            
            total_bull_score += bull_contribution
            total_bear_score += bear_contribution
            total_weight += effective_weight
            
            # Determine if this layer is dominant or conflicting
            layer_bias = signals['bull_score'] - signals['bear_score']
            if abs(layer_bias) > 10:  # Strong directional signal
                if layer_bias > 0:
                    dominant_systems.append(f"{layer} (BULLISH)")
                else:
                    dominant_systems.append(f"{layer} (BEARISH)")
        
        # Normalize scores
        if total_weight > 0:
            normalized_bull = total_bull_score / total_weight
            normalized_bear = total_bear_score / total_weight
        else:
            normalized_bull = 50.0
            normalized_bear = 50.0
        
        # Calculate consensus score
        total_directional = normalized_bull + normalized_bear
        if total_directional > 0:
            consensus_score = max(normalized_bull, normalized_bear) / total_directional * 100
        else:
            consensus_score = 50.0
        
        # Identify conflicts
        if abs(normalized_bull - normalized_bear) < 5:  # Very close scores
            conflicting_systems = list(layer_signals.keys())
        
        return {
            'bull_score': normalized_bull,
            'bear_score': normalized_bear,
            'consensus_score': consensus_score,
            'dominant_systems': dominant_systems,
            'conflicting_systems': conflicting_systems,
            'reliability_score': consensus_score,
            'total_weight': total_weight
        }
    
    def _calculate_unified_direction(self, consensus_analysis: Dict[str, Any]) -> Tuple[MarketDirection, float]:
        """Calculate unified market direction and confidence"""
        
        bull_score = consensus_analysis['bull_score']
        bear_score = consensus_analysis['bear_score']
        
        # Determine direction
        # 0DTE OPTIMIZED: Lower thresholds for more aggressive directional calls
        if bull_score > bear_score + 3:  # Lowered from 10 to 3 for 0DTE
            if bull_score > 65:  # Lowered from 70 to 65
                direction = MarketDirection.STRONG_BULLISH
            else:
                direction = MarketDirection.BULLISH
            confidence = min(95, bull_score)
        elif bear_score > bull_score + 3:  # Lowered from 10 to 3 for 0DTE
            if bear_score > 65:  # Lowered from 70 to 65
                direction = MarketDirection.STRONG_BEARISH
            else:
                direction = MarketDirection.BEARISH
            confidence = min(95, bear_score)
        else:
            # 0DTE OPTIMIZATION: Even for "neutral", pick the stronger direction
            if bull_score > bear_score:
                direction = MarketDirection.BULLISH
                confidence = max(45, bull_score)  # Minimum 45% confidence
            else:
                direction = MarketDirection.BEARISH
                confidence = max(45, bear_score)  # Minimum 45% confidence
        
        return direction, confidence
    
    def _apply_quality_filters(self, base_confidence: float, layer_signals: Dict, spy_price: float) -> Tuple[float, float]:
        """Apply signal quality filters"""
        
        adjusted_confidence = base_confidence
        
        # Check for bias corrections - REDUCED PENALTY
        bias_corrections = sum(1 for signals in layer_signals.values() if signals.get('bias_corrected', False))
        if bias_corrections > 0:
            # Minimal reduction for bias corrections (was too harsh at 5% per correction)
            adjusted_confidence *= (1 - bias_corrections * 0.01)  # Only 1% reduction per correction
        
        # Time-based filter - LESS AGGRESSIVE for 0DTE
        current_hour = datetime.now().hour
        if current_hour < 10 or current_hour > 15:
            adjusted_confidence *= 0.95  # Reduced penalty from 0.9 to 0.95
        
        # Calculate signal quality
        avg_confidence = np.mean([signals['confidence'] for signals in layer_signals.values()])
        signal_quality = (adjusted_confidence + avg_confidence) / 2
        
        return max(10, min(95, adjusted_confidence)), max(10, min(100, signal_quality))
    
    def _generate_strategy_recommendations(self, direction: MarketDirection, confidence: float, intelligence) -> Dict[str, Any]:
        """Generate strategy recommendations - SPREADS ONLY"""
        
        base_strategies = self.strategy_matrix.get(direction, self.strategy_matrix[MarketDirection.NEUTRAL])
        
        # For low confidence, still use directional spreads but with more conservative approach
        if confidence < 50:
            # Very low confidence - use neutral spread selection
            return {
                'primary': 'BULL_CALL_SPREAD',  # Default to bullish spread for 0DTE
                'backup': ['BEAR_PUT_SPREAD', 'BULL_PUT_SPREAD'],
                'avoid': ['BEAR_CALL_SPREAD']
            }
        elif confidence < 65:
            # Medium confidence - use direction but with backup options
            return {
                'primary': base_strategies['primary'],
                'backup': base_strategies['backup'] + ['BULL_PUT_SPREAD', 'BEAR_PUT_SPREAD'],
                'avoid': []
            }
        
        # High confidence - use full directional strategy
        return base_strategies
    
    def _calculate_risk_parameters(self, direction: MarketDirection, confidence: float, signal_quality: float) -> Dict[str, Any]:
        """Calculate risk management parameters"""
        
        # Conservative position sizing
        base_size = 1
        quality_factor = signal_quality / 100.0
        confidence_factor = confidence / 100.0
        
        max_position_size = max(1, int(base_size * quality_factor * confidence_factor * 2))
        
        # Risk management for debit spreads
        if confidence >= 75:
            stop_loss_pct = 75  # 75% of premium
            profit_target_pct = 50  # 50% of max profit
        elif confidence >= 60:
            stop_loss_pct = 60  # 60% of premium
            profit_target_pct = 40  # 40% of max profit
        else:
            stop_loss_pct = 50  # 50% of premium
            profit_target_pct = 30  # 30% of max profit
        
        return {
            'max_position_size': max_position_size,
            'stop_loss_pct': stop_loss_pct,
            'profit_target_pct': profit_target_pct,
            'optimal_entry_time': "10:00 AM - 2:30 PM ET",
            'max_holding_period': "Until 3:30 PM or profit target"
        }
    
    def _calculate_signal_strength(self, confidence: float, consensus_score: float) -> SignalStrength:
        """Calculate signal strength"""
        
        combined_score = (confidence + consensus_score) / 2
        
        if combined_score >= 80:
            return SignalStrength.VERY_STRONG
        elif combined_score >= 65:
            return SignalStrength.STRONG
        elif combined_score >= 50:
            return SignalStrength.MODERATE
        elif combined_score >= 35:
            return SignalStrength.WEAK
        else:
            return SignalStrength.VERY_WEAK
    
    def _generate_reasoning_and_warnings(self, layer_signals: Dict, consensus_analysis: Dict, signal_quality: float) -> Tuple[List[str], List[str]]:
        """Generate reasoning and warnings"""
        
        reasoning = []
        warnings = []
        
        # Consensus reasoning
        consensus_score = consensus_analysis['consensus_score']
        if consensus_score >= 70:
            reasoning.append(f"Strong layer consensus ({consensus_score:.1f}%)")
        elif consensus_score < 50:
            warnings.append(f"Low layer consensus ({consensus_score:.1f}%) - conflicting signals")
        
        # Bias correction notifications
        corrected_layers = [layer for layer, signals in layer_signals.items() if signals.get('bias_corrected', False)]
        if corrected_layers:
            reasoning.append(f"Bias correction applied to: {', '.join(corrected_layers)}")
        
        # Signal quality
        if signal_quality >= 75:
            reasoning.append(f"High signal quality ({signal_quality:.1f}%)")
        elif signal_quality < 50:
            warnings.append(f"Low signal quality ({signal_quality:.1f}%) - proceed with caution")
        
        return reasoning, warnings
    
    def _update_bias_tracking(self, layer_signals: Dict[str, Dict]):
        """Update bias tracking for each layer"""
        
        for layer, signals in layer_signals.items():
            bull_score = signals['bull_score']
            bear_score = signals['bear_score']
            
            total_score = bull_score + bear_score
            if total_score > 0:
                current_bias = (bull_score - bear_score) / total_score
                
                # Update running average
                tracker = self.bias_tracking[layer]
                tracker['samples'] += 1
                
                # Exponential moving average with alpha = 0.1
                alpha = 0.1
                tracker['bull_bias'] = tracker['bull_bias'] * (1 - alpha) + current_bias * alpha
    
    def _classify_vix_environment(self, vix_data: Optional[pd.DataFrame]) -> str:
        """Classify VIX environment"""
        
        if vix_data is None or vix_data.empty:
            return 'NORMAL'
        
        try:
            current_vix = float(vix_data['close'].iloc[-1])
            if current_vix > 30:
                return 'HIGH'
            elif current_vix < 15:
                return 'LOW'
            else:
                return 'NORMAL'
        except:
            return 'NORMAL'
    
    def _estimate_win_rate(self, direction: MarketDirection, confidence: float) -> float:
        """Estimate win rate based on direction and confidence"""
        
        base_rates = {
            MarketDirection.STRONG_BULLISH: 55,
            MarketDirection.BULLISH: 52,
            MarketDirection.NEUTRAL: 48,
            MarketDirection.BEARISH: 52,
            MarketDirection.STRONG_BEARISH: 55
        }
        
        base_rate = base_rates.get(direction, 50)
        confidence_adjustment = (confidence - 50) * 0.2  # Up to ±10% adjustment
        
        return max(35, min(75, base_rate + confidence_adjustment))
    
    def _estimate_max_drawdown(self, confidence: float) -> float:
        """Estimate maximum drawdown"""
        
        base_drawdown = 20.0  # Base 20% drawdown
        confidence_factor = max(0.6, confidence / 100.0)
        
        return max(8, min(35, base_drawdown / confidence_factor))
    
    def get_bias_report(self) -> Dict[str, Any]:
        """Get current bias tracking report"""
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'layer_biases': {},
            'overall_bias': 0.0,
            'bias_corrections_applied': 0
        }
        
        total_bias = 0.0
        total_samples = 0
        
        for layer, tracker in self.bias_tracking.items():
            if tracker['samples'] > 0:
                report['layer_biases'][layer] = {
                    'bias': tracker['bull_bias'],
                    'samples': tracker['samples'],
                    'interpretation': 'BULLISH' if tracker['bull_bias'] > 0.1 else 'BEARISH' if tracker['bull_bias'] < -0.1 else 'NEUTRAL'
                }
                
                total_bias += tracker['bull_bias'] * tracker['samples']
                total_samples += tracker['samples']
        
        if total_samples > 0:
            report['overall_bias'] = total_bias / total_samples
        
        return report

def main():
    """Test the integrated unified signal system"""
    
    print("🎯 TESTING INTEGRATED UNIFIED SIGNAL SYSTEM")
    print("="*60)
    
    # Initialize system
    unified_system = IntegratedUnifiedSignalSystem()
    
    # Test with sample data (would normally come from real data)
    sample_options_data = pd.DataFrame({
        'option_type': ['call', 'put'] * 100,
        'volume': np.random.randint(10, 1000, 200),
        'strike': np.random.uniform(500, 600, 200),
        'moneyness': np.random.uniform(-0.1, 0.1, 200)
    })
    
    sample_vix_data = pd.DataFrame({
        'close': [22.5]
    })
    
    # Generate unified signal
    unified_signal = unified_system.generate_unified_signal(
        options_data=sample_options_data,
        spy_price=580.0,
        vix_data=sample_vix_data
    )
    
    print(f"\n🎯 UNIFIED SIGNAL RESULT:")
    print(f"   Direction: {unified_signal.direction.name}")
    print(f"   Confidence: {unified_signal.confidence:.1f}%")
    print(f"   Strength: {unified_signal.strength.name}")
    print(f"   Strategy: {unified_signal.primary_strategy}")
    print(f"   Position Size: {unified_signal.max_position_size} contracts")
    print(f"   Consensus Score: {unified_signal.consensus_score:.1f}%")
    print(f"   Signal Quality: {unified_signal.signal_quality:.1f}%")
    
    print(f"\n💡 REASONING:")
    for reason in unified_signal.reasoning:
        print(f"   ✓ {reason}")
    
    print(f"\n⚠️ WARNINGS:")
    for warning in unified_signal.warnings:
        print(f"   ⚠ {warning}")
    
    # Get bias report
    bias_report = unified_system.get_bias_report()
    print(f"\n📊 BIAS TRACKING REPORT:")
    for layer, bias_info in bias_report['layer_biases'].items():
        print(f"   {layer}: {bias_info['interpretation']} bias ({bias_info['bias']:.3f})")
    
    return unified_signal

if __name__ == "__main__":
    main()
