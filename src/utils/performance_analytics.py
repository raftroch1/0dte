#!/usr/bin/env python3
"""
Enhanced Performance Analytics System - Inspired by ChatGPT Micro-Cap Experiment
===============================================================================

COMPREHENSIVE PERFORMANCE ANALYSIS FOR 0DTE OPTIONS TRADING:
1. Sortino Ratio calculation (missing from current system)
2. CAPM Analysis (Beta, Alpha vs benchmarks) 
3. Advanced drawdown metrics (duration, recovery time)
4. Risk-adjusted return metrics
5. Performance attribution analysis
6. Benchmark comparison system

This system provides the sophisticated performance analytics that the ChatGPT
repo demonstrated, including CAPM analysis, advanced risk metrics, and
comprehensive benchmark comparisons.

Location: src/utils/ (following .cursorrules structure)
Author: Advanced Options Trading Framework - Performance Analytics System
Inspired by: ChatGPT Micro-Cap Experiment performance tracking system
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
import json
import warnings
from scipy import stats

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics - inspired by ChatGPT repo's analytics"""
    
    # Basic Performance
    total_return: float
    annualized_return: float
    volatility: float
    
    # Risk-Adjusted Metrics (from ChatGPT repo)
    sharpe_ratio: float
    sortino_ratio: float          # Missing from current system
    calmar_ratio: float
    
    # Drawdown Analysis (enhanced from ChatGPT repo)
    max_drawdown: float
    max_drawdown_duration: int    # Days
    current_drawdown: float
    recovery_time: Optional[int]  # Days to recover from max DD
    
    # CAPM Analysis (from ChatGPT repo's benchmark comparison)
    beta: float
    alpha: float
    r_squared: float
    tracking_error: float
    information_ratio: float
    
    # Trading Statistics
    win_rate: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    
    # Advanced Metrics
    var_95: float                 # Value at Risk (95%)
    expected_shortfall: float     # Conditional VaR
    skewness: float
    kurtosis: float
    
    # Consistency Metrics
    monthly_win_rate: float
    consecutive_wins: int
    consecutive_losses: int

@dataclass
class BenchmarkComparison:
    """Benchmark comparison analysis - from ChatGPT repo patterns"""
    
    benchmark_name: str
    benchmark_return: float
    excess_return: float
    outperformance: bool
    
    # Relative Performance
    beta: float
    alpha: float
    correlation: float
    r_squared: float
    
    # Risk Comparison
    volatility_ratio: float       # Strategy vol / Benchmark vol
    sharpe_comparison: float      # Strategy Sharpe - Benchmark Sharpe
    max_dd_comparison: float      # Strategy DD - Benchmark DD

class PerformanceAnalyzer:
    """
    Enhanced Performance Analytics System
    
    Implements the sophisticated performance analysis from the ChatGPT
    Micro-Cap experiment, including CAPM analysis, advanced risk metrics,
    and comprehensive benchmark comparisons.
    
    Key Features (from ChatGPT repo):
    - Sortino ratio calculation (downside deviation)
    - CAPM analysis (Beta, Alpha, R²)
    - Advanced drawdown analysis
    - Multi-benchmark comparison
    - Risk-adjusted performance metrics
    """
    
    def __init__(self, risk_free_rate: float = 0.045):
        """
        Initialize performance analyzer
        
        Args:
            risk_free_rate: Annual risk-free rate (default 4.5%)
        """
        self.risk_free_rate = risk_free_rate
        self.daily_rf_rate = (1 + risk_free_rate) ** (1/252) - 1
        
        # Benchmark data cache
        self.benchmark_cache: Dict[str, pd.Series] = {}
        
        logger.info("📊 ENHANCED PERFORMANCE ANALYZER INITIALIZED")
        logger.info(f"   Risk-Free Rate: {risk_free_rate:.1%}")
        logger.info(f"   Daily RF Rate: {self.daily_rf_rate:.4%}")
    
    def calculate_returns(self, equity_curve: pd.Series) -> pd.Series:
        """
        Calculate daily returns from equity curve
        
        Args:
            equity_curve: Time series of account balance
            
        Returns:
            Daily returns series
        """
        if len(equity_curve) < 2:
            return pd.Series(dtype=float)
        
        # Ensure datetime index
        if not isinstance(equity_curve.index, pd.DatetimeIndex):
            equity_curve.index = pd.to_datetime(equity_curve.index)
        
        # Ensure timezone-naive for consistency
        if equity_curve.index.tz is not None:
            equity_curve.index = equity_curve.index.tz_localize(None)
        
        # Calculate daily returns
        returns = equity_curve.pct_change().dropna()
        
        # Remove any infinite or NaN values
        returns = returns.replace([np.inf, -np.inf], np.nan).dropna()
        
        return returns
    
    def calculate_sortino_ratio(self, returns: pd.Series, 
                              target_return: float = None) -> float:
        """
        Calculate Sortino Ratio (missing from current system)
        
        Sortino ratio focuses on downside deviation instead of total volatility,
        providing a better risk-adjusted return measure for asymmetric strategies.
        
        From ChatGPT repo's advanced risk metrics.
        """
        if len(returns) < 2:
            return 0.0
        
        if target_return is None:
            target_return = self.daily_rf_rate
        
        # Calculate excess returns
        excess_returns = returns - target_return
        
        # Calculate downside deviation (only negative excess returns)
        downside_returns = excess_returns[excess_returns < 0]
        
        if len(downside_returns) == 0:
            return np.inf  # No downside risk
        
        downside_deviation = np.sqrt(np.mean(downside_returns ** 2))
        
        if downside_deviation == 0:
            return np.inf
        
        # Annualized Sortino ratio
        mean_excess = np.mean(excess_returns)
        sortino = (mean_excess / downside_deviation) * np.sqrt(252)
        
        return float(sortino)
    
    def calculate_capm_metrics(self, returns: pd.Series, 
                             benchmark_returns: pd.Series) -> Tuple[float, float, float, float]:
        """
        Calculate CAPM metrics (Beta, Alpha, R², Tracking Error)
        
        Implements the CAPM analysis from ChatGPT repo's benchmark comparison system.
        
        Returns:
            (beta, alpha_annualized, r_squared, tracking_error)
        """
        if len(returns) < 10 or len(benchmark_returns) < 10:
            return 0.0, 0.0, 0.0, 0.0
        
        # Align data
        aligned_data = pd.DataFrame({
            'strategy': returns,
            'benchmark': benchmark_returns
        }).dropna()
        
        if len(aligned_data) < 10:
            return 0.0, 0.0, 0.0, 0.0
        
        strategy_excess = aligned_data['strategy'] - self.daily_rf_rate
        benchmark_excess = aligned_data['benchmark'] - self.daily_rf_rate
        
        # Calculate beta using linear regression
        if np.std(benchmark_excess) == 0:
            return 0.0, 0.0, 0.0, 0.0
        
        beta, alpha_daily = np.polyfit(benchmark_excess, strategy_excess, 1)
        
        # Calculate R-squared
        correlation = np.corrcoef(strategy_excess, benchmark_excess)[0, 1]
        r_squared = correlation ** 2 if not np.isnan(correlation) else 0.0
        
        # Annualize alpha
        alpha_annualized = (1 + alpha_daily) ** 252 - 1
        
        # Calculate tracking error (annualized)
        tracking_diff = strategy_excess - beta * benchmark_excess
        tracking_error = np.std(tracking_diff) * np.sqrt(252)
        
        return float(beta), float(alpha_annualized), float(r_squared), float(tracking_error)
    
    def calculate_drawdown_metrics(self, equity_curve: pd.Series) -> Tuple[float, int, float, Optional[int]]:
        """
        Calculate advanced drawdown metrics
        
        Enhanced drawdown analysis from ChatGPT repo's risk management system.
        
        Returns:
            (max_drawdown, max_dd_duration, current_drawdown, recovery_time)
        """
        if len(equity_curve) < 2:
            return 0.0, 0, 0.0, None
        
        # Calculate running maximum (peak)
        running_max = equity_curve.expanding().max()
        
        # Calculate drawdown series
        drawdown = (equity_curve / running_max) - 1.0
        
        # Maximum drawdown
        max_drawdown = abs(drawdown.min())
        
        # Current drawdown
        current_drawdown = abs(drawdown.iloc[-1])
        
        # Maximum drawdown duration
        max_dd_duration = 0
        current_duration = 0
        
        for dd in drawdown:
            if dd < 0:
                current_duration += 1
                max_dd_duration = max(max_dd_duration, current_duration)
            else:
                current_duration = 0
        
        # Recovery time (days to recover from max drawdown)
        recovery_time = None
        max_dd_idx = drawdown.idxmin()
        
        if max_dd_idx in drawdown.index:
            max_dd_pos = drawdown.index.get_loc(max_dd_idx)
            recovery_data = drawdown.iloc[max_dd_pos:]
            
            # Find first zero or positive drawdown after max DD
            recovery_idx = recovery_data[recovery_data >= 0].index
            if len(recovery_idx) > 0:
                recovery_time = len(recovery_data[:recovery_idx[0]])
        
        return float(max_drawdown), max_dd_duration, float(current_drawdown), recovery_time
    
    def calculate_var_and_es(self, returns: pd.Series, 
                           confidence_level: float = 0.95) -> Tuple[float, float]:
        """
        Calculate Value at Risk (VaR) and Expected Shortfall (ES)
        
        Advanced risk metrics for tail risk assessment.
        """
        if len(returns) < 10:
            return 0.0, 0.0
        
        # Sort returns in ascending order
        sorted_returns = np.sort(returns)
        
        # Calculate VaR (percentile)
        var_index = int((1 - confidence_level) * len(sorted_returns))
        var_95 = abs(sorted_returns[var_index]) if var_index < len(sorted_returns) else 0.0
        
        # Calculate Expected Shortfall (mean of returns below VaR)
        tail_returns = sorted_returns[:var_index] if var_index > 0 else []
        expected_shortfall = abs(np.mean(tail_returns)) if len(tail_returns) > 0 else 0.0
        
        return float(var_95), float(expected_shortfall)
    
    def calculate_trading_statistics(self, trade_pnls: List[float]) -> Dict[str, float]:
        """
        Calculate comprehensive trading statistics
        
        From ChatGPT repo's trade analysis system.
        """
        if not trade_pnls:
            return {
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'largest_win': 0.0,
                'largest_loss': 0.0,
                'consecutive_wins': 0,
                'consecutive_losses': 0
            }
        
        pnls = np.array(trade_pnls)
        
        # Basic statistics
        wins = pnls[pnls > 0]
        losses = pnls[pnls < 0]
        
        win_rate = len(wins) / len(pnls) if len(pnls) > 0 else 0.0
        
        # Profit factor
        total_wins = np.sum(wins) if len(wins) > 0 else 0.0
        total_losses = abs(np.sum(losses)) if len(losses) > 0 else 0.0
        profit_factor = total_wins / total_losses if total_losses > 0 else np.inf
        
        # Average win/loss
        avg_win = np.mean(wins) if len(wins) > 0 else 0.0
        avg_loss = np.mean(losses) if len(losses) > 0 else 0.0
        
        # Largest win/loss
        largest_win = np.max(wins) if len(wins) > 0 else 0.0
        largest_loss = np.min(losses) if len(losses) > 0 else 0.0
        
        # Consecutive wins/losses
        consecutive_wins = 0
        consecutive_losses = 0
        current_wins = 0
        current_losses = 0
        
        for pnl in pnls:
            if pnl > 0:
                current_wins += 1
                current_losses = 0
                consecutive_wins = max(consecutive_wins, current_wins)
            elif pnl < 0:
                current_losses += 1
                current_wins = 0
                consecutive_losses = max(consecutive_losses, current_losses)
        
        return {
            'win_rate': float(win_rate),
            'profit_factor': float(profit_factor) if not np.isinf(profit_factor) else 999.0,
            'avg_win': float(avg_win),
            'avg_loss': float(avg_loss),
            'largest_win': float(largest_win),
            'largest_loss': float(largest_loss),
            'consecutive_wins': consecutive_wins,
            'consecutive_losses': consecutive_losses
        }
    
    def get_benchmark_data(self, symbol: str, start_date: datetime, 
                          end_date: datetime) -> pd.Series:
        """
        Get benchmark data for comparison
        
        Implements benchmark data fetching similar to ChatGPT repo's
        multi-benchmark comparison system.
        """
        cache_key = f"{symbol}_{start_date.date()}_{end_date.date()}"
        
        if cache_key in self.benchmark_cache:
            return self.benchmark_cache[cache_key]
        
        try:
            # Try to import yfinance for benchmark data
            import yfinance as yf
            
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date)
            
            if data.empty:
                logger.warning(f"No benchmark data found for {symbol}")
                return pd.Series(dtype=float)
            
            # Calculate returns
            prices = data['Close']
            returns = prices.pct_change().dropna()
            
            # Ensure timezone-naive for consistency
            if returns.index.tz is not None:
                returns.index = returns.index.tz_localize(None)
            
            # Cache the data
            self.benchmark_cache[cache_key] = returns
            
            return returns
            
        except ImportError:
            logger.warning("yfinance not available for benchmark data")
            return pd.Series(dtype=float)
        except Exception as e:
            logger.warning(f"Error fetching benchmark data for {symbol}: {e}")
            return pd.Series(dtype=float)
    
    def analyze_performance(self, equity_curve: pd.Series, 
                          trade_pnls: Optional[List[float]] = None,
                          benchmark_symbols: Optional[List[str]] = None) -> PerformanceMetrics:
        """
        Comprehensive performance analysis
        
        Main analysis function implementing all metrics from ChatGPT repo's
        performance tracking system.
        """
        
        if len(equity_curve) < 2:
            logger.warning("Insufficient data for performance analysis")
            return self._get_empty_metrics()
        
        # Calculate returns
        returns = self.calculate_returns(equity_curve)
        
        if len(returns) < 2:
            return self._get_empty_metrics()
        
        # Basic performance metrics
        total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1
        annualized_return = (1 + total_return) ** (252 / len(returns)) - 1
        volatility = returns.std() * np.sqrt(252)
        
        # Risk-adjusted metrics
        excess_returns = returns - self.daily_rf_rate
        sharpe_ratio = (excess_returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0.0
        sortino_ratio = self.calculate_sortino_ratio(returns)
        
        # Calmar ratio (annualized return / max drawdown)
        max_dd, max_dd_duration, current_dd, recovery_time = self.calculate_drawdown_metrics(equity_curve)
        calmar_ratio = annualized_return / max_dd if max_dd > 0 else 0.0
        
        # Default CAPM metrics (will be updated if benchmark available)
        beta, alpha, r_squared, tracking_error = 0.0, 0.0, 0.0, 0.0
        information_ratio = 0.0
        
        # CAPM analysis with SPY as default benchmark
        if benchmark_symbols is None:
            benchmark_symbols = ['SPY']
        
        if benchmark_symbols:
            benchmark_symbol = benchmark_symbols[0]  # Use first benchmark
            start_date = equity_curve.index[0]
            end_date = equity_curve.index[-1]
            
            benchmark_returns = self.get_benchmark_data(benchmark_symbol, start_date, end_date)
            
            if len(benchmark_returns) > 10:
                beta, alpha, r_squared, tracking_error = self.calculate_capm_metrics(returns, benchmark_returns)
                
                # Information ratio
                if tracking_error > 0:
                    information_ratio = alpha / tracking_error
        
        # Trading statistics
        trading_stats = self.calculate_trading_statistics(trade_pnls or [])
        
        # Advanced risk metrics
        var_95, expected_shortfall = self.calculate_var_and_es(returns)
        
        # Distribution metrics
        skewness = float(stats.skew(returns)) if len(returns) > 3 else 0.0
        kurtosis = float(stats.kurtosis(returns)) if len(returns) > 3 else 0.0
        
        # Monthly consistency (simplified)
        monthly_win_rate = trading_stats['win_rate']  # Simplified for now
        
        return PerformanceMetrics(
            # Basic Performance
            total_return=float(total_return),
            annualized_return=float(annualized_return),
            volatility=float(volatility),
            
            # Risk-Adjusted Metrics
            sharpe_ratio=float(sharpe_ratio),
            sortino_ratio=float(sortino_ratio),
            calmar_ratio=float(calmar_ratio),
            
            # Drawdown Analysis
            max_drawdown=float(max_dd),
            max_drawdown_duration=max_dd_duration,
            current_drawdown=float(current_dd),
            recovery_time=recovery_time,
            
            # CAPM Analysis
            beta=float(beta),
            alpha=float(alpha),
            r_squared=float(r_squared),
            tracking_error=float(tracking_error),
            information_ratio=float(information_ratio),
            
            # Trading Statistics
            win_rate=trading_stats['win_rate'],
            profit_factor=trading_stats['profit_factor'],
            avg_win=trading_stats['avg_win'],
            avg_loss=trading_stats['avg_loss'],
            largest_win=trading_stats['largest_win'],
            largest_loss=trading_stats['largest_loss'],
            
            # Advanced Metrics
            var_95=float(var_95),
            expected_shortfall=float(expected_shortfall),
            skewness=float(skewness),
            kurtosis=float(kurtosis),
            
            # Consistency Metrics
            monthly_win_rate=monthly_win_rate,
            consecutive_wins=trading_stats['consecutive_wins'],
            consecutive_losses=trading_stats['consecutive_losses']
        )
    
    def compare_to_benchmarks(self, equity_curve: pd.Series,
                            benchmark_symbols: List[str] = None) -> List[BenchmarkComparison]:
        """
        Compare performance to multiple benchmarks
        
        Implements multi-benchmark comparison from ChatGPT repo's
        performance evaluation system.
        """
        
        if benchmark_symbols is None:
            benchmark_symbols = ['SPY', 'QQQ', 'IWM']  # Default benchmarks
        
        comparisons = []
        returns = self.calculate_returns(equity_curve)
        
        if len(returns) < 10:
            return comparisons
        
        start_date = equity_curve.index[0]
        end_date = equity_curve.index[-1]
        
        for symbol in benchmark_symbols:
            benchmark_returns = self.get_benchmark_data(symbol, start_date, end_date)
            
            if len(benchmark_returns) < 10:
                continue
            
            # Align data
            aligned_data = pd.DataFrame({
                'strategy': returns,
                'benchmark': benchmark_returns
            }).dropna()
            
            if len(aligned_data) < 10:
                continue
            
            # Calculate benchmark performance
            benchmark_total_return = (1 + aligned_data['benchmark']).prod() - 1
            benchmark_volatility = aligned_data['benchmark'].std() * np.sqrt(252)
            benchmark_sharpe = (aligned_data['benchmark'].mean() - self.daily_rf_rate) / aligned_data['benchmark'].std() * np.sqrt(252)
            
            # Strategy performance (aligned)
            strategy_total_return = (1 + aligned_data['strategy']).prod() - 1
            strategy_volatility = aligned_data['strategy'].std() * np.sqrt(252)
            strategy_sharpe = (aligned_data['strategy'].mean() - self.daily_rf_rate) / aligned_data['strategy'].std() * np.sqrt(252)
            
            # CAMP metrics
            beta, alpha, r_squared, tracking_error = self.calculate_camp_metrics(
                aligned_data['strategy'], aligned_data['benchmark']
            )
            
            # Correlation
            correlation = aligned_data.corr().iloc[0, 1]
            
            # Drawdown comparison
            strategy_equity = (1 + aligned_data['strategy']).cumprod()
            benchmark_equity = (1 + aligned_data['benchmark']).cumprod()
            
            strategy_dd, _, _, _ = self.calculate_drawdown_metrics(strategy_equity)
            benchmark_dd, _, _, _ = self.calculate_drawdown_metrics(benchmark_equity)
            
            comparison = BenchmarkComparison(
                benchmark_name=symbol,
                benchmark_return=float(benchmark_total_return),
                excess_return=float(strategy_total_return - benchmark_total_return),
                outperformance=strategy_total_return > benchmark_total_return,
                
                beta=float(beta),
                alpha=float(alpha),
                correlation=float(correlation),
                r_squared=float(r_squared),
                
                volatility_ratio=float(strategy_volatility / benchmark_volatility) if benchmark_volatility > 0 else 0.0,
                sharpe_comparison=float(strategy_sharpe - benchmark_sharpe),
                max_dd_comparison=float(strategy_dd - benchmark_dd)
            )
            
            comparisons.append(comparison)
        
        return comparisons
    
    def print_performance_report(self, metrics: PerformanceMetrics,
                               benchmark_comparisons: Optional[List[BenchmarkComparison]] = None) -> None:
        """
        Print comprehensive performance report
        
        Displays performance analysis similar to ChatGPT repo's
        daily results system with enhanced metrics.
        """
        
        print("\n" + "=" * 80)
        print("📊 ENHANCED PERFORMANCE ANALYTICS REPORT")
        print("=" * 80)
        
        # Basic Performance
        print(f"\n📈 RETURN METRICS:")
        print(f"   Total Return: {metrics.total_return:+.2%}")
        print(f"   Annualized Return: {metrics.annualized_return:+.2%}")
        print(f"   Volatility (Ann.): {metrics.volatility:.2%}")
        
        # Risk-Adjusted Performance
        print(f"\n🎯 RISK-ADJUSTED METRICS:")
        print(f"   Sharpe Ratio: {metrics.sharpe_ratio:.3f}")
        print(f"   Sortino Ratio: {metrics.sortino_ratio:.3f}")
        print(f"   Calmar Ratio: {metrics.calmar_ratio:.3f}")
        print(f"   Information Ratio: {metrics.information_ratio:.3f}")
        
        # Drawdown Analysis
        print(f"\n📉 DRAWDOWN ANALYSIS:")
        print(f"   Maximum Drawdown: {metrics.max_drawdown:.2%}")
        print(f"   Max DD Duration: {metrics.max_drawdown_duration} days")
        print(f"   Current Drawdown: {metrics.current_drawdown:.2%}")
        if metrics.recovery_time is not None:
            print(f"   Recovery Time: {metrics.recovery_time} days")
        else:
            print(f"   Recovery Time: Not recovered")
        
        # CAPM Analysis
        print(f"\n📊 CAPM ANALYSIS (vs SPY):")
        print(f"   Beta: {metrics.beta:.3f}")
        print(f"   Alpha (Ann.): {metrics.alpha:+.2%}")
        print(f"   R-Squared: {metrics.r_squared:.3f}")
        print(f"   Tracking Error: {metrics.tracking_error:.2%}")
        
        # Trading Statistics
        print(f"\n🎲 TRADING STATISTICS:")
        print(f"   Win Rate: {metrics.win_rate:.1%}")
        print(f"   Profit Factor: {metrics.profit_factor:.2f}")
        print(f"   Average Win: ${metrics.avg_win:+.2f}")
        print(f"   Average Loss: ${metrics.avg_loss:+.2f}")
        print(f"   Largest Win: ${metrics.largest_win:+.2f}")
        print(f"   Largest Loss: ${metrics.largest_loss:+.2f}")
        
        # Risk Metrics
        print(f"\n⚠️  RISK METRICS:")
        print(f"   VaR (95%): {metrics.var_95:.2%}")
        print(f"   Expected Shortfall: {metrics.expected_shortfall:.2%}")
        print(f"   Skewness: {metrics.skewness:.3f}")
        print(f"   Kurtosis: {metrics.kurtosis:.3f}")
        
        # Consistency Metrics
        print(f"\n🔄 CONSISTENCY METRICS:")
        print(f"   Monthly Win Rate: {metrics.monthly_win_rate:.1%}")
        print(f"   Max Consecutive Wins: {metrics.consecutive_wins}")
        print(f"   Max Consecutive Losses: {metrics.consecutive_losses}")
        
        # Benchmark Comparisons
        if benchmark_comparisons:
            print(f"\n🏆 BENCHMARK COMPARISONS:")
            for comp in benchmark_comparisons:
                print(f"\n   vs {comp.benchmark_name}:")
                print(f"     Excess Return: {comp.excess_return:+.2%}")
                print(f"     Beta: {comp.beta:.3f}")
                print(f"     Alpha: {comp.alpha:+.2%}")
                print(f"     Correlation: {comp.correlation:.3f}")
                print(f"     Sharpe Advantage: {comp.sharpe_comparison:+.3f}")
                print(f"     Outperformance: {'✅' if comp.outperformance else '❌'}")
    
    def _get_empty_metrics(self) -> PerformanceMetrics:
        """Return empty metrics for insufficient data"""
        return PerformanceMetrics(
            total_return=0.0, annualized_return=0.0, volatility=0.0,
            sharpe_ratio=0.0, sortino_ratio=0.0, calmar_ratio=0.0,
            max_drawdown=0.0, max_drawdown_duration=0, current_drawdown=0.0, recovery_time=None,
            beta=0.0, alpha=0.0, r_squared=0.0, tracking_error=0.0, information_ratio=0.0,
            win_rate=0.0, profit_factor=0.0, avg_win=0.0, avg_loss=0.0,
            largest_win=0.0, largest_loss=0.0,
            var_95=0.0, expected_shortfall=0.0, skewness=0.0, kurtosis=0.0,
            monthly_win_rate=0.0, consecutive_wins=0, consecutive_losses=0
        )
    
    def export_metrics(self, metrics: PerformanceMetrics, 
                      filepath: str) -> None:
        """Export metrics to JSON file"""
        
        metrics_dict = asdict(metrics)
        
        # Convert any numpy types to Python types
        for key, value in metrics_dict.items():
            if isinstance(value, (np.integer, np.floating)):
                metrics_dict[key] = float(value)
        
        with open(filepath, 'w') as f:
            json.dump(metrics_dict, f, indent=2, default=str)
        
        logger.info(f"Performance metrics exported to {filepath}")

# Example usage and integration patterns
if __name__ == "__main__":
    """
    Example usage of the Performance Analyzer
    
    Demonstrates integration patterns from ChatGPT repo
    """
    
    # Create sample equity curve
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    
    # Simulate equity curve with some volatility
    np.random.seed(42)
    returns = np.random.normal(0.001, 0.02, 100)  # Daily returns
    equity_curve = pd.Series((1 + returns).cumprod() * 25000, index=dates)
    
    # Sample trade P&Ls
    trade_pnls = [50, -30, 75, -25, 100, -40, 60, -20, 80, -35]
    
    # Initialize analyzer
    analyzer = PerformanceAnalyzer(risk_free_rate=0.045)
    
    # Analyze performance
    metrics = analyzer.analyze_performance(
        equity_curve=equity_curve,
        trade_pnls=trade_pnls,
        benchmark_symbols=['SPY']
    )
    
    # Compare to benchmarks
    comparisons = analyzer.compare_to_benchmarks(
        equity_curve=equity_curve,
        benchmark_symbols=['SPY', 'QQQ']
    )
    
    # Print comprehensive report
    analyzer.print_performance_report(metrics, comparisons)
    
    # Export metrics
    analyzer.export_metrics(metrics, "performance_metrics.json")
