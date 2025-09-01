#!/usr/bin/env python3
"""
Cash Flow Audit - Critical Accounting Bug Investigation
======================================================

CRITICAL DISCREPANCY IDENTIFIED:
- Strategy P&L Summary: +$7,744.08 (BUY_CALL: +$6,020.98, BUY_PUT: +$1,656.59, IRON_CONDOR: +$66.51)
- Actual Account Loss: -$4,705.92 (Final: $20,294.08 vs Initial: $25,000.00)
- MISSING MONEY: $12,450.00

This script audits the cash flow to identify the accounting bug.
"""

import pandas as pd
import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def audit_cash_flows():
    """Audit cash flows from detailed logs to find the accounting bug"""
    
    print("🔍 CASH FLOW AUDIT - CRITICAL ACCOUNTING BUG INVESTIGATION")
    print("="*80)
    
    # Load the logs
    try:
        trades_df = pd.read_csv('logs/trades_20250831_163409.csv')
        balance_df = pd.read_csv('logs/balance_progression_20250831_163409.csv')
        
        print(f"✅ Loaded {len(trades_df)} trades and {len(balance_df)} balance entries")
    except Exception as e:
        print(f"❌ Error loading logs: {e}")
        return
    
    print("\n📊 DISCREPANCY ANALYSIS:")
    print("-" * 50)
    
    # Calculate strategy P&L from trades
    completed_trades = trades_df[trades_df['realized_pnl'].notna()]
    
    strategy_pnl_by_type = {}
    for strategy in completed_trades['strategy_type'].unique():
        strategy_trades = completed_trades[completed_trades['strategy_type'] == strategy]
        total_pnl = strategy_trades['realized_pnl'].sum()
        strategy_pnl_by_type[strategy] = total_pnl
        print(f"   {strategy}: ${total_pnl:+,.2f} ({len(strategy_trades)} trades)")
    
    total_strategy_pnl = sum(strategy_pnl_by_type.values())
    print(f"\n📊 TOTAL STRATEGY P&L: ${total_strategy_pnl:+,.2f}")
    
    # Calculate actual account change
    initial_balance = 25000.00
    final_balance = balance_df['balance'].iloc[-1]
    actual_pnl = final_balance - initial_balance
    
    print(f"📊 ACTUAL ACCOUNT P&L: ${actual_pnl:+,.2f}")
    print(f"   Initial: ${initial_balance:,.2f}")
    print(f"   Final: ${final_balance:,.2f}")
    
    # Calculate discrepancy
    discrepancy = total_strategy_pnl - actual_pnl
    print(f"\n🚨 DISCREPANCY: ${discrepancy:+,.2f}")
    print(f"   Strategy P&L: ${total_strategy_pnl:+,.2f}")
    print(f"   Account P&L: ${actual_pnl:+,.2f}")
    print(f"   Missing Money: ${discrepancy:+,.2f}")
    
    print("\n🔍 DETAILED CASH FLOW ANALYSIS:")
    print("-" * 50)
    
    # Analyze balance changes
    balance_df['balance_change'] = balance_df['balance'].diff()
    
    # Group by reason type
    entry_changes = balance_df[balance_df['reason'].str.contains('ENTRY', na=False)]
    exit_changes = balance_df[balance_df['reason'].str.contains('EXIT', na=False)]
    
    total_entries = entry_changes['change'].sum()
    total_exits = exit_changes['change'].sum()
    
    print(f"📊 CASH FLOW BREAKDOWN:")
    print(f"   Total Entry Cash: ${total_entries:+,.2f} (money spent)")
    print(f"   Total Exit Cash: ${total_exits:+,.2f} (money received)")
    print(f"   Net Cash Flow: ${total_entries + total_exits:+,.2f}")
    
    print(f"\n📊 ENTRY/EXIT ANALYSIS:")
    print(f"   Entry Transactions: {len(entry_changes)}")
    print(f"   Exit Transactions: {len(exit_changes)}")
    
    # Check for unmatched entries/exits
    entry_count = len(entry_changes)
    exit_count = len(exit_changes)
    
    if entry_count != exit_count:
        print(f"\n🚨 UNMATCHED TRANSACTIONS:")
        print(f"   Entries: {entry_count}")
        print(f"   Exits: {exit_count}")
        print(f"   Difference: {entry_count - exit_count}")
        
        if entry_count > exit_count:
            print(f"   ❌ {entry_count - exit_count} positions never closed!")
            print(f"   ❌ This explains missing money: positions still open")
    
    # Analyze individual trade cash flows
    print(f"\n🔍 INDIVIDUAL TRADE ANALYSIS:")
    print("-" * 50)
    
    cash_flow_errors = []
    
    for _, trade in completed_trades.iterrows():
        trade_id = trade['trade_id']
        realized_pnl = trade['realized_pnl']
        
        # Find corresponding balance entries
        entry_balance = balance_df[balance_df['reason'].str.contains(f"ENTRY_{trade_id}", na=False)]
        exit_balance = balance_df[balance_df['reason'].str.contains(f"EXIT_{trade_id}", na=False)]
        
        if len(entry_balance) == 1 and len(exit_balance) == 1:
            entry_change = entry_balance['change'].iloc[0]
            exit_change = exit_balance['change'].iloc[0]
            balance_pnl = entry_change + exit_change
            
            # Compare trade P&L vs balance P&L
            pnl_diff = realized_pnl - balance_pnl
            
            if abs(pnl_diff) > 0.01:  # More than 1 cent difference
                cash_flow_errors.append({
                    'trade_id': trade_id,
                    'trade_pnl': realized_pnl,
                    'balance_pnl': balance_pnl,
                    'difference': pnl_diff
                })
    
    if cash_flow_errors:
        print(f"🚨 FOUND {len(cash_flow_errors)} CASH FLOW ERRORS:")
        for error in cash_flow_errors[:5]:  # Show first 5
            print(f"   {error['trade_id']}: Trade P&L ${error['trade_pnl']:+.2f} vs Balance P&L ${error['balance_pnl']:+.2f} (Diff: ${error['difference']:+.2f})")
        
        total_error = sum(error['difference'] for error in cash_flow_errors)
        print(f"\n   TOTAL CASH FLOW ERROR: ${total_error:+,.2f}")
    else:
        print("✅ No individual trade cash flow errors found")
    
    # Check for open positions at end
    print(f"\n🔍 OPEN POSITIONS CHECK:")
    print("-" * 30)
    
    all_trades = trades_df.copy()
    open_trades = all_trades[all_trades['exit_date'].isna()]
    
    if len(open_trades) > 0:
        print(f"🚨 FOUND {len(open_trades)} OPEN POSITIONS:")
        for _, trade in open_trades.iterrows():
            cash_used = trade['cash_used']
            print(f"   {trade['trade_id']}: ${cash_used:.2f} cash tied up")
        
        total_open_cash = open_trades['cash_used'].sum()
        print(f"\n   TOTAL CASH IN OPEN POSITIONS: ${total_open_cash:,.2f}")
        print(f"   ❌ This explains the missing money!")
    else:
        print("✅ No open positions found")
    
    print(f"\n🎯 SUMMARY:")
    print("="*50)
    print(f"Strategy P&L: ${total_strategy_pnl:+,.2f}")
    print(f"Account P&L: ${actual_pnl:+,.2f}")
    print(f"Discrepancy: ${discrepancy:+,.2f}")
    
    if len(open_trades) > 0:
        print(f"\n✅ ROOT CAUSE IDENTIFIED:")
        print(f"   - {len(open_trades)} positions never closed")
        print(f"   - ${total_open_cash:,.2f} cash tied up in open positions")
        print(f"   - Strategy P&L only counts CLOSED trades")
        print(f"   - Account balance reflects ALL cash flows (including open positions)")
    
    return {
        'strategy_pnl': total_strategy_pnl,
        'account_pnl': actual_pnl,
        'discrepancy': discrepancy,
        'open_positions': len(open_trades),
        'cash_in_open_positions': total_open_cash if len(open_trades) > 0 else 0
    }

def main():
    """Main audit function"""
    
    print("🚨 CRITICAL ACCOUNTING BUG INVESTIGATION")
    print("="*60)
    print("ISSUE: Strategy shows +$7,744 profit but account lost -$4,705")
    print("MISSING: $12,450 unaccounted for")
    print()
    
    results = audit_cash_flows()
    
    if results:
        print(f"\n🔧 RECOMMENDED FIXES:")
        print("-" * 30)
        
        if results['open_positions'] > 0:
            print("1. ✅ Close all open positions in backtest")
            print("2. ✅ Fix position exit logic to ensure all trades close")
            print("3. ✅ Add validation to ensure entries = exits")
        
        print("4. ✅ Separate 'realized P&L' from 'unrealized P&L'")
        print("5. ✅ Add cash flow reconciliation checks")
        print("6. ✅ Fix final balance calculation methodology")

if __name__ == "__main__":
    main()
