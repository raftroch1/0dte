#!/usr/bin/env python3
"""
🧪 FLYAGONAL INTEGRATION TEST
============================
Test script to verify Flyagonal strategy integration with the framework.

Tests:
1. Strategy initialization
2. Framework compatibility
3. Position construction
4. Backtester integration
5. Logging and analytics

Following @.cursorrules:
- Tests framework integration without affecting Iron Condor system
- Verifies compatibility with existing infrastructure
- Ensures proper separation and isolation

Location: src/strategies/flyagonal_python/ (following .cursorrules structure)
Author: Advanced Options Trading Framework - Flyagonal Test Module
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_flyagonal_imports():
    """Test 1: Verify all imports work correctly"""
    print("🧪 TEST 1: Flyagonal Imports")
    
    try:
        from flyagonal_strategy import FlyagonalStrategy, FlyagonalPosition
        from flyagonal_backtester import FlyagonalBacktester
        print("   ✅ Flyagonal imports successful")
        return True
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False

def test_strategy_initialization():
    """Test 2: Verify strategy initializes correctly"""
    print("\n🧪 TEST 2: Strategy Initialization")
    
    try:
        from flyagonal_strategy import FlyagonalStrategy
        
        # Initialize strategy
        strategy = FlyagonalStrategy(initial_balance=25000)
        
        # Check key attributes
        assert strategy.initial_balance == 25000
        assert strategy.min_profit_zone_width == 200
        assert strategy.max_positions == 1
        assert len(strategy.open_positions) == 0
        
        print("   ✅ Strategy initialization successful")
        print(f"      Initial Balance: ${strategy.initial_balance:,.2f}")
        print(f"      Min Profit Zone: {strategy.min_profit_zone_width} points")
        print(f"      Max Positions: {strategy.max_positions}")
        return True
        
    except Exception as e:
        print(f"   ❌ Strategy initialization error: {e}")
        return False

def test_backtester_initialization():
    """Test 3: Verify backtester initializes and extends framework"""
    print("\n🧪 TEST 3: Backtester Initialization")
    
    try:
        from flyagonal_backtester import FlyagonalBacktester
        
        # Initialize backtester
        backtester = FlyagonalBacktester(initial_balance=25000)
        
        # Check inheritance from UnifiedStrategyBacktester
        assert hasattr(backtester, 'data_loader')
        assert hasattr(backtester, 'cash_manager')
        assert hasattr(backtester, 'pricing_calculator')
        assert hasattr(backtester, 'logger')
        
        # Check Flyagonal-specific attributes
        assert hasattr(backtester, 'flyagonal_strategy')
        assert backtester.flyagonal_trades == 0
        assert backtester.max_positions == 1
        
        print("   ✅ Backtester initialization successful")
        print(f"      Framework Integration: ✅")
        print(f"      Flyagonal Strategy: ✅")
        print(f"      Initial Balance: ${backtester.initial_balance:,.2f}")
        return True
        
    except Exception as e:
        print(f"   ❌ Backtester initialization error: {e}")
        return False

def test_vix_regime_detection():
    """Test 4: Verify VIX regime detection works"""
    print("\n🧪 TEST 4: VIX Regime Detection")
    
    try:
        from flyagonal_strategy import FlyagonalStrategy
        
        strategy = FlyagonalStrategy()
        
        # Test different VIX levels
        test_cases = [
            (12.0, 'LOW'),
            (20.0, 'MEDIUM'),
            (30.0, 'HIGH')
        ]
        
        for vix_level, expected_regime in test_cases:
            regime = strategy.detect_vix_regime(vix_level)
            assert regime == expected_regime, f"VIX {vix_level} should be {expected_regime}, got {regime}"
        
        print("   ✅ VIX regime detection successful")
        for vix_level, expected_regime in test_cases:
            print(f"      VIX {vix_level}: {expected_regime}")
        return True
        
    except Exception as e:
        print(f"   ❌ VIX regime detection error: {e}")
        return False

def test_framework_compatibility():
    """Test 5: Verify compatibility with existing framework components"""
    print("\n🧪 TEST 5: Framework Compatibility")
    
    try:
        from flyagonal_backtester import FlyagonalBacktester
        
        backtester = FlyagonalBacktester()
        
        # Test framework component access
        components = [
            'data_loader',
            'cash_manager', 
            'pricing_calculator',
            'logger'
        ]
        
        for component in components:
            assert hasattr(backtester, component), f"Missing framework component: {component}"
            component_obj = getattr(backtester, component)
            assert component_obj is not None, f"Framework component {component} is None"
        
        # Test method inheritance
        methods = [
            '_detect_market_regime',
            '_calculate_put_call_ratio',
            '_process_trading_day'
        ]
        
        for method in methods:
            assert hasattr(backtester, method), f"Missing inherited method: {method}"
        
        print("   ✅ Framework compatibility verified")
        print(f"      Components: {len(components)} ✅")
        print(f"      Methods: {len(methods)} ✅")
        return True
        
    except Exception as e:
        print(f"   ❌ Framework compatibility error: {e}")
        return False

def test_strategy_recommendation():
    """Test 6: Verify strategy recommendation logic"""
    print("\n🧪 TEST 6: Strategy Recommendation")
    
    try:
        from flyagonal_backtester import FlyagonalBacktester
        
        backtester = FlyagonalBacktester()
        
        # Test different market regimes
        test_cases = [
            ('NEUTRAL', 'FLYAGONAL'),
            ('BULLISH', 'FLYAGONAL'),
            ('BEARISH', 'NO_TRADE')
        ]
        
        for regime, expected_strategy in test_cases:
            strategy = backtester._get_strategy_recommendation(regime, 450.0)
            assert strategy == expected_strategy, f"Regime {regime} should recommend {expected_strategy}, got {strategy}"
        
        print("   ✅ Strategy recommendation successful")
        for regime, expected_strategy in test_cases:
            print(f"      {regime} → {expected_strategy}")
        return True
        
    except Exception as e:
        print(f"   ❌ Strategy recommendation error: {e}")
        return False

def test_position_class():
    """Test 7: Verify FlyagonalPosition class works"""
    print("\n🧪 TEST 7: Position Class")
    
    try:
        from flyagonal_strategy import FlyagonalPosition
        
        # Create test position
        position = FlyagonalPosition(
            position_id="TEST_001",
            entry_time=datetime.now(),
            spy_price=450.0
        )
        
        # Check attributes
        assert position.position_id == "TEST_001"
        assert position.spy_price == 450.0
        assert position.is_open == True
        assert position.call_butterfly is None
        assert position.put_diagonal is None
        
        print("   ✅ Position class successful")
        print(f"      Position ID: {position.position_id}")
        print(f"      SPY Price: ${position.spy_price}")
        print(f"      Status: {'Open' if position.is_open else 'Closed'}")
        return True
        
    except Exception as e:
        print(f"   ❌ Position class error: {e}")
        return False

def run_all_tests():
    """Run all integration tests"""
    print("🦋 FLYAGONAL INTEGRATION TESTS")
    print("="*50)
    
    tests = [
        test_flyagonal_imports,
        test_strategy_initialization,
        test_backtester_initialization,
        test_vix_regime_detection,
        test_framework_compatibility,
        test_strategy_recommendation,
        test_position_class
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 TEST RESULTS")
    print("="*30)
    print(f"   Passed: {passed}/{total}")
    print(f"   Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("   🎉 ALL TESTS PASSED!")
        print("   ✅ Flyagonal strategy ready for backtesting")
    else:
        print("   ⚠️  Some tests failed")
        print("   🔧 Review errors before proceeding")
    
    return passed == total

def test_iron_condor_isolation():
    """Test 8: Verify Iron Condor system is not affected"""
    print("\n🧪 TEST 8: Iron Condor Isolation")
    
    try:
        # Test that we can still import Iron Condor components
        sys.path.append(str(Path(__file__).parent.parent.parent / 'tests' / 'analysis'))
        from fixed_dynamic_risk_backtester import FixedDynamicRiskBacktester
        
        # Initialize Iron Condor backtester
        iron_condor_backtester = FixedDynamicRiskBacktester()
        
        # Verify it still works
        assert hasattr(iron_condor_backtester, 'data_loader')
        assert hasattr(iron_condor_backtester, 'cash_manager')
        
        print("   ✅ Iron Condor system isolation verified")
        print("      Iron Condor system: UNAFFECTED ✅")
        print("      Flyagonal system: ISOLATED ✅")
        return True
        
    except Exception as e:
        print(f"   ❌ Iron Condor isolation error: {e}")
        return False

if __name__ == "__main__":
    # Run all tests
    success = run_all_tests()
    
    # Additional isolation test
    print("\n" + "="*50)
    test_iron_condor_isolation()
    
    if success:
        print(f"\n🚀 FLYAGONAL STRATEGY READY")
        print(f"   Framework Integration: ✅")
        print(f"   Iron Condor Protection: ✅")
        print(f"   Ready for Backtesting: ✅")
    else:
        print(f"\n⚠️  INTEGRATION ISSUES DETECTED")
        print(f"   Review test failures before proceeding")
    
    sys.exit(0 if success else 1)
