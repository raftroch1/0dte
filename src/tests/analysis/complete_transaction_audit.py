#!/usr/bin/env python3
"""
COMPLETE TRANSACTION AUDIT - FIND THE $2,400 DISCREPANCY
========================================================

Following @.cursorrules - DETAILED analysis of EVERY SINGLE transaction
NO DISCREPANCY IS ACCEPTABLE - WE NEED PERFECT ACCOUNTING!
"""

import pandas as pd
import sys
import os

def complete_transaction_audit():
    """Audit EVERY SINGLE transaction to find the exact $2,400 discrepancy"""
    
    print("🔍 COMPLETE TRANSACTION AUDIT - ZERO TOLERANCE FOR DISCREPANCIES")
    print("="*90)
    print("Following @.cursorrules - analyzing EVERY SINGLE TRANSACTION")
    print()
    
    # Load the detailed logs
    try:
        trades_df = pd.read_csv('logs/trades_20250831_172009.csv')
        balance_df = pd.read_csv('logs/balance_progression_20250831_172009.csv')
        
        print(f"✅ Loaded {len(trades_df)} trades and {len(balance_df)} balance entries")
    except Exception as e:
        print(f"❌ Error loading logs: {e}")
        return
    
    print("\n🔍 TRANSACTION-BY-TRANSACTION ANALYSIS:")
    print("="*90)
    
    # Manual balance calculation
    initial_balance = 25000.0
    calculated_balance = initial_balance
    
    print(f"{'Step':<4} {'Date/Time':<20} {'Transaction':<35} {'Amount':<12} {'Balance':<12} {'Expected':<12} {'Diff':<8}")
    print("-" * 110)
    
    step = 0
    total_discrepancy = 0
    
    # Process each balance entry
    for _, entry in balance_df.iterrows():
        if entry['reason'] == 'INITIAL_BALANCE':
            continue
            
        step += 1
        timestamp = entry['timestamp']
        reason = entry['reason']
        change = entry['change']
        reported_balance = entry['balance']
        
        # Calculate expected balance
        calculated_balance += change
        
        # Check for discrepancy
        diff = reported_balance - calculated_balance
        total_discrepancy += diff
        
        print(f"{step:<4} {timestamp:<20} {reason:<35} ${change:+8.2f} ${reported_balance:8.2f} ${calculated_balance:8.2f} ${diff:+6.2f}")
    
    print("-" * 110)
    print(f"TOTAL BALANCE DISCREPANCY: ${total_discrepancy:+,.2f}")
    
    # Now analyze the TRADE P&L vs BALANCE CHANGES
    print(f"\n🔍 TRADE P&L vs BALANCE CHANGE ANALYSIS:")
    print("="*90)
    
    print(f"{'Trade ID':<25} {'Entry Cost':<12} {'Exit P&L':<12} {'Net P&L':<12} {'Balance Change':<15} {'Discrepancy':<12}")
    print("-" * 100)
    
    trade_pnl_discrepancy = 0
    
    for _, trade in trades_df.iterrows():
        trade_id = trade['trade_id']
        entry_cost = trade['cash_used']  # What we paid to enter
        exit_pnl = trade['realized_pnl']  # What we got back minus what we paid
        
        # Find the corresponding balance entries
        entry_reason = f"{trade['strategy_type']}_ENTRY_{trade_id}"
        exit_reason = f"{trade['strategy_type']}_EXIT_{trade_id}"
        
        # Get entry balance change
        entry_balance = balance_df[balance_df['reason'] == entry_reason]
        exit_balance = balance_df[balance_df['reason'] == exit_reason]
        
        if len(entry_balance) == 1 and len(exit_balance) == 1:
            entry_change = entry_balance['change'].iloc[0]  # Should be -entry_cost
            exit_change = exit_balance['change'].iloc[0]    # Should be +exit_pnl
            
            # Total balance change for this trade
            total_balance_change = entry_change + exit_change
            
            # The trade P&L should equal the total balance change
            # For option buying: Net P&L = Exit Value - Entry Cost
            # Balance change = -Entry Cost + Exit Value = Net P&L
            
            discrepancy = exit_pnl - total_balance_change
            trade_pnl_discrepancy += discrepancy
            
            print(f"{trade_id:<25} ${entry_cost:<11.2f} ${exit_pnl:<11.2f} ${exit_pnl:<11.2f} ${total_balance_change:<14.2f} ${discrepancy:<11.2f}")
        else:
            print(f"{trade_id:<25} MISSING BALANCE ENTRIES!")
    
    print("-" * 100)
    print(f"TOTAL TRADE P&L DISCREPANCY: ${trade_pnl_discrepancy:+,.2f}")
    
    # DETAILED ENTRY/EXIT ANALYSIS
    print(f"\n🔍 DETAILED ENTRY/EXIT COST ANALYSIS:")
    print("="*90)
    
    print(f"{'Trade ID':<25} {'Entry Cost':<12} {'Entry Change':<12} {'Exit P&L':<12} {'Exit Change':<12} {'Entry Diff':<12} {'Exit Diff':<12}")
    print("-" * 110)
    
    entry_cost_discrepancy = 0
    exit_pnl_discrepancy = 0
    
    for _, trade in trades_df.iterrows():
        trade_id = trade['trade_id']
        entry_cost = trade['cash_used']
        exit_pnl = trade['realized_pnl']
        
        # Find balance entries
        entry_reason = f"{trade['strategy_type']}_ENTRY_{trade_id}"
        exit_reason = f"{trade['strategy_type']}_EXIT_{trade_id}"
        
        entry_balance = balance_df[balance_df['reason'] == entry_reason]
        exit_balance = balance_df[balance_df['reason'] == exit_reason]
        
        if len(entry_balance) == 1 and len(exit_balance) == 1:
            entry_change = entry_balance['change'].iloc[0]
            exit_change = exit_balance['change'].iloc[0]
            
            # Entry change should be -entry_cost
            entry_diff = entry_change - (-entry_cost)
            
            # Exit change should be +exit_pnl
            exit_diff = exit_change - exit_pnl
            
            entry_cost_discrepancy += entry_diff
            exit_pnl_discrepancy += exit_diff
            
            print(f"{trade_id:<25} ${entry_cost:<11.2f} ${entry_change:<11.2f} ${exit_pnl:<11.2f} ${exit_change:<11.2f} ${entry_diff:<11.2f} ${exit_diff:<11.2f}")
    
    print("-" * 110)
    print(f"ENTRY COST DISCREPANCY: ${entry_cost_discrepancy:+,.2f}")
    print(f"EXIT P&L DISCREPANCY: ${exit_pnl_discrepancy:+,.2f}")
    
    # FINAL ANALYSIS
    print(f"\n🎯 ROOT CAUSE ANALYSIS:")
    print("="*50)
    print(f"Expected $2,400 discrepancy (8 trades × $300): ${8 * 300:+,.2f}")
    print(f"Actual trade P&L discrepancy: ${trade_pnl_discrepancy:+,.2f}")
    print(f"Entry cost discrepancy: ${entry_cost_discrepancy:+,.2f}")
    print(f"Exit P&L discrepancy: ${exit_pnl_discrepancy:+,.2f}")
    
    # Check if the discrepancy matches expected pattern
    if abs(trade_pnl_discrepancy - 2400) < 10:
        print(f"\n✅ DISCREPANCY PATTERN IDENTIFIED:")
        print(f"   The $2,400 discrepancy = 8 trades × $300 entry cost")
        print(f"   This suggests trade P&L is NOT including entry costs properly")
        print(f"   Balance tracking is CORRECT")
        print(f"   Trade P&L reporting is WRONG")
    
    # Calculate what the correct trade P&L should be
    print(f"\n🔧 CORRECTED TRADE P&L CALCULATION:")
    print("-" * 60)
    
    corrected_total_pnl = 0
    
    for _, trade in trades_df.iterrows():
        trade_id = trade['trade_id']
        reported_pnl = trade['realized_pnl']
        entry_cost = trade['cash_used']
        
        # The CORRECT P&L should be: Exit Value - Entry Cost
        # But we're reporting: Exit Value (without subtracting entry cost)
        # So correct P&L = reported_pnl - entry_cost
        correct_pnl = reported_pnl - entry_cost
        corrected_total_pnl += correct_pnl
        
        print(f"{trade_id:<25} Reported: ${reported_pnl:+8.2f} Correct: ${correct_pnl:+8.2f}")
    
    print("-" * 60)
    print(f"CORRECTED TOTAL P&L: ${corrected_total_pnl:+,.2f}")
    
    # Compare with actual balance change
    actual_pnl = balance_df['balance'].iloc[-1] - 25000.0
    print(f"ACTUAL BALANCE P&L: ${actual_pnl:+,.2f}")
    print(f"DIFFERENCE: ${corrected_total_pnl - actual_pnl:+,.2f}")
    
    if abs(corrected_total_pnl - actual_pnl) < 1.0:
        print(f"\n🎉 BUG CONFIRMED AND SOLUTION IDENTIFIED!")
        print(f"   The trade P&L calculation is missing entry cost deduction")
        print(f"   Balance tracking is 100% accurate")
        print(f"   Fix: Subtract entry cost from reported P&L in trade calculations")

def main():
    """Main audit function"""
    
    complete_transaction_audit()
    
    print(f"\n🔧 EXACT FIX NEEDED:")
    print("="*30)
    print("In _should_close_position method:")
    print("CURRENT: net_pnl = exit_value - entry_cost")
    print("PROBLEM: This is correct for balance, but trade P&L reporting is wrong")
    print("FIX: Ensure trade P&L properly reflects net result")

if __name__ == "__main__":
    main()
