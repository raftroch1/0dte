#!/usr/bin/env python3
"""
INVESTIGATE MASSIVE $58K DISCREPANCY
===================================

Following @.cursorrules - ZERO TOLERANCE for accounting errors!
We have a $58,650 discrepancy that must be found and fixed!
"""

import pandas as pd
import sys
import os

def investigate_massive_discrepancy():
    """Investigate the massive $58,650 discrepancy"""
    
    print("🚨 INVESTIGATING MASSIVE $58,650 DISCREPANCY")
    print("="*80)
    print("Following @.cursorrules - ZERO TOLERANCE for accounting errors!")
    print()
    
    # Load the latest logs
    try:
        trades_df = pd.read_csv('logs/trades_20250831_175406.csv')
        balance_df = pd.read_csv('logs/balance_progression_20250831_175406.csv')
        
        print(f"✅ Loaded {len(trades_df)} trades and {len(balance_df)} balance entries")
    except Exception as e:
        print(f"❌ Error loading logs: {e}")
        return
    
    print(f"\n🔍 BASIC DISCREPANCY ANALYSIS:")
    print("="*50)
    
    # Calculate totals
    initial_balance = 25000.0
    final_balance = balance_df['balance'].iloc[-1]
    actual_pnl = final_balance - initial_balance
    
    # Sum individual trade P&L
    trade_pnl_sum = trades_df['realized_pnl'].sum()
    
    # Count entries vs exits
    total_trades = len(trades_df)
    completed_trades = len(trades_df[trades_df['realized_pnl'] != 0])
    backtest_end_trades = len(trades_df[trades_df['exit_reason'] == 'BACKTEST_END'])
    
    print(f"Initial Balance: ${initial_balance:,.2f}")
    print(f"Final Balance: ${final_balance:,.2f}")
    print(f"Actual P&L: ${actual_pnl:+,.2f}")
    print(f"Trade P&L Sum: ${trade_pnl_sum:+,.2f}")
    print(f"Discrepancy: ${trade_pnl_sum - actual_pnl:+,.2f}")
    print(f"Total Trades: {total_trades}")
    print(f"Completed Trades: {completed_trades}")
    print(f"Backtest End Trades: {backtest_end_trades}")
    
    # Analyze entry costs
    print(f"\n🔍 ENTRY COST ANALYSIS:")
    print("="*40)
    
    total_entry_costs = trades_df['cash_used'].sum()
    print(f"Total Entry Costs: ${total_entry_costs:,.2f}")
    print(f"Expected Impact: -${total_entry_costs:,.2f}")
    
    # Check if the discrepancy matches entry costs pattern
    expected_discrepancy = total_trades * 300  # If each trade has $300 entry cost
    print(f"Expected Discrepancy (if $300 per trade): ${expected_discrepancy:,.2f}")
    print(f"Actual Discrepancy: ${trade_pnl_sum - actual_pnl:,.2f}")
    
    # Analyze balance entries
    print(f"\n🔍 BALANCE ENTRY ANALYSIS:")
    print("="*40)
    
    entry_balance_changes = balance_df[balance_df['reason'].str.contains('ENTRY')]['change'].sum()
    exit_balance_changes = balance_df[balance_df['reason'].str.contains('EXIT')]['change'].sum()
    
    print(f"Total Entry Balance Changes: ${entry_balance_changes:+,.2f}")
    print(f"Total Exit Balance Changes: ${exit_balance_changes:+,.2f}")
    print(f"Net Balance Change: ${entry_balance_changes + exit_balance_changes:+,.2f}")
    print(f"Should Equal Actual P&L: ${actual_pnl:+,.2f}")
    
    # Check for the root cause
    print(f"\n🎯 ROOT CAUSE ANALYSIS:")
    print("="*40)
    
    # The issue might be that we're reporting EXIT VALUE instead of NET P&L
    # For option buying: Net P&L = Exit Value - Entry Cost
    # But if we're reporting Exit Value as P&L, we get inflated numbers
    
    print(f"HYPOTHESIS: Trade P&L is reporting EXIT VALUES, not NET P&L")
    print(f"If true, then:")
    print(f"  - Trade P&L Sum: ${trade_pnl_sum:+,.2f} (exit values)")
    print(f"  - Total Entry Costs: ${total_entry_costs:,.2f}")
    print(f"  - Correct Net P&L: ${trade_pnl_sum - total_entry_costs:+,.2f}")
    print(f"  - Actual P&L: ${actual_pnl:+,.2f}")
    print(f"  - Difference: ${(trade_pnl_sum - total_entry_costs) - actual_pnl:+,.2f}")
    
    corrected_pnl = trade_pnl_sum - total_entry_costs
    if abs(corrected_pnl - actual_pnl) < 100:  # Within $100
        print(f"\n✅ ROOT CAUSE CONFIRMED!")
        print(f"   Trade P&L is reporting EXIT VALUES, not NET P&L")
        print(f"   The system is double-counting entry costs")
        print(f"   Balance tracking is CORRECT")
        print(f"   Trade P&L reporting is WRONG")
    else:
        print(f"\n❌ HYPOTHESIS INCORRECT - DEEPER INVESTIGATION NEEDED")
    
    # Sample a few trades to verify
    print(f"\n🔍 SAMPLE TRADE ANALYSIS:")
    print("="*50)
    
    sample_trades = trades_df.head(5)
    for _, trade in sample_trades.iterrows():
        trade_id = trade['trade_id']
        cash_used = trade['cash_used']
        realized_pnl = trade['realized_pnl']
        
        print(f"{trade_id}:")
        print(f"  Entry Cost: ${cash_used:.2f}")
        print(f"  Reported P&L: ${realized_pnl:+.2f}")
        print(f"  If P&L is exit value, Net P&L should be: ${realized_pnl - cash_used:+.2f}")
    
    # Check the balance progression for these trades
    print(f"\n🔍 BALANCE PROGRESSION VERIFICATION:")
    print("="*50)
    
    for _, trade in sample_trades.iterrows():
        trade_id = trade['trade_id']
        strategy_type = trade['strategy_type']
        
        # Find entry and exit balance changes
        entry_reason = f"{strategy_type}_ENTRY_{trade_id}"
        exit_reason = f"{strategy_type}_EXIT_{trade_id}"
        
        entry_balance = balance_df[balance_df['reason'] == entry_reason]
        exit_balance = balance_df[balance_df['reason'] == exit_reason]
        
        if len(entry_balance) == 1 and len(exit_balance) == 1:
            entry_change = entry_balance['change'].iloc[0]
            exit_change = exit_balance['change'].iloc[0]
            net_balance_change = entry_change + exit_change
            
            print(f"{trade_id}:")
            print(f"  Entry Change: ${entry_change:+.2f}")
            print(f"  Exit Change: ${exit_change:+.2f}")
            print(f"  Net Balance Change: ${net_balance_change:+.2f}")
            print(f"  Reported P&L: ${trade['realized_pnl']:+.2f}")
            print(f"  Difference: ${trade['realized_pnl'] - net_balance_change:+.2f}")

def main():
    """Main investigation function"""
    
    investigate_massive_discrepancy()
    
    print(f"\n🔧 REQUIRED FIXES:")
    print("="*30)
    print("1. ✅ Identify if trade P&L is reporting exit values vs net P&L")
    print("2. ✅ Fix the P&L calculation in _should_close_position")
    print("3. ✅ Ensure trade P&L = exit_value - entry_cost")
    print("4. ✅ Validate that balance tracking remains correct")
    print("5. ✅ Re-run backtest to confirm fix")

if __name__ == "__main__":
    main()
