#!/usr/bin/env python3
"""
Gamma Exposure (GEX) Analyzer - Smart Direction Enhancement
==========================================================

INTELLIGENT GEX INTEGRATION:
- Uses GEX to ENHANCE signals, not restrict them
- Identifies when direction detection is reliable vs unreliable
- Provides confidence adjustments based on gamma environment
- Avoids the common mistake of using GEX as primary direction filter

This addresses the core issue: GEX often makes direction detection harder,
so we use it to identify WHEN our other signals are most/least reliable.

Location: src/strategies/market_intelligence/ (following .cursorrules structure)
Author: Advanced Options Trading System - GEX Intelligence
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
from datetime import datetime
import logging

@dataclass
class GammaExposureAnalysis:
    """Comprehensive gamma exposure analysis"""
    # Core GEX Metrics
    total_gamma_exposure: float
    call_gamma_exposure: float
    put_gamma_exposure: float
    net_gamma_exposure: float
    
    # GEX Environment
    gex_environment: str  # 'HIGH_SUPPRESSION', 'MODERATE', 'LOW_GAMMA', 'NEGATIVE_GAMMA'
    direction_reliability: str  # 'HIGH', 'MEDIUM', 'LOW', 'UNRELIABLE'
    
    # Key Levels
    major_gamma_strikes: List[float]
    gamma_flip_level: Optional[float]
    resistance_levels: List[float]
    support_levels: List[float]
    
    # Signal Enhancement
    confidence_multiplier: float  # 0.7 to 1.3
    signal_quality_score: float  # 0-100
    
    # Reasoning
    gex_factors: List[str]
    warnings: List[str]

class GammaExposureAnalyzer:
    """
    Smart Gamma Exposure Analyzer for 0DTE Trading
    
    KEY INSIGHT: Instead of using GEX to predict direction,
    use it to identify WHEN direction signals are reliable.
    
    Features:
    1. GEX environment classification
    2. Direction reliability assessment  
    3. Signal confidence enhancement
    4. Gamma level identification
    5. Market microstructure analysis
    """
    
    def __init__(self):
        # GEX environment thresholds (in millions of dollars)
        self.gex_thresholds = {
            'high_suppression': 5000,    # >$5B gamma = high suppression
            'moderate_suppression': 2000, # $2-5B = moderate suppression
            'low_gamma': 500,            # $500M-2B = normal environment
            'negative_gamma': 0          # <$0 = negative gamma (explosive)
        }
        
        # Direction reliability based on GEX environment
        self.reliability_map = {
            'HIGH_SUPPRESSION': 'LOW',      # Hard to detect direction
            'MODERATE': 'MEDIUM',           # Moderate direction detection
            'LOW_GAMMA': 'HIGH',            # Good direction detection
            'NEGATIVE_GAMMA': 'UNRELIABLE'  # Explosive, unpredictable
        }
        
        # Confidence multipliers based on GEX environment
        self.confidence_multipliers = {
            'HIGH_SUPPRESSION': 0.8,    # Reduce confidence in high GEX
            'MODERATE': 0.95,           # Slight reduction
            'LOW_GAMMA': 1.1,           # Boost confidence in low GEX
            'NEGATIVE_GAMMA': 0.7       # Major reduction in negative GEX
        }
        
        # Logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("⚡ GAMMA EXPOSURE ANALYZER INITIALIZED")
        self.logger.info("   Strategy: Signal Enhancement, Not Direction Prediction")
    
    def analyze_gamma_exposure(
        self, 
        options_data: pd.DataFrame,
        current_spy_price: float,
        time_to_expiry: float = 0.25  # 0DTE = ~6 hours / 24 hours
    ) -> GammaExposureAnalysis:
        """
        Analyze gamma exposure environment and its impact on direction detection
        
        Args:
            options_data: Current options chain
            current_spy_price: Current SPY price
            time_to_expiry: Time to expiration in days (0DTE = ~0.25)
        """
        
        self.logger.info("⚡ ANALYZING GAMMA EXPOSURE ENVIRONMENT")
        
        # Calculate gamma exposure for each option
        gamma_data = self._calculate_option_gammas(options_data, current_spy_price, time_to_expiry)
        
        # Aggregate gamma exposure by strike
        strike_gamma = self._aggregate_gamma_by_strike(gamma_data)
        
        # Calculate total exposures
        exposures = self._calculate_total_exposures(strike_gamma, current_spy_price)
        
        # Classify GEX environment
        gex_environment = self._classify_gex_environment(exposures['net_gamma_exposure'])
        
        # Assess direction reliability
        direction_reliability = self.reliability_map[gex_environment]
        
        # Calculate confidence multiplier
        confidence_multiplier = self.confidence_multipliers[gex_environment]
        
        # Identify key gamma levels
        key_levels = self._identify_key_gamma_levels(strike_gamma, current_spy_price)
        
        # Calculate signal quality score
        signal_quality_score = self._calculate_signal_quality_score(
            gex_environment, direction_reliability, key_levels, current_spy_price
        )
        
        # Generate reasoning
        gex_factors, warnings = self._generate_gex_reasoning(
            gex_environment, exposures, key_levels, current_spy_price
        )
        
        analysis = GammaExposureAnalysis(
            total_gamma_exposure=exposures['total_gamma_exposure'],
            call_gamma_exposure=exposures['call_gamma_exposure'],
            put_gamma_exposure=exposures['put_gamma_exposure'],
            net_gamma_exposure=exposures['net_gamma_exposure'],
            gex_environment=gex_environment,
            direction_reliability=direction_reliability,
            major_gamma_strikes=key_levels['major_strikes'],
            gamma_flip_level=key_levels['gamma_flip_level'],
            resistance_levels=key_levels['resistance_levels'],
            support_levels=key_levels['support_levels'],
            confidence_multiplier=confidence_multiplier,
            signal_quality_score=signal_quality_score,
            gex_factors=gex_factors,
            warnings=warnings
        )
        
        self.logger.info(f"⚡ GEX ANALYSIS COMPLETE:")
        self.logger.info(f"   Environment: {gex_environment}")
        self.logger.info(f"   Direction Reliability: {direction_reliability}")
        self.logger.info(f"   Confidence Multiplier: {confidence_multiplier:.2f}x")
        self.logger.info(f"   Signal Quality: {signal_quality_score:.1f}/100")
        
        return analysis
    
    def _calculate_option_gammas(
        self, 
        options_data: pd.DataFrame, 
        spot_price: float, 
        time_to_expiry: float
    ) -> pd.DataFrame:
        """Calculate gamma for each option using Black-Scholes"""
        
        gamma_data = options_data.copy()
        
        # Estimate implied volatility from volume (simplified)
        gamma_data['estimated_iv'] = np.where(
            gamma_data['volume'] > 100, 0.25,  # High volume = higher IV
            np.where(gamma_data['volume'] > 50, 0.20, 0.15)  # Default IVs
        )
        
        # Calculate gamma using simplified Black-Scholes gamma formula
        # Gamma = (phi(d1)) / (S * sigma * sqrt(T))
        # Where phi is the standard normal PDF
        
        d1_values = []
        gamma_values = []
        
        for _, row in gamma_data.iterrows():
            strike = row['strike']
            iv = row['estimated_iv']
            
            if time_to_expiry <= 0:
                gamma = 0  # No gamma at expiration
            else:
                # Simplified d1 calculation
                d1 = (np.log(spot_price / strike) + (0.05 + 0.5 * iv**2) * time_to_expiry) / (iv * np.sqrt(time_to_expiry))
                
                # Standard normal PDF
                phi_d1 = (1 / np.sqrt(2 * np.pi)) * np.exp(-0.5 * d1**2)
                
                # Gamma calculation
                gamma = phi_d1 / (spot_price * iv * np.sqrt(time_to_expiry))
            
            d1_values.append(d1)
            gamma_values.append(gamma)
        
        gamma_data['d1'] = d1_values
        gamma_data['gamma'] = gamma_values
        
        # Calculate dollar gamma exposure
        # Dollar Gamma = Gamma * Open Interest * 100 * Spot Price^2 / 100
        gamma_data['open_interest'] = np.where(
            gamma_data['volume'] > 0, 
            gamma_data['volume'] * 10,  # Estimate OI from volume
            0
        )
        
        gamma_data['dollar_gamma'] = (
            gamma_data['gamma'] * 
            gamma_data['open_interest'] * 
            100 *  # Contract multiplier
            spot_price**2 / 100  # Convert to millions
        )
        
        return gamma_data
    
    def _aggregate_gamma_by_strike(self, gamma_data: pd.DataFrame) -> pd.DataFrame:
        """Aggregate gamma exposure by strike price"""
        
        strike_gamma = gamma_data.groupby('strike').agg({
            'dollar_gamma': 'sum',
            'volume': 'sum',
            'open_interest': 'sum'
        }).reset_index()
        
        # Separate calls and puts
        calls = gamma_data[gamma_data['option_type'] == 'call'].groupby('strike')['dollar_gamma'].sum()
        puts = gamma_data[gamma_data['option_type'] == 'put'].groupby('strike')['dollar_gamma'].sum()
        
        strike_gamma = strike_gamma.merge(calls.rename('call_gamma'), on='strike', how='left')
        strike_gamma = strike_gamma.merge(puts.rename('put_gamma'), on='strike', how='left')
        
        strike_gamma['call_gamma'] = strike_gamma['call_gamma'].fillna(0)
        strike_gamma['put_gamma'] = strike_gamma['put_gamma'].fillna(0)
        
        # Net gamma (calls are positive, puts are negative for dealers)
        strike_gamma['net_gamma'] = strike_gamma['call_gamma'] - strike_gamma['put_gamma']
        
        return strike_gamma.sort_values('strike')
    
    def _calculate_total_exposures(self, strike_gamma: pd.DataFrame, current_price: float) -> Dict[str, float]:
        """Calculate total gamma exposures"""
        
        total_gamma = strike_gamma['dollar_gamma'].sum()
        call_gamma = strike_gamma['call_gamma'].sum()
        put_gamma = strike_gamma['put_gamma'].sum()
        net_gamma = strike_gamma['net_gamma'].sum()
        
        return {
            'total_gamma_exposure': total_gamma,
            'call_gamma_exposure': call_gamma,
            'put_gamma_exposure': put_gamma,
            'net_gamma_exposure': net_gamma
        }
    
    def _classify_gex_environment(self, net_gamma_exposure: float) -> str:
        """Classify the gamma exposure environment"""
        
        abs_gamma = abs(net_gamma_exposure)
        
        if net_gamma_exposure < self.gex_thresholds['negative_gamma']:
            return 'NEGATIVE_GAMMA'
        elif abs_gamma > self.gex_thresholds['high_suppression']:
            return 'HIGH_SUPPRESSION'
        elif abs_gamma > self.gex_thresholds['moderate_suppression']:
            return 'MODERATE'
        else:
            return 'LOW_GAMMA'
    
    def _identify_key_gamma_levels(self, strike_gamma: pd.DataFrame, current_price: float) -> Dict[str, Any]:
        """Identify key gamma levels and strikes"""
        
        # Find strikes with highest gamma exposure
        major_strikes = strike_gamma.nlargest(5, 'dollar_gamma')['strike'].tolist()
        
        # Find gamma flip level (where net gamma changes sign)
        gamma_flip_level = None
        for i in range(len(strike_gamma) - 1):
            current_gamma = strike_gamma.iloc[i]['net_gamma']
            next_gamma = strike_gamma.iloc[i + 1]['net_gamma']
            
            if (current_gamma > 0 and next_gamma < 0) or (current_gamma < 0 and next_gamma > 0):
                gamma_flip_level = strike_gamma.iloc[i]['strike']
                break
        
        # Identify resistance and support levels
        above_price = strike_gamma[strike_gamma['strike'] > current_price]
        below_price = strike_gamma[strike_gamma['strike'] < current_price]
        
        resistance_levels = above_price.nlargest(3, 'dollar_gamma')['strike'].tolist()
        support_levels = below_price.nlargest(3, 'dollar_gamma')['strike'].tolist()
        
        return {
            'major_strikes': major_strikes,
            'gamma_flip_level': gamma_flip_level,
            'resistance_levels': resistance_levels,
            'support_levels': support_levels
        }
    
    def _calculate_signal_quality_score(
        self, 
        gex_environment: str, 
        direction_reliability: str,
        key_levels: Dict, 
        current_price: float
    ) -> float:
        """Calculate overall signal quality score"""
        
        base_scores = {
            'HIGH_SUPPRESSION': 30,
            'MODERATE': 60,
            'LOW_GAMMA': 85,
            'NEGATIVE_GAMMA': 40
        }
        
        base_score = base_scores[gex_environment]
        
        # Adjust based on proximity to major gamma levels
        proximity_penalty = 0
        for strike in key_levels['major_strikes'][:3]:  # Top 3 strikes
            distance_pct = abs(current_price - strike) / current_price
            if distance_pct < 0.01:  # Within 1%
                proximity_penalty += 15
            elif distance_pct < 0.02:  # Within 2%
                proximity_penalty += 10
        
        final_score = max(10, base_score - proximity_penalty)
        
        return final_score
    
    def _generate_gex_reasoning(
        self, 
        gex_environment: str, 
        exposures: Dict,
        key_levels: Dict, 
        current_price: float
    ) -> Tuple[List[str], List[str]]:
        """Generate reasoning and warnings for GEX analysis"""
        
        factors = []
        warnings = []
        
        # Environment-specific factors
        if gex_environment == 'HIGH_SUPPRESSION':
            factors.append(f"High gamma suppression: ${exposures['net_gamma_exposure']:.0f}M")
            factors.append("Market makers will hedge aggressively, dampening moves")
            warnings.append("Direction signals may be unreliable due to gamma suppression")
            
        elif gex_environment == 'NEGATIVE_GAMMA':
            factors.append(f"Negative gamma environment: ${exposures['net_gamma_exposure']:.0f}M")
            factors.append("Market makers are short gamma - expect explosive moves")
            warnings.append("High volatility expected - use wider stops")
            
        elif gex_environment == 'LOW_GAMMA':
            factors.append(f"Low gamma environment: ${exposures['net_gamma_exposure']:.0f}M")
            factors.append("Minimal dealer hedging - direction signals more reliable")
            
        # Key level factors
        if key_levels['gamma_flip_level']:
            factors.append(f"Gamma flip level at ${key_levels['gamma_flip_level']:.0f}")
            
        # Proximity warnings
        for strike in key_levels['major_strikes'][:2]:
            distance_pct = abs(current_price - strike) / current_price
            if distance_pct < 0.015:  # Within 1.5%
                warnings.append(f"Close to major gamma strike ${strike:.0f} - expect pinning")
        
        return factors, warnings
    
    def enhance_signal_with_gex(
        self, 
        base_confidence: float, 
        gex_analysis: GammaExposureAnalysis
    ) -> Tuple[float, List[str]]:
        """
        Enhance signal confidence based on GEX analysis
        
        This is the key method: instead of blocking signals,
        we adjust confidence based on GEX environment.
        """
        
        # Apply GEX confidence multiplier
        enhanced_confidence = base_confidence * gex_analysis.confidence_multiplier
        
        # Additional adjustments based on signal quality
        if gex_analysis.signal_quality_score < 40:
            enhanced_confidence *= 0.9  # Further reduction for poor signal quality
        elif gex_analysis.signal_quality_score > 80:
            enhanced_confidence *= 1.05  # Slight boost for excellent signal quality
        
        # Cap confidence at reasonable levels
        enhanced_confidence = max(20, min(95, enhanced_confidence))
        
        # Generate enhancement reasoning
        enhancement_reasons = []
        enhancement_reasons.append(f"GEX Environment: {gex_analysis.gex_environment}")
        enhancement_reasons.append(f"Direction Reliability: {gex_analysis.direction_reliability}")
        enhancement_reasons.append(f"Confidence Multiplier: {gex_analysis.confidence_multiplier:.2f}x")
        enhancement_reasons.append(f"Signal Quality Score: {gex_analysis.signal_quality_score:.0f}/100")
        
        if gex_analysis.warnings:
            enhancement_reasons.extend([f"⚠️ {warning}" for warning in gex_analysis.warnings])
        
        return enhanced_confidence, enhancement_reasons

def main():
    """Test the Gamma Exposure Analyzer"""
    
    print("⚡ TESTING GAMMA EXPOSURE ANALYZER")
    print("=" * 70)
    
    # Initialize analyzer
    analyzer = GammaExposureAnalyzer()
    
    # Create sample options data
    sample_data = pd.DataFrame({
        'strike': [630, 635, 640, 645, 650, 625, 640, 650, 655, 660],
        'option_type': ['put', 'put', 'call', 'call', 'call', 'put', 'call', 'call', 'call', 'call'],
        'volume': [500, 800, 1200, 900, 600, 300, 1000, 700, 400, 200],
        'transactions': [50, 80, 120, 90, 60, 30, 100, 70, 40, 20]
    })
    
    current_spy_price = 640.0
    time_to_expiry = 0.25  # 6 hours for 0DTE
    
    # Test GEX analysis
    print(f"\n⚡ ANALYZING GEX FOR SPY @ ${current_spy_price}")
    gex_analysis = analyzer.analyze_gamma_exposure(sample_data, current_spy_price, time_to_expiry)
    
    print(f"\n📊 GEX ANALYSIS RESULTS:")
    print(f"   Environment: {gex_analysis.gex_environment}")
    print(f"   Direction Reliability: {gex_analysis.direction_reliability}")
    print(f"   Net Gamma Exposure: ${gex_analysis.net_gamma_exposure:.0f}M")
    print(f"   Confidence Multiplier: {gex_analysis.confidence_multiplier:.2f}x")
    print(f"   Signal Quality Score: {gex_analysis.signal_quality_score:.0f}/100")
    
    if gex_analysis.major_gamma_strikes:
        print(f"   Major Gamma Strikes: {gex_analysis.major_gamma_strikes}")
    
    if gex_analysis.gamma_flip_level:
        print(f"   Gamma Flip Level: ${gex_analysis.gamma_flip_level:.0f}")
    
    print(f"\n🔍 GEX FACTORS:")
    for factor in gex_analysis.gex_factors:
        print(f"   • {factor}")
    
    if gex_analysis.warnings:
        print(f"\n⚠️  GEX WARNINGS:")
        for warning in gex_analysis.warnings:
            print(f"   • {warning}")
    
    # Test signal enhancement
    print(f"\n🎯 TESTING SIGNAL ENHANCEMENT:")
    base_confidence = 75.0
    enhanced_confidence, reasons = analyzer.enhance_signal_with_gex(base_confidence, gex_analysis)
    
    print(f"   Base Confidence: {base_confidence:.1f}%")
    print(f"   Enhanced Confidence: {enhanced_confidence:.1f}%")
    print(f"   Enhancement: {enhanced_confidence - base_confidence:+.1f}%")
    
    print(f"\n📋 ENHANCEMENT REASONING:")
    for reason in reasons:
        print(f"   • {reason}")

if __name__ == "__main__":
    main()
