#!/usr/bin/env python3
"""
ChatGPT Micro-Cap Integration Example
====================================

COMPREHENSIVE EXAMPLE: Using all three ChatGPT repo-inspired modules together
in a complete 0DTE options trading workflow.

This example demonstrates how to integrate:
1. Risk Manager - Automated risk controls and position monitoring
2. Performance Analytics - Advanced performance metrics and analysis  
3. Trade Validator - Pre-trade validation and safety checks

The integration follows the sophisticated patterns from the ChatGPT Micro-Cap
experiment while maintaining compatibility with your existing .cursorrules
structure and 0DTE trading strategies.

Location: src/examples/ (following .cursorrules structure)
Author: Advanced Options Trading Framework - Integration Example
Inspired by: ChatGPT Micro-Cap Experiment comprehensive trading system
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

# Import the three new modules
from src.utils.risk_manager import RiskManager, RiskLimits, PositionRisk
from src.utils.performance_analytics import PerformanceAnalyzer, PerformanceMetrics
from src.utils.trade_validator import TradeValidator, TradeValidationRequest, ValidationResult

# Import existing system components
from src.strategies.professional_0dte.professional_credit_spread_system import (
    Professional0DTESystem, ProfessionalConfig, TradeSignal, SpreadType
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedTradingSystem:
    """
    Enhanced 0DTE Trading System with ChatGPT Repo Integration
    
    Combines your existing Professional0DTESystem with the three new modules:
    - Risk Manager for automated risk controls
    - Performance Analytics for advanced metrics
    - Trade Validator for pre-trade safety checks
    
    This creates a comprehensive trading system with institutional-grade
    risk management and performance tracking.
    """
    
    def __init__(self, config: Optional[ProfessionalConfig] = None):
        """Initialize enhanced trading system"""
        
        # Core trading system
        self.config = config or ProfessionalConfig()
        self.trading_system = Professional0DTESystem(self.config)
        
        # Risk management (from ChatGPT repo patterns)
        risk_limits = RiskLimits(
            max_daily_loss=self.config.max_daily_loss,
            max_daily_profit=self.config.max_daily_profit,
            max_risk_per_trade_pct=self.config.max_risk_per_trade_pct,
            max_concurrent_positions=4
        )
        self.risk_manager = RiskManager(risk_limits)
        
        # Performance analytics (enhanced metrics)
        self.performance_analyzer = PerformanceAnalyzer(risk_free_rate=0.045)
        
        # Trade validation (safety checks)
        self.trade_validator = TradeValidator(
            max_daily_loss=self.config.max_daily_loss,
            max_daily_profit=self.config.max_daily_profit,
            max_risk_per_trade=self.config.max_risk_per_trade_pct,
            max_positions=4
        )
        
        # Trading state
        self.equity_curve: List[float] = [self.config.account_balance]
        self.trade_history: List[Dict[str, Any]] = []
        self.daily_pnl = 0.0
        self.position_counter = 0
        
        logger.info("🚀 ENHANCED TRADING SYSTEM INITIALIZED")
        logger.info(f"   Starting Balance: ${self.config.account_balance:,.2f}")
        logger.info(f"   Daily Target: ${self.config.max_daily_profit}")
        logger.info(f"   Max Daily Loss: ${self.config.max_daily_loss}")
    
    def start_trading_day(self, date: datetime) -> None:
        """
        Start new trading day with risk reset
        
        Implements daily reset patterns from ChatGPT repo's
        daily trading cycle management.
        """
        
        current_balance = self.equity_curve[-1]
        self.risk_manager.reset_daily_metrics(current_balance)
        self.daily_pnl = 0.0
        
        logger.info(f"📅 TRADING DAY STARTED: {date.date()}")
        logger.info(f"   Starting Balance: ${current_balance:,.2f}")
        
        # Display risk dashboard
        self.risk_manager.print_risk_dashboard(current_balance)
    
    def evaluate_trade_opportunity(self, 
                                 options_data: pd.DataFrame,
                                 spy_price: float,
                                 market_regime: str,
                                 current_time: datetime,
                                 vix_level: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        Comprehensive trade evaluation with all safety checks
        
        Integrates all three modules for complete trade analysis:
        1. Generate signal using existing system
        2. Validate trade using Trade Validator
        3. Check risk limits using Risk Manager
        4. Execute if all checks pass
        """
        
        logger.info(f"🔍 EVALUATING TRADE OPPORTUNITY")
        logger.info(f"   SPY Price: ${spy_price:.2f}")
        logger.info(f"   Market Regime: {market_regime}")
        logger.info(f"   Time: {current_time.strftime('%H:%M:%S')}")
        
        # Step 1: Generate trade signal using existing system
        trade_signal = self.trading_system.generate_trade_signal(
            options_data=options_data,
            spy_price=spy_price,
            market_regime=market_regime,
            current_time=current_time
        )
        
        if not trade_signal:
            logger.info("   ❌ No trade signal generated")
            return None
        
        logger.info(f"   ✅ Trade signal generated: {trade_signal.spread_type.value}")
        logger.info(f"   Contracts: {trade_signal.contracts}")
        logger.info(f"   Premium: ${trade_signal.premium_collected:.2f}")
        logger.info(f"   Max Risk: ${trade_signal.max_risk:.2f}")
        
        # Step 2: Validate trade using Trade Validator
        current_balance = self.equity_curve[-1]
        available_cash = current_balance - sum(
            pos.max_risk for pos in self.risk_manager.positions.values()
        )
        
        validation_request = TradeValidationRequest(
            strategy_type=trade_signal.spread_type.value,
            contracts=trade_signal.contracts,
            premium_collected=trade_signal.premium_collected,
            max_risk=trade_signal.max_risk,
            max_profit=trade_signal.max_profit,
            spy_price=spy_price,
            market_regime=market_regime,
            current_balance=current_balance,
            available_cash=available_cash,
            current_positions=len(self.risk_manager.positions),
            daily_pnl=self.daily_pnl,
            current_time=current_time,
            vix_level=vix_level,
            short_strike=trade_signal.short_strike,
            long_strike=trade_signal.long_strike,
            confidence_score=trade_signal.confidence
        )
        
        validation_response = self.trade_validator.validate_trade(validation_request)
        
        logger.info(f"   📋 Trade Validation: {validation_response.overall_result.value}")
        logger.info(f"   Approved: {validation_response.approved}")
        logger.info(f"   Confidence: {validation_response.confidence_level:.1%}")
        
        if not validation_response.approved:
            logger.warning(f"   ❌ Trade rejected: {validation_response.summary_message}")
            return None
        
        # Step 3: Final risk check using Risk Manager
        is_valid, risk_reason = self.risk_manager.validate_new_position(
            strategy_type=trade_signal.spread_type.value,
            contracts=trade_signal.contracts,
            premium_collected=trade_signal.premium_collected,
            max_risk=trade_signal.max_risk,
            current_balance=current_balance
        )
        
        if not is_valid:
            logger.warning(f"   ❌ Risk check failed: {risk_reason}")
            return None
        
        logger.info(f"   ✅ All checks passed - Trade approved for execution")
        
        # Use recommended position size if available
        final_contracts = validation_response.recommended_contracts or trade_signal.contracts
        
        return {
            'trade_signal': trade_signal,
            'validation_response': validation_response,
            'final_contracts': final_contracts,
            'approved': True
        }
    
    def execute_trade(self, trade_opportunity: Dict[str, Any]) -> str:
        """
        Execute approved trade with full tracking
        
        Implements trade execution with comprehensive logging
        similar to ChatGPT repo's trade management system.
        """
        
        trade_signal = trade_opportunity['trade_signal']
        final_contracts = trade_opportunity['final_contracts']
        
        # Generate unique position ID
        self.position_counter += 1
        position_id = f"{trade_signal.spread_type.value}_{self.position_counter:03d}"
        
        # Add to risk monitoring
        self.risk_manager.add_position(
            position_id=position_id,
            strategy_type=trade_signal.spread_type.value,
            contracts=final_contracts,
            premium_collected=trade_signal.premium_collected,
            max_risk=trade_signal.max_risk,
            max_profit=trade_signal.max_profit,
            entry_time=trade_signal.entry_time
        )
        
        # Record trade
        trade_record = {
            'position_id': position_id,
            'entry_time': trade_signal.entry_time,
            'strategy_type': trade_signal.spread_type.value,
            'contracts': final_contracts,
            'premium_collected': trade_signal.premium_collected,
            'max_risk': trade_signal.max_risk,
            'max_profit': trade_signal.max_profit,
            'short_strike': trade_signal.short_strike,
            'long_strike': trade_signal.long_strike,
            'confidence': trade_signal.confidence,
            'status': 'OPEN'
        }
        
        self.trade_history.append(trade_record)
        
        logger.info(f"🎯 TRADE EXECUTED: {position_id}")
        logger.info(f"   Strategy: {trade_signal.spread_type.value}")
        logger.info(f"   Contracts: {final_contracts}")
        logger.info(f"   Premium Collected: ${trade_signal.premium * final_contracts:.2f}")
        
        return position_id
    
    def monitor_positions(self, current_spy_price: float, 
                         current_time: datetime) -> List[str]:
        """
        Monitor all open positions for exit signals
        
        Implements position monitoring from ChatGPT repo's
        automated stop-loss and profit-taking system.
        """
        
        actions_taken = []
        
        for position_id, position in list(self.risk_manager.positions.items()):
            
            # Simulate current P&L (simplified for example)
            # In real system, this would calculate actual option values
            time_decay_factor = 0.95  # Simplified time decay
            current_pnl = position.current_value * time_decay_factor - position.current_value
            
            # Update position and check for triggers
            action = self.risk_manager.update_position_pnl(position_id, current_pnl)
            
            if action in ['STOP_LOSS', 'PROFIT_TARGET']:
                # Close position
                self.close_position(position_id, current_pnl, action, current_time)
                actions_taken.append(f"{position_id}: {action}")
        
        return actions_taken
    
    def close_position(self, position_id: str, final_pnl: float, 
                      reason: str, close_time: datetime) -> None:
        """
        Close position with full tracking
        
        Implements position closure from ChatGPT repo's
        trade management system.
        """
        
        # Update risk manager
        self.risk_manager.close_position(position_id, final_pnl, reason)
        
        # Update daily P&L
        self.daily_pnl += final_pnl
        
        # Update equity curve
        current_balance = self.equity_curve[-1] + final_pnl
        self.equity_curve.append(current_balance)
        
        # Update trade history
        for trade in self.trade_history:
            if trade['position_id'] == position_id:
                trade['close_time'] = close_time
                trade['final_pnl'] = final_pnl
                trade['close_reason'] = reason
                trade['status'] = 'CLOSED'
                break
        
        logger.info(f"📊 POSITION CLOSED: {position_id}")
        logger.info(f"   Final P&L: ${final_pnl:+.2f}")
        logger.info(f"   Reason: {reason}")
        logger.info(f"   Daily P&L: ${self.daily_pnl:+.2f}")
    
    def end_trading_day(self, date: datetime) -> Dict[str, Any]:
        """
        End trading day with comprehensive analysis
        
        Implements end-of-day analysis from ChatGPT repo's
        daily results system.
        """
        
        current_balance = self.equity_curve[-1]
        
        # Check daily limits
        within_limits, limit_message = self.risk_manager.check_daily_limits()
        
        # Generate daily summary
        daily_summary = {
            'date': date.date(),
            'starting_balance': self.equity_curve[-2] if len(self.equity_curve) > 1 else self.config.account_balance,
            'ending_balance': current_balance,
            'daily_pnl': self.daily_pnl,
            'daily_return_pct': (self.daily_pnl / self.equity_curve[-2]) * 100 if len(self.equity_curve) > 1 else 0.0,
            'trades_executed': len([t for t in self.trade_history if t['entry_time'].date() == date.date()]),
            'within_limits': within_limits,
            'limit_message': limit_message
        }
        
        logger.info(f"📅 TRADING DAY ENDED: {date.date()}")
        logger.info(f"   Daily P&L: ${self.daily_pnl:+.2f}")
        logger.info(f"   Daily Return: {daily_summary['daily_return_pct']:+.2f}%")
        logger.info(f"   Trades: {daily_summary['trades_executed']}")
        logger.info(f"   Ending Balance: ${current_balance:,.2f}")
        
        return daily_summary
    
    def generate_performance_report(self) -> PerformanceMetrics:
        """
        Generate comprehensive performance report
        
        Uses the enhanced Performance Analytics module for
        institutional-grade performance analysis.
        """
        
        if len(self.equity_curve) < 2:
            logger.warning("Insufficient data for performance analysis")
            return self.performance_analyzer._get_empty_metrics()
        
        # Create equity curve series
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=len(self.equity_curve)-1),
            periods=len(self.equity_curve),
            freq='D'
        )
        equity_series = pd.Series(self.equity_curve, index=dates)
        
        # Extract trade P&Ls
        trade_pnls = [
            trade['final_pnl'] for trade in self.trade_history 
            if trade['status'] == 'CLOSED' and 'final_pnl' in trade
        ]
        
        # Generate comprehensive analysis
        metrics = self.performance_analyzer.analyze_performance(
            equity_curve=equity_series,
            trade_pnls=trade_pnls,
            benchmark_symbols=['SPY']  # Compare to SPY
        )
        
        return metrics
    
    def print_comprehensive_dashboard(self) -> None:
        """
        Print comprehensive trading dashboard
        
        Combines all three modules for complete system overview
        similar to ChatGPT repo's comprehensive reporting.
        """
        
        current_balance = self.equity_curve[-1] if self.equity_curve else self.config.account_balance
        
        print("\n" + "=" * 80)
        print("🚀 ENHANCED 0DTE TRADING SYSTEM DASHBOARD")
        print("=" * 80)
        
        # System Overview
        print(f"\n📊 SYSTEM OVERVIEW:")
        print(f"   Current Balance: ${current_balance:,.2f}")
        print(f"   Total Return: {((current_balance / self.config.account_balance) - 1) * 100:+.2f}%")
        print(f"   Total Trades: {len(self.trade_history)}")
        print(f"   Open Positions: {len(self.risk_manager.positions)}")
        print(f"   Daily P&L: ${self.daily_pnl:+.2f}")
        
        # Risk Management Dashboard
        self.risk_manager.print_risk_dashboard(current_balance)
        
        # Performance Analytics
        if len(self.equity_curve) >= 2:
            print(f"\n📈 PERFORMANCE ANALYTICS:")
            metrics = self.generate_performance_report()
            self.performance_analyzer.print_performance_report(metrics)
        
        # Recent Trades
        if self.trade_history:
            print(f"\n📋 RECENT TRADES:")
            recent_trades = self.trade_history[-5:]  # Last 5 trades
            for trade in recent_trades:
                status_emoji = "🟢" if trade['status'] == 'CLOSED' and trade.get('final_pnl', 0) > 0 else "🔴" if trade['status'] == 'CLOSED' else "🟡"
                pnl_str = f"${trade.get('final_pnl', 0):+.2f}" if 'final_pnl' in trade else "OPEN"
                print(f"   {status_emoji} {trade['position_id']}: {trade['strategy_type']} - {pnl_str}")

def run_integration_example():
    """
    Complete integration example
    
    Demonstrates how all three ChatGPT repo modules work together
    in a realistic 0DTE trading scenario.
    """
    
    print("🚀 CHATGPT MICRO-CAP INTEGRATION EXAMPLE")
    print("=" * 60)
    print("Demonstrating integration of:")
    print("1. Risk Manager - Automated risk controls")
    print("2. Performance Analytics - Advanced metrics")
    print("3. Trade Validator - Pre-trade safety checks")
    print("=" * 60)
    
    # Initialize enhanced trading system
    config = ProfessionalConfig()
    trading_system = EnhancedTradingSystem(config)
    
    # Simulate a trading day
    trading_date = datetime(2024, 1, 15, 10, 0)
    trading_system.start_trading_day(trading_date)
    
    # Simulate market data
    spy_price = 475.50
    market_regime = "BULLISH"
    vix_level = 16.5
    
    # Create mock options data
    options_data = pd.DataFrame({
        'strike': [470, 471, 472, 473, 474, 475, 476, 477, 478, 479, 480],
        'call_bid': [5.50, 4.75, 4.00, 3.25, 2.50, 1.75, 1.25, 0.85, 0.55, 0.35, 0.20],
        'call_ask': [5.75, 5.00, 4.25, 3.50, 2.75, 2.00, 1.50, 1.00, 0.70, 0.45, 0.30],
        'put_bid': [0.20, 0.35, 0.55, 0.85, 1.25, 1.75, 2.50, 3.25, 4.00, 4.75, 5.50],
        'put_ask': [0.30, 0.45, 0.70, 1.00, 1.50, 2.00, 2.75, 3.50, 4.25, 5.00, 5.75],
        'volume': [1000, 1200, 1500, 1800, 2000, 2200, 1800, 1500, 1200, 1000, 800]
    })
    
    # Evaluate trade opportunity
    trade_opportunity = trading_system.evaluate_trade_opportunity(
        options_data=options_data,
        spy_price=spy_price,
        market_regime=market_regime,
        current_time=trading_date,
        vix_level=vix_level
    )
    
    if trade_opportunity and trade_opportunity['approved']:
        # Execute the trade
        position_id = trading_system.execute_trade(trade_opportunity)
        
        # Simulate some time passing and position monitoring
        later_time = trading_date + timedelta(hours=2)
        actions = trading_system.monitor_positions(spy_price + 1.50, later_time)
        
        if actions:
            print(f"\n📊 Position Actions Taken: {actions}")
    
    # End trading day
    daily_summary = trading_system.end_trading_day(trading_date)
    
    # Display comprehensive dashboard
    trading_system.print_comprehensive_dashboard()
    
    print(f"\n🎉 INTEGRATION EXAMPLE COMPLETED!")
    print(f"   This example shows how all three ChatGPT repo modules")
    print(f"   work together to create a comprehensive trading system")
    print(f"   with institutional-grade risk management and analytics.")

if __name__ == "__main__":
    """Run the complete integration example"""
    run_integration_example()
