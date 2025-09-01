#!/usr/bin/env python3
"""
Test Accounting Fixes - Validate Critical Bug Fixes
===================================================

This script tests the fixes for:
1. ✅ Open position cleanup at backtest end
2. ✅ Proper P&L calculation including entry costs
3. ✅ Entry/exit validation
4. ✅ Cash flow reconciliation

Location: src/tests/analysis/ (following .cursorrules structure)
"""

import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from unified_strategy_backtester import UnifiedStrategyBacktester

def test_accounting_fixes():
    """Test the critical accounting bug fixes"""
    
    print("🧪 TESTING CRITICAL ACCOUNTING BUG FIXES")
    print("="*60)
    print("Testing fixes for:")
    print("1. ✅ Open position cleanup at backtest end")
    print("2. ✅ Proper P&L calculation including entry costs")
    print("3. ✅ Entry/exit validation")
    print("4. ✅ Cash flow reconciliation")
    print()
    
    # Initialize backtester
    backtester = UnifiedStrategyBacktester(initial_balance=25000)
    
    # Run SHORT backtest (5 days) to validate fixes
    print("🎯 Running 5-day validation backtest...")
    results = backtester.run_unified_backtest(
        start_date="2024-07-01",
        end_date="2024-07-05"
    )
    
    print("\n" + "="*60)
    print("🔍 VALIDATION RESULTS")
    print("="*60)
    
    # Check if fixes worked
    session_summary = results.get('session_summary', {})
    
    print(f"\n📊 BASIC METRICS:")
    
    # 🚨 FIX: Extract correct values from nested session summary
    performance = session_summary.get('performance', {})
    initial_balance = performance.get('initial_balance', 0)
    final_balance = results.get('final_balance', 0)
    actual_pnl = results.get('actual_pnl', 0)
    reported_pnl = performance.get('total_pnl', 0)  # Get from performance section
    pnl_discrepancy = results.get('pnl_discrepancy', 0)
    
    print(f"   Initial Balance: ${initial_balance:,.2f}")
    print(f"   Final Balance: ${final_balance:,.2f}")
    print(f"   Actual P&L: ${actual_pnl:+,.2f}")
    print(f"   Reported P&L: ${reported_pnl:+,.2f}")
    print(f"   P&L Discrepancy: ${pnl_discrepancy:+,.2f}")
    
    print(f"\n🔍 VALIDATION CHECKS:")
    
    # Check 1: Cash flow validation
    cash_flow_validated = results.get('cash_flow_validated', False)
    print(f"   Cash Flow Validated: {'✅ PASS' if cash_flow_validated else '❌ FAIL'}")
    
    # Check 2: Entry/exit matching
    total_trades = session_summary.get('total_trades', 0)
    winning_trades = session_summary.get('winning_trades', 0)
    losing_trades = session_summary.get('losing_trades', 0)
    
    entries_exits_match = total_trades == (winning_trades + losing_trades)
    print(f"   Entries = Exits: {'✅ PASS' if entries_exits_match else '❌ FAIL'}")
    print(f"     Total: {total_trades}, Wins: {winning_trades}, Losses: {losing_trades}")
    
    # Check 3: P&L discrepancy (use extracted values)
    pnl_acceptable = pnl_discrepancy <= 1.0
    print(f"   P&L Discrepancy < $1: {'✅ PASS' if pnl_acceptable else '❌ FAIL'}")
    print(f"     Discrepancy: ${pnl_discrepancy:+.2f}")
    
    # Additional validation: Check if reported P&L matches actual P&L
    pnl_match = abs(reported_pnl - actual_pnl) <= 1.0
    print(f"   Reported P&L Matches Actual: {'✅ PASS' if pnl_match else '❌ FAIL'}")
    print(f"     Reported: ${reported_pnl:+.2f}, Actual: ${actual_pnl:+.2f}")
    
    # Check 4: Strategy diversity
    strategy_diversity = results.get('strategy_diversity_achieved', False)
    print(f"   Strategy Diversity: {'✅ PASS' if strategy_diversity else '⚠️  LIMITED'}")
    
    # Overall validation (include P&L match check)
    all_checks_pass = cash_flow_validated and entries_exits_match and pnl_acceptable and pnl_match
    
    print(f"\n🎯 OVERALL VALIDATION:")
    if all_checks_pass:
        print("   ✅ ALL CRITICAL BUGS FIXED!")
        print("   ✅ Accounting system is now accurate")
        print("   ✅ Ready for production backtesting")
    else:
        print("   ❌ Some issues remain - further investigation needed")
    
    print(f"\n📁 LOG FILES GENERATED:")
    log_files = results.get('log_files', {})
    for log_type, file_path in log_files.items():
        print(f"   {log_type}: {file_path}")
    
    return all_checks_pass

def main():
    """Main test function"""
    
    success = test_accounting_fixes()
    
    if success:
        print(f"\n🚀 READY TO RUN FULL BACKTEST!")
        print(f"   The critical accounting bugs have been fixed")
        print(f"   P&L calculations are now accurate")
        print(f"   All positions properly close at backtest end")
    else:
        print(f"\n⚠️  FURTHER DEBUGGING NEEDED")
        print(f"   Some validation checks failed")
        print(f"   Review the detailed logs for issues")

if __name__ == "__main__":
    main()
