#!/usr/bin/env python3
"""
Trade Validation Framework - Inspired by ChatGPT Micro-Cap Experiment
====================================================================

COMPREHENSIVE TRADE VALIDATION FOR 0DTE OPTIONS TRADING:
1. Pre-trade validation checks (from ChatGPT repo patterns)
2. Cash constraint verification
3. Risk limit compliance
4. Market condition validation
5. Position size optimization
6. Order execution safety checks

This system provides the sophisticated trade validation that the ChatGPT
repo demonstrated for stock trading, adapted for 0DTE options strategies
with enhanced safety checks and validation logic.

Location: src/utils/ (following .cursorrules structure)
Author: Advanced Options Trading Framework - Trade Validation System
Inspired by: ChatGPT Micro-Cap Experiment trade validation patterns
"""

import pandas as pd
import numpy as np
from datetime import datetime, time
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ValidationResult(Enum):
    """Trade validation results"""
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    WARNING = "WARNING"
    CONDITIONAL = "CONDITIONAL"

class ValidationCategory(Enum):
    """Validation check categories"""
    CASH_CONSTRAINTS = "CASH_CONSTRAINTS"
    RISK_LIMITS = "RISK_LIMITS"
    MARKET_CONDITIONS = "MARKET_CONDITIONS"
    POSITION_SIZING = "POSITION_SIZING"
    TIME_RESTRICTIONS = "TIME_RESTRICTIONS"
    STRATEGY_SPECIFIC = "STRATEGY_SPECIFIC"

@dataclass
class ValidationCheck:
    """Individual validation check result"""
    category: ValidationCategory
    check_name: str
    result: ValidationResult
    message: str
    severity: str  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    recommendation: Optional[str] = None
    adjusted_value: Optional[float] = None

@dataclass
class TradeValidationRequest:
    """Trade validation request - from ChatGPT repo patterns"""
    
    # Trade Details
    strategy_type: str
    contracts: int
    premium_collected: float
    max_risk: float
    max_profit: float
    
    # Market Data
    spy_price: float
    market_regime: str
    
    # Account Information
    current_balance: float
    available_cash: float
    current_positions: int
    daily_pnl: float
    
    # Timing
    current_time: datetime
    
    # Optional fields (with defaults)
    vix_level: Optional[float] = None
    volume: Optional[float] = None
    expiration_time: Optional[datetime] = None
    short_strike: Optional[float] = None
    long_strike: Optional[float] = None
    confidence_score: Optional[float] = None

@dataclass
class TradeValidationResponse:
    """Comprehensive validation response"""
    
    overall_result: ValidationResult
    approved: bool
    confidence_level: float
    
    # Individual checks
    checks: List[ValidationCheck]
    
    # Recommendations
    recommended_contracts: Optional[int] = None
    recommended_adjustments: List[str] = None
    
    # Risk Assessment
    risk_score: float = 0.0
    risk_category: str = "UNKNOWN"
    
    # Summary
    summary_message: str = ""
    action_required: List[str] = None

class TradeValidator:
    """
    Comprehensive Trade Validation System
    
    Implements the sophisticated trade validation from the ChatGPT
    Micro-Cap experiment, including cash constraints, risk limits,
    market condition checks, and position sizing validation.
    
    Key Features (from ChatGPT repo):
    - Multi-layer validation checks
    - Cash constraint verification
    - Risk limit compliance
    - Market condition assessment
    - Position size optimization
    - Time-based restrictions
    """
    
    def __init__(self, 
                 max_daily_loss: float = 400.0,
                 max_daily_profit: float = 250.0,
                 max_risk_per_trade: float = 0.016,
                 max_positions: int = 4,
                 min_account_balance: float = 1000.0):
        """
        Initialize trade validator with risk parameters
        
        Args:
            max_daily_loss: Maximum daily loss limit
            max_daily_profit: Daily profit target
            max_risk_per_trade: Maximum risk per trade (as % of account)
            max_positions: Maximum concurrent positions
            min_account_balance: Minimum account balance required
        """
        
        self.max_daily_loss = max_daily_loss
        self.max_daily_profit = max_daily_profit
        self.max_risk_per_trade = max_risk_per_trade
        self.max_positions = max_positions
        self.min_account_balance = min_account_balance
        
        # Market hours (ET)
        self.market_open = time(9, 30)
        self.market_close = time(16, 0)
        self.no_new_trades_after = time(14, 30)  # 2:30 PM ET
        self.force_close_by = time(15, 30)       # 3:30 PM ET
        
        logger.info("✅ TRADE VALIDATOR INITIALIZED")
        logger.info(f"   Max Daily Loss: ${max_daily_loss}")
        logger.info(f"   Daily Target: ${max_daily_profit}")
        logger.info(f"   Max Risk/Trade: {max_risk_per_trade:.1%}")
        logger.info(f"   Max Positions: {max_positions}")
    
    def validate_trade(self, request: TradeValidationRequest) -> TradeValidationResponse:
        """
        Comprehensive trade validation
        
        Implements the multi-layer validation system from ChatGPT repo's
        trade execution framework.
        
        Args:
            request: Trade validation request
            
        Returns:
            Comprehensive validation response
        """
        
        checks = []
        
        # 1. Cash Constraints (from ChatGPT repo pattern)
        cash_checks = self._validate_cash_constraints(request)
        checks.extend(cash_checks)
        
        # 2. Risk Limits
        risk_checks = self._validate_risk_limits(request)
        checks.extend(risk_checks)
        
        # 3. Market Conditions
        market_checks = self._validate_market_conditions(request)
        checks.extend(market_checks)
        
        # 4. Position Sizing
        sizing_checks = self._validate_position_sizing(request)
        checks.extend(sizing_checks)
        
        # 5. Time Restrictions
        time_checks = self._validate_time_restrictions(request)
        checks.extend(time_checks)
        
        # 6. Strategy Specific
        strategy_checks = self._validate_strategy_specific(request)
        checks.extend(strategy_checks)
        
        # Determine overall result
        overall_result, approved, confidence = self._determine_overall_result(checks)
        
        # Generate recommendations
        recommended_contracts, adjustments = self._generate_recommendations(request, checks)
        
        # Calculate risk assessment
        risk_score, risk_category = self._assess_risk(request, checks)
        
        # Create summary
        summary_message = self._create_summary(overall_result, checks)
        
        # Action items
        action_required = self._determine_actions(checks)
        
        return TradeValidationResponse(
            overall_result=overall_result,
            approved=approved,
            confidence_level=confidence,
            checks=checks,
            recommended_contracts=recommended_contracts,
            recommended_adjustments=adjustments,
            risk_score=risk_score,
            risk_category=risk_category,
            summary_message=summary_message,
            action_required=action_required
        )
    
    def _validate_cash_constraints(self, request: TradeValidationRequest) -> List[ValidationCheck]:
        """
        Validate cash constraints
        
        Implements cash constraint checking from ChatGPT repo's
        position validation system.
        """
        
        checks = []
        
        # 1. Minimum account balance
        if request.current_balance < self.min_account_balance:
            checks.append(ValidationCheck(
                category=ValidationCategory.CASH_CONSTRAINTS,
                check_name="Minimum Balance",
                result=ValidationResult.REJECTED,
                message=f"Account balance ${request.current_balance:,.2f} below minimum ${self.min_account_balance:,.2f}",
                severity="CRITICAL",
                recommendation="Deposit funds or reduce position size"
            ))
        
        # 2. Available cash for margin
        required_margin = request.max_risk  # Simplified for 0DTE
        if required_margin > request.available_cash:
            checks.append(ValidationCheck(
                category=ValidationCategory.CASH_CONSTRAINTS,
                check_name="Margin Requirement",
                result=ValidationResult.REJECTED,
                message=f"Insufficient margin: need ${required_margin:,.2f}, have ${request.available_cash:,.2f}",
                severity="CRITICAL",
                recommendation="Reduce position size or close other positions"
            ))
        else:
            checks.append(ValidationCheck(
                category=ValidationCategory.CASH_CONSTRAINTS,
                check_name="Margin Requirement",
                result=ValidationResult.APPROVED,
                message=f"Sufficient margin: ${request.available_cash:,.2f} available",
                severity="LOW"
            ))
        
        # 3. Cash utilization check
        cash_utilization = required_margin / request.current_balance
        if cash_utilization > 0.80:  # 80% cash utilization warning
            checks.append(ValidationCheck(
                category=ValidationCategory.CASH_CONSTRAINTS,
                check_name="Cash Utilization",
                result=ValidationResult.WARNING,
                message=f"High cash utilization: {cash_utilization:.1%}",
                severity="MEDIUM",
                recommendation="Consider reducing position size for better cash management"
            ))
        
        return checks
    
    def _validate_risk_limits(self, request: TradeValidationRequest) -> List[ValidationCheck]:
        """
        Validate risk limits
        
        Implements risk limit checking from ChatGPT repo's
        risk management system.
        """
        
        checks = []
        
        # 1. Daily loss limit
        potential_daily_loss = request.daily_pnl - request.max_risk
        if potential_daily_loss <= -self.max_daily_loss:
            checks.append(ValidationCheck(
                category=ValidationCategory.RISK_LIMITS,
                check_name="Daily Loss Limit",
                result=ValidationResult.REJECTED,
                message=f"Would exceed daily loss limit: ${potential_daily_loss:.2f} <= ${-self.max_daily_loss:.2f}",
                severity="CRITICAL",
                recommendation="Stop trading for the day"
            ))
        elif potential_daily_loss <= -self.max_daily_loss * 0.75:
            checks.append(ValidationCheck(
                category=ValidationCategory.RISK_LIMITS,
                check_name="Daily Loss Limit",
                result=ValidationResult.WARNING,
                message=f"Approaching daily loss limit: ${potential_daily_loss:.2f}",
                severity="HIGH",
                recommendation="Consider reducing position size"
            ))
        else:
            checks.append(ValidationCheck(
                category=ValidationCategory.RISK_LIMITS,
                check_name="Daily Loss Limit",
                result=ValidationResult.APPROVED,
                message=f"Within daily loss limit: ${potential_daily_loss:.2f}",
                severity="LOW"
            ))
        
        # 2. Per-trade risk limit
        risk_percentage = request.max_risk / request.current_balance
        if risk_percentage > self.max_risk_per_trade:
            checks.append(ValidationCheck(
                category=ValidationCategory.RISK_LIMITS,
                check_name="Per-Trade Risk",
                result=ValidationResult.REJECTED,
                message=f"Exceeds per-trade risk limit: {risk_percentage:.1%} > {self.max_risk_per_trade:.1%}",
                severity="CRITICAL",
                recommendation="Reduce position size",
                adjusted_value=int(request.contracts * self.max_risk_per_trade / risk_percentage)
            ))
        elif risk_percentage > self.max_risk_per_trade * 0.8:
            checks.append(ValidationCheck(
                category=ValidationCategory.RISK_LIMITS,
                check_name="Per-Trade Risk",
                result=ValidationResult.WARNING,
                message=f"High per-trade risk: {risk_percentage:.1%}",
                severity="MEDIUM",
                recommendation="Consider reducing position size"
            ))
        else:
            checks.append(ValidationCheck(
                category=ValidationCategory.RISK_LIMITS,
                check_name="Per-Trade Risk",
                result=ValidationResult.APPROVED,
                message=f"Acceptable per-trade risk: {risk_percentage:.1%}",
                severity="LOW"
            ))
        
        # 3. Daily profit target check
        if request.daily_pnl >= self.max_daily_profit:
            checks.append(ValidationCheck(
                category=ValidationCategory.RISK_LIMITS,
                check_name="Daily Profit Target",
                result=ValidationResult.CONDITIONAL,
                message=f"Daily profit target reached: ${request.daily_pnl:.2f}",
                severity="MEDIUM",
                recommendation="Consider stopping trading for the day"
            ))
        
        # 4. Position count limit
        if request.current_positions >= self.max_positions:
            checks.append(ValidationCheck(
                category=ValidationCategory.RISK_LIMITS,
                check_name="Position Count",
                result=ValidationResult.REJECTED,
                message=f"Maximum positions reached: {request.current_positions}/{self.max_positions}",
                severity="HIGH",
                recommendation="Close existing positions before opening new ones"
            ))
        elif request.current_positions >= self.max_positions * 0.8:
            checks.append(ValidationCheck(
                category=ValidationCategory.RISK_LIMITS,
                check_name="Position Count",
                result=ValidationResult.WARNING,
                message=f"Approaching position limit: {request.current_positions}/{self.max_positions}",
                severity="MEDIUM",
                recommendation="Monitor position count carefully"
            ))
        
        return checks
    
    def _validate_market_conditions(self, request: TradeValidationRequest) -> List[ValidationCheck]:
        """
        Validate market conditions
        
        Implements market condition checking from ChatGPT repo's
        market analysis system.
        """
        
        checks = []
        
        # 1. VIX level check
        if request.vix_level is not None:
            if request.vix_level > 35:
                checks.append(ValidationCheck(
                    category=ValidationCategory.MARKET_CONDITIONS,
                    check_name="VIX Level",
                    result=ValidationResult.WARNING,
                    message=f"High VIX level: {request.vix_level:.1f}",
                    severity="HIGH",
                    recommendation="Exercise caution in high volatility environment"
                ))
            elif request.vix_level < 15:
                checks.append(ValidationCheck(
                    category=ValidationCategory.MARKET_CONDITIONS,
                    check_name="VIX Level",
                    result=ValidationResult.WARNING,
                    message=f"Low VIX level: {request.vix_level:.1f}",
                    severity="MEDIUM",
                    recommendation="Limited premium opportunities in low volatility"
                ))
            else:
                checks.append(ValidationCheck(
                    category=ValidationCategory.MARKET_CONDITIONS,
                    check_name="VIX Level",
                    result=ValidationResult.APPROVED,
                    message=f"Normal VIX level: {request.vix_level:.1f}",
                    severity="LOW"
                ))
        
        # 2. Market regime validation
        regime_confidence = {
            'BULLISH': 0.8,
            'BEARISH': 0.8,
            'NEUTRAL': 0.9,
            'NO_TRADE': 0.0
        }
        
        confidence = regime_confidence.get(request.market_regime, 0.5)
        
        if request.market_regime == 'NO_TRADE':
            checks.append(ValidationCheck(
                category=ValidationCategory.MARKET_CONDITIONS,
                check_name="Market Regime",
                result=ValidationResult.REJECTED,
                message="Market regime indicates no trading",
                severity="HIGH",
                recommendation="Wait for better market conditions"
            ))
        elif confidence < 0.6:
            checks.append(ValidationCheck(
                category=ValidationCategory.MARKET_CONDITIONS,
                check_name="Market Regime",
                result=ValidationResult.WARNING,
                message=f"Uncertain market regime: {request.market_regime}",
                severity="MEDIUM",
                recommendation="Consider reducing position size due to uncertainty"
            ))
        else:
            checks.append(ValidationCheck(
                category=ValidationCategory.MARKET_CONDITIONS,
                check_name="Market Regime",
                result=ValidationResult.APPROVED,
                message=f"Clear market regime: {request.market_regime}",
                severity="LOW"
            ))
        
        # 3. Volume check
        if request.volume is not None:
            avg_volume = 50_000_000  # Approximate SPY average volume
            if request.volume < avg_volume * 0.5:
                checks.append(ValidationCheck(
                    category=ValidationCategory.MARKET_CONDITIONS,
                    check_name="Market Volume",
                    result=ValidationResult.WARNING,
                    message=f"Low market volume: {request.volume:,.0f}",
                    severity="MEDIUM",
                    recommendation="Exercise caution in low volume conditions"
                ))
        
        return checks
    
    def _validate_position_sizing(self, request: TradeValidationRequest) -> List[ValidationCheck]:
        """
        Validate position sizing
        
        Implements position sizing validation from ChatGPT repo's
        portfolio management system.
        """
        
        checks = []
        
        # 1. Minimum position size
        if request.contracts < 1:
            checks.append(ValidationCheck(
                category=ValidationCategory.POSITION_SIZING,
                check_name="Minimum Size",
                result=ValidationResult.REJECTED,
                message="Position size must be at least 1 contract",
                severity="CRITICAL",
                recommendation="Increase position size to minimum 1 contract"
            ))
        
        # 2. Maximum position size (concentration risk)
        max_position_value = request.current_balance * 0.25  # 25% max concentration
        position_value = request.contracts * request.premium_collected * 100
        
        if position_value > max_position_value:
            max_contracts = int(max_position_value / (request.premium_collected * 100))
            checks.append(ValidationCheck(
                category=ValidationCategory.POSITION_SIZING,
                check_name="Concentration Risk",
                result=ValidationResult.WARNING,
                message=f"Large position size: ${position_value:,.2f} ({position_value/request.current_balance:.1%} of account)",
                severity="MEDIUM",
                recommendation=f"Consider reducing to {max_contracts} contracts",
                adjusted_value=max_contracts
            ))
        
        # 3. Risk-reward ratio
        if request.max_profit > 0:
            risk_reward_ratio = request.max_risk / request.max_profit
            if risk_reward_ratio > 3.0:  # Risk more than 3x potential profit
                checks.append(ValidationCheck(
                    category=ValidationCategory.POSITION_SIZING,
                    check_name="Risk-Reward Ratio",
                    result=ValidationResult.WARNING,
                    message=f"Poor risk-reward ratio: {risk_reward_ratio:.1f}:1",
                    severity="MEDIUM",
                    recommendation="Consider strategies with better risk-reward profile"
                ))
            elif risk_reward_ratio < 0.5:  # Very favorable
                checks.append(ValidationCheck(
                    category=ValidationCategory.POSITION_SIZING,
                    check_name="Risk-Reward Ratio",
                    result=ValidationResult.APPROVED,
                    message=f"Excellent risk-reward ratio: {risk_reward_ratio:.1f}:1",
                    severity="LOW"
                ))
        
        return checks
    
    def _validate_time_restrictions(self, request: TradeValidationRequest) -> List[ValidationCheck]:
        """
        Validate time-based restrictions
        
        Implements time restriction checking from ChatGPT repo's
        trading schedule system.
        """
        
        checks = []
        
        current_time = request.current_time.time()
        
        # 1. Market hours check
        if current_time < self.market_open or current_time > self.market_close:
            checks.append(ValidationCheck(
                category=ValidationCategory.TIME_RESTRICTIONS,
                check_name="Market Hours",
                result=ValidationResult.REJECTED,
                message=f"Outside market hours: {current_time}",
                severity="CRITICAL",
                recommendation="Wait for market open"
            ))
        
        # 2. No new trades after 2:30 PM ET
        elif current_time > self.no_new_trades_after:
            checks.append(ValidationCheck(
                category=ValidationCategory.TIME_RESTRICTIONS,
                check_name="Late Day Trading",
                result=ValidationResult.WARNING,
                message=f"Late in trading day: {current_time}",
                severity="HIGH",
                recommendation="Avoid new positions close to market close"
            ))
        
        # 3. Force close by 3:30 PM ET
        elif current_time > self.force_close_by:
            checks.append(ValidationCheck(
                category=ValidationCategory.TIME_RESTRICTIONS,
                check_name="Force Close Time",
                result=ValidationResult.REJECTED,
                message=f"Past force close time: {current_time}",
                severity="CRITICAL",
                recommendation="Close existing positions, no new trades"
            ))
        
        # 4. Early morning caution (first 15 minutes)
        early_cutoff = time(9, 45)
        if current_time < early_cutoff:
            checks.append(ValidationCheck(
                category=ValidationCategory.TIME_RESTRICTIONS,
                check_name="Early Trading",
                result=ValidationResult.WARNING,
                message=f"Early in trading session: {current_time}",
                severity="MEDIUM",
                recommendation="Exercise caution during market open volatility"
            ))
        
        # 5. 0DTE expiration timing
        if request.expiration_time:
            time_to_expiry = (request.expiration_time - request.current_time).total_seconds() / 3600
            if time_to_expiry < 1:  # Less than 1 hour to expiry
                checks.append(ValidationCheck(
                    category=ValidationCategory.TIME_RESTRICTIONS,
                    check_name="Time to Expiry",
                    result=ValidationResult.WARNING,
                    message=f"Close to expiry: {time_to_expiry:.1f} hours",
                    severity="HIGH",
                    recommendation="High gamma risk near expiration"
                ))
        
        return checks
    
    def _validate_strategy_specific(self, request: TradeValidationRequest) -> List[ValidationCheck]:
        """
        Validate strategy-specific requirements
        
        Implements strategy validation from ChatGPT repo's
        strategy-specific checking system.
        """
        
        checks = []
        
        # 1. Premium collection minimum
        min_premium = 0.30  # $30 minimum premium
        if request.premium_collected < min_premium:
            checks.append(ValidationCheck(
                category=ValidationCategory.STRATEGY_SPECIFIC,
                check_name="Premium Threshold",
                result=ValidationResult.REJECTED,
                message=f"Premium too low: ${request.premium_collected:.2f} < ${min_premium:.2f}",
                severity="HIGH",
                recommendation="Look for higher premium opportunities"
            ))
        
        # 2. Strike selection validation
        if request.short_strike and request.long_strike:
            strike_width = abs(request.short_strike - request.long_strike)
            if strike_width < 1.0:
                checks.append(ValidationCheck(
                    category=ValidationCategory.STRATEGY_SPECIFIC,
                    check_name="Strike Width",
                    result=ValidationResult.WARNING,
                    message=f"Narrow strike width: ${strike_width:.2f}",
                    severity="MEDIUM",
                    recommendation="Consider wider strikes for better risk-reward"
                ))
            elif strike_width > 5.0:
                checks.append(ValidationCheck(
                    category=ValidationCategory.STRATEGY_SPECIFIC,
                    check_name="Strike Width",
                    result=ValidationResult.WARNING,
                    message=f"Wide strike width: ${strike_width:.2f}",
                    severity="MEDIUM",
                    recommendation="Wide strikes increase risk"
                ))
        
        # 3. Confidence score validation
        if request.confidence_score is not None:
            if request.confidence_score < 60:
                checks.append(ValidationCheck(
                    category=ValidationCategory.STRATEGY_SPECIFIC,
                    check_name="Strategy Confidence",
                    result=ValidationResult.WARNING,
                    message=f"Low confidence score: {request.confidence_score:.1f}%",
                    severity="MEDIUM",
                    recommendation="Consider waiting for higher confidence setups"
                ))
            elif request.confidence_score > 85:
                checks.append(ValidationCheck(
                    category=ValidationCategory.STRATEGY_SPECIFIC,
                    check_name="Strategy Confidence",
                    result=ValidationResult.APPROVED,
                    message=f"High confidence score: {request.confidence_score:.1f}%",
                    severity="LOW"
                ))
        
        return checks
    
    def _determine_overall_result(self, checks: List[ValidationCheck]) -> Tuple[ValidationResult, bool, float]:
        """Determine overall validation result"""
        
        # Count results by type
        rejected = sum(1 for c in checks if c.result == ValidationResult.REJECTED)
        warnings = sum(1 for c in checks if c.result == ValidationResult.WARNING)
        approved = sum(1 for c in checks if c.result == ValidationResult.APPROVED)
        
        # Determine overall result
        if rejected > 0:
            return ValidationResult.REJECTED, False, 0.0
        elif warnings > 2:  # Too many warnings
            return ValidationResult.CONDITIONAL, False, 0.3
        elif warnings > 0:
            return ValidationResult.WARNING, True, 0.7
        else:
            return ValidationResult.APPROVED, True, 0.9
    
    def _generate_recommendations(self, request: TradeValidationRequest, 
                                checks: List[ValidationCheck]) -> Tuple[Optional[int], List[str]]:
        """Generate position size and other recommendations"""
        
        recommended_contracts = None
        adjustments = []
        
        # Find position size adjustments
        for check in checks:
            if check.adjusted_value is not None:
                if recommended_contracts is None:
                    recommended_contracts = int(check.adjusted_value)
                else:
                    recommended_contracts = min(recommended_contracts, int(check.adjusted_value))
        
        # Collect recommendations
        for check in checks:
            if check.recommendation and check.recommendation not in adjustments:
                adjustments.append(check.recommendation)
        
        return recommended_contracts, adjustments
    
    def _assess_risk(self, request: TradeValidationRequest, 
                    checks: List[ValidationCheck]) -> Tuple[float, str]:
        """Assess overall risk level"""
        
        risk_score = 0.0
        
        # Weight by severity
        severity_weights = {'LOW': 1, 'MEDIUM': 3, 'HIGH': 7, 'CRITICAL': 15}
        
        for check in checks:
            weight = severity_weights.get(check.severity, 1)
            if check.result == ValidationResult.REJECTED:
                risk_score += weight * 3
            elif check.result == ValidationResult.WARNING:
                risk_score += weight * 1
        
        # Normalize to 0-100 scale
        risk_score = min(100, risk_score)
        
        # Categorize risk
        if risk_score >= 50:
            risk_category = "HIGH"
        elif risk_score >= 25:
            risk_category = "MEDIUM"
        else:
            risk_category = "LOW"
        
        return risk_score, risk_category
    
    def _create_summary(self, result: ValidationResult, checks: List[ValidationCheck]) -> str:
        """Create validation summary message"""
        
        if result == ValidationResult.APPROVED:
            return "Trade approved - all validation checks passed"
        elif result == ValidationResult.REJECTED:
            critical_issues = [c.message for c in checks if c.result == ValidationResult.REJECTED]
            return f"Trade rejected - Critical issues: {'; '.join(critical_issues[:2])}"
        elif result == ValidationResult.WARNING:
            return "Trade approved with warnings - monitor carefully"
        else:
            return "Trade conditionally approved - address warnings before execution"
    
    def _determine_actions(self, checks: List[ValidationCheck]) -> List[str]:
        """Determine required actions"""
        
        actions = []
        
        rejected_checks = [c for c in checks if c.result == ValidationResult.REJECTED]
        if rejected_checks:
            actions.append("Address critical validation failures")
        
        warning_checks = [c for c in checks if c.result == ValidationResult.WARNING]
        if len(warning_checks) > 2:
            actions.append("Review and address multiple warnings")
        
        return actions
    
    def print_validation_report(self, response: TradeValidationResponse) -> None:
        """
        Print comprehensive validation report
        
        Displays validation results similar to ChatGPT repo's
        trade validation system.
        """
        
        print("\n" + "=" * 70)
        print("✅ TRADE VALIDATION REPORT")
        print("=" * 70)
        
        # Overall Result
        status_emoji = {
            ValidationResult.APPROVED: "✅",
            ValidationResult.REJECTED: "❌",
            ValidationResult.WARNING: "⚠️",
            ValidationResult.CONDITIONAL: "🔶"
        }
        
        print(f"\n🎯 OVERALL RESULT: {status_emoji[response.overall_result]} {response.overall_result.value}")
        print(f"   Approved: {'YES' if response.approved else 'NO'}")
        print(f"   Confidence: {response.confidence_level:.1%}")
        print(f"   Risk Score: {response.risk_score:.0f}/100 ({response.risk_category})")
        
        # Summary
        print(f"\n📋 SUMMARY: {response.summary_message}")
        
        # Recommendations
        if response.recommended_contracts:
            print(f"\n💡 RECOMMENDED POSITION SIZE: {response.recommended_contracts} contracts")
        
        if response.recommended_adjustments:
            print(f"\n🔧 RECOMMENDED ADJUSTMENTS:")
            for adj in response.recommended_adjustments[:3]:  # Show top 3
                print(f"   • {adj}")
        
        # Validation Checks by Category
        categories = {}
        for check in response.checks:
            if check.category not in categories:
                categories[check.category] = []
            categories[check.category].append(check)
        
        print(f"\n📊 DETAILED VALIDATION CHECKS:")
        for category, checks in categories.items():
            print(f"\n   {category.value}:")
            for check in checks:
                result_emoji = {
                    ValidationResult.APPROVED: "✅",
                    ValidationResult.REJECTED: "❌",
                    ValidationResult.WARNING: "⚠️",
                    ValidationResult.CONDITIONAL: "🔶"
                }
                print(f"     {result_emoji[check.result]} {check.check_name}: {check.message}")
        
        # Action Items
        if response.action_required:
            print(f"\n🚨 ACTION REQUIRED:")
            for action in response.action_required:
                print(f"   • {action}")

# Example usage and integration patterns
if __name__ == "__main__":
    """
    Example usage of the Trade Validator
    
    Demonstrates integration patterns from ChatGPT repo
    """
    
    # Initialize validator
    validator = TradeValidator(
        max_daily_loss=400.0,
        max_daily_profit=250.0,
        max_risk_per_trade=0.016,
        max_positions=4
    )
    
    # Create validation request
    request = TradeValidationRequest(
        strategy_type="IRON_CONDOR",
        contracts=2,
        premium_collected=0.50,
        max_risk=150.0,
        max_profit=100.0,
        spy_price=472.50,
        market_regime="NEUTRAL",
        vix_level=18.5,
        volume=45_000_000,
        current_balance=25000.0,
        available_cash=24000.0,
        current_positions=1,
        daily_pnl=50.0,
        current_time=datetime.now().replace(hour=10, minute=30),
        short_strike=470.0,
        long_strike=468.0,
        confidence_score=75.0
    )
    
    # Validate trade
    response = validator.validate_trade(request)
    
    # Print report
    validator.print_validation_report(response)
    
    print(f"\nTrade Decision: {'EXECUTE' if response.approved else 'REJECT'}")
    if response.recommended_contracts:
        print(f"Recommended Size: {response.recommended_contracts} contracts")
