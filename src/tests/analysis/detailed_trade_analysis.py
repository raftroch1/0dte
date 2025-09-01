#!/usr/bin/env python3
"""
DETAILED TRADE-BY-TRADE ANALYSIS - FIND THE EXACT BUG
====================================================

This script analyzes EVERY SINGLE TRADE to find the exact discrepancy
Following @.cursorrules - detailed analysis of real data
"""

import pandas as pd
import sys
import os

def analyze_detailed_trades():
    """Analyze every single trade to find the exact bug"""
    
    print("🔍 DETAILED TRADE-BY-TRADE ANALYSIS")
    print("="*80)
    print("Following @.cursorrules - analyzing REAL trade data")
    print()
    
    # Load the detailed logs
    try:
        trades_df = pd.read_csv('logs/trades_20250831_170556.csv')
        balance_df = pd.read_csv('logs/balance_progression_20250831_170556.csv')
        
        print(f"✅ Loaded {len(trades_df)} trades and {len(balance_df)} balance entries")
    except Exception as e:
        print(f"❌ Error loading logs: {e}")
        return
    
    print("\n🔍 CRITICAL BUG ANALYSIS:")
    print("="*50)
    
    # Analyze each trade individually
    print("\n📊 TRADE-BY-TRADE BREAKDOWN:")
    print("-" * 100)
    print(f"{'Trade ID':<20} {'Entry Cost':<12} {'Exit P&L':<12} {'Net P&L':<12} {'Balance Before':<15} {'Balance After':<15} {'Expected After':<15} {'Discrepancy':<12}")
    print("-" * 100)
    
    total_discrepancy = 0
    duplicate_entries = 0
    
    for _, trade in trades_df.iterrows():
        trade_id = trade['trade_id']
        entry_cost = trade['cash_used']
        exit_pnl = trade['realized_pnl']
        balance_before = trade['account_balance_before']
        balance_after = trade['account_balance_after']
        
        # Calculate expected balance after trade
        expected_after = balance_before + exit_pnl  # This should be: balance_before - entry_cost + exit_pnl
        # But we already deducted entry_cost when opening, so exit_pnl should be net
        
        discrepancy = balance_after - expected_after
        total_discrepancy += discrepancy
        
        print(f"{trade_id:<20} ${entry_cost:<11.2f} ${exit_pnl:<11.2f} ${exit_pnl:<11.2f} ${balance_before:<14.2f} ${balance_after:<14.2f} ${expected_after:<14.2f} ${discrepancy:<11.2f}")
    
    print("-" * 100)
    print(f"TOTAL DISCREPANCY: ${total_discrepancy:+,.2f}")
    
    # Analyze balance progression for duplicates
    print(f"\n🔍 BALANCE PROGRESSION ANALYSIS:")
    print("-" * 80)
    
    duplicate_count = 0
    prev_entry = None
    
    for _, entry in balance_df.iterrows():
        if prev_entry is not None:
            # Check for duplicate entries (same timestamp, same change, same reason)
            if (entry['timestamp'] == prev_entry['timestamp'] and 
                entry['change'] == prev_entry['change'] and 
                entry['reason'] == prev_entry['reason']):
                duplicate_count += 1
                print(f"🚨 DUPLICATE: {entry['timestamp']} - {entry['reason']} - ${entry['change']:+.2f}")
        
        prev_entry = entry
    
    print(f"\n📊 DUPLICATE ANALYSIS:")
    print(f"   Total Duplicates Found: {duplicate_count}")
    print(f"   Duplicate Impact: ${duplicate_count * 0:+,.2f}")  # Will calculate actual impact
    
    # Calculate the REAL impact of duplicates
    duplicate_impact = 0
    seen_entries = set()
    
    for _, entry in balance_df.iterrows():
        entry_key = f"{entry['timestamp']}_{entry['reason']}_{entry['change']}"
        
        if entry_key in seen_entries:
            # This is a duplicate - it shouldn't have been applied
            duplicate_impact += entry['change']
            print(f"   DUPLICATE IMPACT: {entry['reason']} - ${entry['change']:+.2f}")
        else:
            seen_entries.add(entry_key)
    
    print(f"\n🎯 ROOT CAUSE ANALYSIS:")
    print("="*50)
    print(f"Total Discrepancy: ${total_discrepancy:+,.2f}")
    print(f"Duplicate Impact: ${duplicate_impact:+,.2f}")
    print(f"Remaining Unexplained: ${total_discrepancy - duplicate_impact:+,.2f}")
    
    # Check if duplicates explain the discrepancy
    if abs(duplicate_impact - 2400) < 10:
        print(f"\n✅ BUG IDENTIFIED: DUPLICATE BALANCE ENTRIES!")
        print(f"   The system is logging each exit TWICE")
        print(f"   This creates ${duplicate_impact:+,.2f} in phantom P&L")
        print(f"   Expected: 8 trades × $300 entry = $2,400 discrepancy")
        print(f"   Actual: ${duplicate_impact:+,.2f} duplicate impact")
    else:
        print(f"\n❌ DUPLICATE IMPACT DOESN'T MATCH EXPECTED")
        print(f"   Expected: $2,400 (8 × $300)")
        print(f"   Found: ${duplicate_impact:+,.2f}")
    
    # Detailed balance analysis
    print(f"\n📊 BALANCE FLOW ANALYSIS:")
    print("-" * 60)
    
    initial_balance = 25000.0
    calculated_balance = initial_balance
    
    print(f"Starting Balance: ${initial_balance:,.2f}")
    
    for _, entry in balance_df.iterrows():
        if entry['reason'] != 'INITIAL_BALANCE':
            calculated_balance += entry['change']
            print(f"{entry['timestamp']:<20} {entry['reason']:<35} ${entry['change']:+8.2f} -> ${calculated_balance:8.2f}")
    
    final_balance = balance_df['balance'].iloc[-1]
    
    print(f"\nCalculated Final: ${calculated_balance:,.2f}")
    print(f"Reported Final: ${final_balance:,.2f}")
    print(f"Difference: ${final_balance - calculated_balance:+,.2f}")

def main():
    """Main analysis function"""
    
    analyze_detailed_trades()
    
    print(f"\n🔧 RECOMMENDED FIXES:")
    print("="*30)
    print("1. ✅ Fix duplicate balance logging in _close_position")
    print("2. ✅ Ensure each exit is logged only ONCE")
    print("3. ✅ Add validation to prevent duplicate entries")
    print("4. ✅ Fix the balance update logic")

if __name__ == "__main__":
    main()
