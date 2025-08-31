#!/usr/bin/env python3
"""
Conservative Cash Management for Credit Spreads - $25K Account
============================================================

CRITICAL: Credit spreads require cash collateral equal to max loss
With $25K account, we must be extremely conservative with position sizing

Cash Requirements:
- Bull Put Spread: (Strike Width - Credit) × 100 per contract
- Bear Call Spread: (Strike Width - Credit) × 100 per contract  
- Iron Condor: (Wing Width - Net Credit) × 100 per contract

Location: src/strategies/cash_management/ (following .cursorrules structure)
Author: Advanced Options Trading System - Conservative Cash Management
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

@dataclass
class Position:
    """Represents an open credit spread position"""
    position_id: str
    strategy_type: str  # 'BULL_PUT_SPREAD', 'BEAR_CALL_SPREAD', 'IRON_CONDOR'
    cash_requirement: float
    max_loss: float
    max_profit: float
    entry_date: datetime
    strikes: Dict  # Strike prices for the spread
    
@dataclass
class CashManagementResult:
    """Result of cash management analysis"""
    can_trade: bool
    max_contracts: int
    cash_required: float
    available_cash: float
    reason: str

class ConservativeCashManager:
    """
    Ultra-conservative cash management for $25K account
    
    Key Principles:
    1. Never risk more than 1% per trade ($250)
    2. Keep 20% cash reserve ($5K) for opportunities
    3. Maximum 2 positions open simultaneously
    4. Prefer narrow spreads (1-3 points) over wide spreads
    """
    
    def __init__(self, account_balance: float = 25000):
        self.account_balance = account_balance
        self.open_positions: List[Position] = []
        self.cash_reserve_percent = 0.20  # 20% reserve
        self.max_risk_per_trade_percent = 0.01  # 1% per trade
        self.max_simultaneous_positions = 2
        
        # Logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"💰 CONSERVATIVE CASH MANAGER INITIALIZED")
        self.logger.info(f"   Account Balance: ${self.account_balance:,.2f}")
        self.logger.info(f"   Cash Reserve: {self.cash_reserve_percent*100}% (${self.account_balance * self.cash_reserve_percent:,.2f})")
        self.logger.info(f"   Max Risk/Trade: {self.max_risk_per_trade_percent*100}% (${self.account_balance * self.max_risk_per_trade_percent:,.2f})")
        self.logger.info(f"   Max Positions: {self.max_simultaneous_positions}")
    
    def calculate_available_cash(self) -> float:
        """Calculate available cash for new positions"""
        
        # Cash tied up in current positions
        used_cash = sum(pos.cash_requirement for pos in self.open_positions)
        
        # Reserve cash (20% of account)
        reserve_cash = self.account_balance * self.cash_reserve_percent
        
        # Available for new positions
        available_cash = self.account_balance - used_cash - reserve_cash
        
        return max(0, available_cash)
    
    def can_open_position(
        self, 
        strategy_type: str,
        spread_width: float,
        credit_received: float,
        contracts: int = 1
    ) -> CashManagementResult:
        """
        Check if we can open a new credit spread position
        
        Args:
            strategy_type: 'BULL_PUT_SPREAD', 'BEAR_CALL_SPREAD', 'IRON_CONDOR'
            spread_width: Width of the spread in points
            credit_received: Credit received per contract
            contracts: Number of contracts (default 1)
        """
        
        # Calculate cash requirement
        if strategy_type in ['BULL_PUT_SPREAD', 'BEAR_CALL_SPREAD']:
            cash_per_contract = (spread_width - credit_received) * 100
        elif strategy_type == 'IRON_CONDOR':
            # For Iron Condor, use the wider wing
            cash_per_contract = (spread_width - credit_received) * 100
        else:
            return CashManagementResult(
                can_trade=False,
                max_contracts=0,
                cash_required=0,
                available_cash=self.calculate_available_cash(),
                reason=f"Unknown strategy type: {strategy_type}"
            )
        
        total_cash_required = cash_per_contract * contracts
        max_loss = total_cash_required  # Max loss = cash requirement for credit spreads
        available_cash = self.calculate_available_cash()
        
        # Check 1: Position limit
        if len(self.open_positions) >= self.max_simultaneous_positions:
            return CashManagementResult(
                can_trade=False,
                max_contracts=0,
                cash_required=total_cash_required,
                available_cash=available_cash,
                reason=f"Maximum {self.max_simultaneous_positions} positions already open"
            )
        
        # Check 2: Cash availability
        if total_cash_required > available_cash:
            max_affordable_contracts = int(available_cash / cash_per_contract)
            return CashManagementResult(
                can_trade=max_affordable_contracts > 0,
                max_contracts=max_affordable_contracts,
                cash_required=cash_per_contract,
                available_cash=available_cash,
                reason=f"Insufficient cash: need ${total_cash_required:,.2f}, have ${available_cash:,.2f}"
            )
        
        # Check 3: Risk per trade limit
        max_risk_per_trade = self.account_balance * self.max_risk_per_trade_percent
        if max_loss > max_risk_per_trade:
            max_risk_contracts = int(max_risk_per_trade / cash_per_contract)
            return CashManagementResult(
                can_trade=max_risk_contracts > 0,
                max_contracts=max_risk_contracts,
                cash_required=cash_per_contract,
                available_cash=available_cash,
                reason=f"Risk limit: max ${max_risk_per_trade:.2f} per trade, position risks ${max_loss:.2f}"
            )
        
        # All checks passed
        return CashManagementResult(
            can_trade=True,
            max_contracts=contracts,
            cash_required=total_cash_required,
            available_cash=available_cash,
            reason="Position approved"
        )
    
    def get_optimal_position_size(
        self,
        strategy_type: str,
        spread_width: float,
        credit_received: float,
        target_profit: float = 250  # Target $250/day
    ) -> CashManagementResult:
        """
        Calculate optimal position size for target profit
        
        For $250/day target with credit spreads:
        - Need ~5-10 small profitable trades
        - Each trade targeting $25-50 profit
        - Risk $100-200 per trade maximum
        """
        
        # Calculate profit per contract
        profit_per_contract = credit_received * 100  # Credit in dollars
        
        # Calculate contracts needed for target profit
        if profit_per_contract > 0:
            target_contracts = max(1, int(target_profit / (profit_per_contract * 5)))  # Assume 20% of max profit
        else:
            target_contracts = 1
        
        # Check if we can afford this position size
        result = self.can_open_position(strategy_type, spread_width, credit_received, target_contracts)
        
        if not result.can_trade and result.max_contracts > 0:
            # Use maximum affordable contracts
            result = self.can_open_position(strategy_type, spread_width, credit_received, result.max_contracts)
            result.reason = f"Reduced to {result.max_contracts} contracts due to cash constraints"
        
        return result
    
    def add_position(
        self,
        position_id: str,
        strategy_type: str,
        cash_requirement: float,
        max_loss: float,
        max_profit: float,
        strikes: Dict
    ) -> bool:
        """Add a new position to tracking"""
        
        if len(self.open_positions) >= self.max_simultaneous_positions:
            self.logger.warning(f"Cannot add position: maximum {self.max_simultaneous_positions} positions reached")
            return False
        
        if cash_requirement > self.calculate_available_cash():
            self.logger.warning(f"Cannot add position: insufficient cash (need ${cash_requirement:,.2f})")
            return False
        
        position = Position(
            position_id=position_id,
            strategy_type=strategy_type,
            cash_requirement=cash_requirement,
            max_loss=max_loss,
            max_profit=max_profit,
            entry_date=datetime.now(),
            strikes=strikes
        )
        
        self.open_positions.append(position)
        
        self.logger.info(f"✅ POSITION ADDED: {strategy_type}")
        self.logger.info(f"   Cash Required: ${cash_requirement:,.2f}")
        self.logger.info(f"   Max Loss: ${max_loss:,.2f}")
        self.logger.info(f"   Max Profit: ${max_profit:,.2f}")
        self.logger.info(f"   Available Cash: ${self.calculate_available_cash():,.2f}")
        
        return True
    
    def remove_position(self, position_id: str) -> bool:
        """Remove a position (when closed)"""
        
        for i, pos in enumerate(self.open_positions):
            if pos.position_id == position_id:
                removed_pos = self.open_positions.pop(i)
                
                self.logger.info(f"✅ POSITION CLOSED: {removed_pos.strategy_type}")
                self.logger.info(f"   Cash Freed: ${removed_pos.cash_requirement:,.2f}")
                self.logger.info(f"   Available Cash: ${self.calculate_available_cash():,.2f}")
                
                return True
        
        self.logger.warning(f"Position {position_id} not found")
        return False
    
    def get_position_summary(self) -> Dict:
        """Get summary of current positions and cash usage"""
        
        total_cash_used = sum(pos.cash_requirement for pos in self.open_positions)
        total_max_loss = sum(pos.max_loss for pos in self.open_positions)
        total_max_profit = sum(pos.max_profit for pos in self.open_positions)
        available_cash = self.calculate_available_cash()
        
        return {
            'account_balance': self.account_balance,
            'open_positions': len(self.open_positions),
            'total_cash_used': total_cash_used,
            'available_cash': available_cash,
            'cash_utilization_pct': (total_cash_used / self.account_balance) * 100,
            'total_max_loss': total_max_loss,
            'total_max_profit': total_max_profit,
            'positions': [
                {
                    'id': pos.position_id,
                    'type': pos.strategy_type,
                    'cash_requirement': pos.cash_requirement,
                    'max_loss': pos.max_loss,
                    'max_profit': pos.max_profit,
                    'strikes': pos.strikes
                }
                for pos in self.open_positions
            ]
        }
    
    def suggest_spread_parameters(self, current_price: float) -> Dict:
        """
        Suggest conservative spread parameters for $25K account
        
        Focus on narrow spreads with good risk/reward
        """
        
        suggestions = {
            'BULL_PUT_SPREAD': {
                'spread_width': 2.0,  # $2 wide spread
                'short_strike_distance': current_price * 0.02,  # 2% OTM
                'target_credit': 0.40,  # $40 credit per contract
                'max_contracts': 3,
                'cash_requirement_estimate': 160,  # ($2 - $0.40) × 100
                'rationale': 'Conservative 2-point spread, 2% OTM for safety'
            },
            'BEAR_CALL_SPREAD': {
                'spread_width': 2.0,  # $2 wide spread  
                'short_strike_distance': current_price * 0.02,  # 2% OTM
                'target_credit': 0.35,  # $35 credit per contract
                'max_contracts': 3,
                'cash_requirement_estimate': 165,  # ($2 - $0.35) × 100
                'rationale': 'Conservative 2-point spread, 2% OTM for safety'
            },
            'IRON_CONDOR': {
                'wing_width': 2.0,  # $2 wings
                'short_strike_distance': current_price * 0.03,  # 3% OTM each side
                'target_net_credit': 0.60,  # $60 net credit
                'max_contracts': 2,
                'cash_requirement_estimate': 280,  # ($2 - $0.60) × 100 × 2 wings
                'rationale': 'Conservative 2-point wings, 3% OTM for wider profit zone'
            }
        }
        
        return suggestions

def main():
    """Test the cash management system"""
    
    print("🏦 TESTING CONSERVATIVE CASH MANAGEMENT")
    print("=" * 60)
    
    # Initialize with $25K account
    cash_manager = ConservativeCashManager(25000)
    
    # Test Bull Put Spread
    print(f"\n📊 TESTING BULL PUT SPREAD:")
    result = cash_manager.can_open_position('BULL_PUT_SPREAD', 2.0, 0.40, 1)
    print(f"   Can Trade: {result.can_trade}")
    print(f"   Max Contracts: {result.max_contracts}")
    print(f"   Cash Required: ${result.cash_required:,.2f}")
    print(f"   Available Cash: ${result.available_cash:,.2f}")
    print(f"   Reason: {result.reason}")
    
    # Test position sizing
    print(f"\n📊 OPTIMAL POSITION SIZING:")
    optimal = cash_manager.get_optimal_position_size('BULL_PUT_SPREAD', 2.0, 0.40)
    print(f"   Optimal Contracts: {optimal.max_contracts}")
    print(f"   Total Cash Required: ${optimal.cash_required:,.2f}")
    
    # Test spread suggestions
    print(f"\n📊 SPREAD SUGGESTIONS (SPY @ $640):")
    suggestions = cash_manager.suggest_spread_parameters(640.0)
    for strategy, params in suggestions.items():
        print(f"   {strategy}:")
        print(f"     Width: ${params['spread_width']}")
        print(f"     Target Credit: ${params['target_credit']}")
        print(f"     Max Contracts: {params['max_contracts']}")
        print(f"     Cash Est: ${params['cash_requirement_estimate']}")

if __name__ == "__main__":
    main()
