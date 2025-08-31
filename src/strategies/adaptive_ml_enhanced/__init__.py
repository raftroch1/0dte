"""
Adaptive ML-Enhanced Strategy Package
====================================

Hybrid strategy combining TypeScript AdaptiveStrategySelector logic 
with Python ML enhancement capabilities.

Following .cursorrules structure: src/strategies/adaptive_ml_enhanced/
"""

try:
    from .strategy import (
        AdaptiveMLEnhancedStrategy,
        AdaptiveMLEnhancedBacktester,
        StrategyType,
        MarketRegime,
        TimeWindow
    )
except ImportError:
    # Allow imports from different contexts
    from src.strategies.adaptive_ml_enhanced.strategy import (
        AdaptiveMLEnhancedStrategy,
        AdaptiveMLEnhancedBacktester,
        StrategyType,
        MarketRegime,
        TimeWindow
    )

__all__ = [
    'AdaptiveMLEnhancedStrategy',
    'AdaptiveMLEnhancedBacktester', 
    'StrategyType',
    'MarketRegime',
    'TimeWindow'
]
