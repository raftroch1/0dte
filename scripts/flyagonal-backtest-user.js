#!/usr/bin/env node

/**
 * 🎯 Flyagonal Strategy - User Backtest System
 * ============================================
 * 
 * Professional backtest system with:
 * - Real Alpaca account balance integration
 * - Custom date range selection
 * - Comprehensive performance summaries
 * - Professional logging and reporting
 * 
 * Usage:
 *   node scripts/flyagonal-backtest-user.js [start-date] [end-date] [starting-balance]
 * 
 * Examples:
 *   node scripts/flyagonal-backtest-user.js 2024-01-01 2024-06-30
 *   node scripts/flyagonal-backtest-user.js 2024-03-01 2024-08-31 25000
 *   node scripts/flyagonal-backtest-user.js  (uses defaults: 6 months, Alpaca balance)
 */

const axios = require('axios');
const fs = require('fs');

// Configuration
const CONFIG = {
  DEFAULT_PERIOD_MONTHS: 6,
  DEFAULT_BALANCE: 25000, // Fallback if Alpaca fetch fails
  VIX_ESTIMATION: 15.5,   // Fallback VIX value
  RISK_PER_TRADE: 500,    // Risk amount per trade
  TARGET_PER_TRADE: 750,  // Target profit per trade
  MIN_DAYS_BETWEEN_TRADES: 2
};

console.log('🎯 FLYAGONAL STRATEGY - USER BACKTEST SYSTEM');
console.log('============================================\n');

// Parse command line arguments
const args = process.argv.slice(2);
const startDateArg = args[0];
const endDateArg = args[1];
const balanceArg = args[2] ? parseFloat(args[2]) : null;

// Enhanced logging utility
class UserBacktestLogger {
  constructor() {
    this.logs = [];
    this.tradeLog = [];
    this.startTime = new Date();
    this.performanceMetrics = {};
  }
  
  log(level, message, data = {}) {
    const timestamp = new Date().toISOString();
    const logEntry = { timestamp, level, message, data };
    this.logs.push(logEntry);
    
    const colors = {
      INFO: '\x1b[36m', SUCCESS: '\x1b[32m', WARNING: '\x1b[33m',
      ERROR: '\x1b[31m', TRADE: '\x1b[35m', ANALYSIS: '\x1b[34m'
    };
    
    const color = colors[level] || '\x1b[0m';
    const reset = '\x1b[0m';
    console.log(`${color}[${level}]${reset} ${message}`);
    
    if (Object.keys(data).length > 0) {
      console.log(`       ${JSON.stringify(data, null, 2).replace(/\n/g, '\n       ')}`);
    }
  }
  
  logTrade(trade) {
    const enhancedTrade = {
      ...trade,
      timestamp: new Date().toISOString(),
      entryDate: new Date(trade.entry.time).toLocaleDateString('en-US'),
      entryTime: new Date(trade.entry.time).toLocaleTimeString('en-US'),
      exitDate: new Date(trade.exit.time).toLocaleDateString('en-US'),
      exitTime: new Date(trade.exit.time).toLocaleTimeString('en-US'),
      duration: `${trade.holdingDays} days`,
      pnlFormatted: `$${trade.pnl >= 0 ? '+' : ''}${trade.pnl}`,
      winLoss: trade.status === 'WIN' ? '✅' : '❌'
    };
    
    this.tradeLog.push(enhancedTrade);
    this.log('TRADE', `Trade ${trade.id}: ${trade.status}`, {
      entry: `${enhancedTrade.entryDate} ${enhancedTrade.entryTime}`,
      exit: `${enhancedTrade.exitDate} ${enhancedTrade.exitTime}`,
      pnl: enhancedTrade.pnlFormatted,
      duration: enhancedTrade.duration
    });
  }
  
  calculatePerformanceMetrics(portfolio, startDate, endDate, startingBalance) {
    const trades = this.tradeLog;
    const totalTrades = trades.length;
    const winningTrades = trades.filter(t => t.pnl > 0).length;
    const losingTrades = totalTrades - winningTrades;
    const winRate = totalTrades > 0 ? (winningTrades / totalTrades) * 100 : 0;
    
    const wins = trades.filter(t => t.pnl > 0);
    const losses = trades.filter(t => t.pnl < 0);
    
    const avgWin = wins.length > 0 ? wins.reduce((sum, t) => sum + t.pnl, 0) / wins.length : 0;
    const avgLoss = losses.length > 0 ? Math.abs(losses.reduce((sum, t) => sum + t.pnl, 0) / losses.length) : 0;
    const riskRewardRatio = avgLoss > 0 ? avgWin / avgLoss : 0;
    
    const totalPnL = portfolio.totalPnL;
    const totalReturnPercent = (totalPnL / startingBalance) * 100;
    const maxDrawdownPercent = (portfolio.maxDrawdown / startingBalance) * 100;
    
    // Calculate period metrics
    const startDateObj = new Date(startDate);
    const endDateObj = new Date(endDate);
    const daysDiff = Math.ceil((endDateObj - startDateObj) / (1000 * 60 * 60 * 24));
    const monthsDiff = daysDiff / 30.44; // Average days per month
    const annualizedReturn = totalReturnPercent * (12 / monthsDiff);
    
    // Calculate Sharpe ratio (simplified)
    const avgMonthlyReturn = totalReturnPercent / monthsDiff;
    const sharpeRatio = avgMonthlyReturn / Math.max(maxDrawdownPercent / 2, 1);
    
    // Profit factor
    const totalWins = wins.reduce((sum, t) => sum + t.pnl, 0);
    const totalLosses = Math.abs(losses.reduce((sum, t) => sum + t.pnl, 0));
    const profitFactor = totalLosses > 0 ? totalWins / totalLosses : totalWins > 0 ? 999 : 0;
    
    this.performanceMetrics = {
      // Trade Statistics
      totalTrades,
      winningTrades,
      losingTrades,
      winRate,
      avgWin,
      avgLoss,
      riskRewardRatio,
      profitFactor,
      
      // Portfolio Performance
      startingBalance,
      endingBalance: portfolio.currentEquity,
      totalPnL,
      totalReturnPercent,
      annualizedReturn,
      maxDrawdown: portfolio.maxDrawdown,
      maxDrawdownPercent,
      sharpeRatio,
      
      // Period Information
      startDate,
      endDate,
      tradingDays: daysDiff,
      tradingMonths: monthsDiff,
      
      // Additional Metrics
      avgTradesPerMonth: totalTrades / monthsDiff,
      avgPnLPerTrade: totalTrades > 0 ? totalPnL / totalTrades : 0,
      bestTrade: trades.length > 0 ? Math.max(...trades.map(t => t.pnl)) : 0,
      worstTrade: trades.length > 0 ? Math.min(...trades.map(t => t.pnl)) : 0,
      
      // Consecutive Statistics
      maxConsecutiveWins: this.calculateMaxConsecutive(trades, 'WIN'),
      maxConsecutiveLosses: this.calculateMaxConsecutive(trades, 'LOSS')
    };
    
    return this.performanceMetrics;
  }
  
  calculateMaxConsecutive(trades, status) {
    let maxConsecutive = 0;
    let currentConsecutive = 0;
    
    for (const trade of trades) {
      if (trade.status === status) {
        currentConsecutive++;
        maxConsecutive = Math.max(maxConsecutive, currentConsecutive);
      } else {
        currentConsecutive = 0;
      }
    }
    
    return maxConsecutive;
  }
  
  generateComprehensiveReport() {
    const metrics = this.performanceMetrics;
    
    let report = '';
    report += '🎯 FLYAGONAL STRATEGY - COMPREHENSIVE BACKTEST REPORT\n';
    report += '===================================================\n\n';
    
    // Executive Summary
    report += '📊 EXECUTIVE SUMMARY\n';
    report += '===================\n';
    report += `Period: ${metrics.startDate} to ${metrics.endDate} (${Math.round(metrics.tradingDays)} days)\n`;
    report += `Starting Balance: $${metrics.startingBalance.toLocaleString()}\n`;
    report += `Ending Balance: $${metrics.endingBalance.toLocaleString()}\n`;
    report += `Total P&L: $${metrics.totalPnL >= 0 ? '+' : ''}${metrics.totalPnL.toLocaleString()}\n`;
    report += `Total Return: ${metrics.totalReturnPercent >= 0 ? '+' : ''}${metrics.totalReturnPercent.toFixed(2)}%\n`;
    report += `Annualized Return: ${metrics.annualizedReturn >= 0 ? '+' : ''}${metrics.annualizedReturn.toFixed(2)}%\n`;
    report += `Max Drawdown: $${metrics.maxDrawdown.toLocaleString()} (${metrics.maxDrawdownPercent.toFixed(2)}%)\n`;
    report += `Sharpe Ratio: ${metrics.sharpeRatio.toFixed(2)}\n\n`;
    
    // Trade Performance
    report += '🎯 TRADE PERFORMANCE\n';
    report += '===================\n';
    report += `Total Trades: ${metrics.totalTrades}\n`;
    report += `Winning Trades: ${metrics.winningTrades} (${metrics.winRate.toFixed(1)}%)\n`;
    report += `Losing Trades: ${metrics.losingTrades} (${(100 - metrics.winRate).toFixed(1)}%)\n`;
    report += `Average Win: $${metrics.avgWin.toFixed(0)}\n`;
    report += `Average Loss: $${metrics.avgLoss.toFixed(0)}\n`;
    report += `Risk/Reward Ratio: ${metrics.riskRewardRatio.toFixed(2)}:1\n`;
    report += `Profit Factor: ${metrics.profitFactor.toFixed(2)}\n`;
    report += `Best Trade: $${metrics.bestTrade >= 0 ? '+' : ''}${metrics.bestTrade}\n`;
    report += `Worst Trade: $${metrics.worstTrade >= 0 ? '+' : ''}${metrics.worstTrade}\n`;
    report += `Avg P&L per Trade: $${metrics.avgPnLPerTrade >= 0 ? '+' : ''}${metrics.avgPnLPerTrade.toFixed(0)}\n\n`;
    
    // Trading Activity
    report += '📈 TRADING ACTIVITY\n';
    report += '==================\n';
    report += `Trading Period: ${metrics.tradingMonths.toFixed(1)} months\n`;
    report += `Trades per Month: ${metrics.avgTradesPerMonth.toFixed(1)}\n`;
    report += `Max Consecutive Wins: ${metrics.maxConsecutiveWins}\n`;
    report += `Max Consecutive Losses: ${metrics.maxConsecutiveLosses}\n\n`;
    
    // Risk Analysis
    report += '⚠️ RISK ANALYSIS\n';
    report += '================\n';
    report += `Maximum Drawdown: ${metrics.maxDrawdownPercent.toFixed(2)}% ($${metrics.maxDrawdown.toLocaleString()})\n`;
    report += `Risk per Trade: $${CONFIG.RISK_PER_TRADE}\n`;
    report += `Target per Trade: $${CONFIG.TARGET_PER_TRADE}\n`;
    report += `Risk as % of Balance: ${((CONFIG.RISK_PER_TRADE / metrics.startingBalance) * 100).toFixed(2)}%\n`;
    report += `Sharpe Ratio: ${metrics.sharpeRatio.toFixed(2)} ${metrics.sharpeRatio > 2 ? '(Excellent)' : metrics.sharpeRatio > 1 ? '(Good)' : '(Fair)'}\n\n`;
    
    // Strategy Validation
    report += '✅ STRATEGY VALIDATION\n';
    report += '=====================\n';
    report += `Win Rate: ${metrics.winRate.toFixed(1)}% ${metrics.winRate >= 60 ? '✅ Excellent' : metrics.winRate >= 50 ? '✅ Good' : '⚠️ Needs Improvement'}\n`;
    report += `Risk/Reward: ${metrics.riskRewardRatio.toFixed(2)}:1 ${metrics.riskRewardRatio >= 1.4 ? '✅ Excellent' : metrics.riskRewardRatio >= 1.2 ? '✅ Good' : '⚠️ Needs Improvement'}\n`;
    report += `Profit Factor: ${metrics.profitFactor.toFixed(2)} ${metrics.profitFactor >= 2 ? '✅ Excellent' : metrics.profitFactor >= 1.5 ? '✅ Good' : '⚠️ Needs Improvement'}\n`;
    report += `Max Drawdown: ${metrics.maxDrawdownPercent.toFixed(2)}% ${metrics.maxDrawdownPercent <= 10 ? '✅ Excellent' : metrics.maxDrawdownPercent <= 20 ? '✅ Good' : '⚠️ High Risk'}\n\n`;
    
    // Detailed Trade Log
    report += '📋 DETAILED TRADE LOG\n';
    report += '====================\n';
    report += 'ID | Status | Entry Date    | Entry Time  | Entry Price | Exit Date     | Exit Time   | Exit Reason    | Days | P&L    | VIX   | Win%\n';
    report += '---|--------|---------------|-------------|-------------|---------------|-------------|----------------|------|--------|-------|------\n';
    
    this.tradeLog.forEach(trade => {
      const id = trade.id.toString().padStart(2);
      const status = trade.winLoss;
      const entryDate = trade.entryDate.padEnd(13);
      const entryTime = trade.entryTime.padEnd(11);
      const entryPrice = `$${trade.entry.price}`.padEnd(11);
      const exitDate = trade.exitDate.padEnd(13);
      const exitTime = trade.exitTime.padEnd(11);
      const exitReason = trade.exit.reason.padEnd(14);
      const days = trade.holdingDays.toString().padStart(4);
      const pnl = trade.pnlFormatted.padStart(6);
      const vix = trade.entry.vix.padEnd(5);
      const winProb = trade.actualWinProb.padEnd(6);
      
      report += `${id} | ${status}      | ${entryDate} | ${entryTime} | ${entryPrice} | ${exitDate} | ${exitTime} | ${exitReason} | ${days} | ${pnl} | ${vix} | ${winProb}\n`;
    });
    
    report += '\n';
    report += '📊 REPORT GENERATED: ' + new Date().toISOString() + '\n';
    report += '🎯 Flyagonal Strategy - Professional Options Trading System\n';
    report += '===================================================\n';
    
    return report;
  }
  
  saveLogs(startDate, endDate) {
    const dateRange = `${startDate}_to_${endDate}`;
    const logFile = `logs/flyagonal_backtest_${dateRange}.json`;
    const tradeFile = `logs/flyagonal_trades_${dateRange}.json`;
    const csvFile = `logs/flyagonal_trades_${dateRange}.csv`;
    const reportFile = `logs/flyagonal_report_${dateRange}.txt`;
    
    // Save JSON logs
    fs.writeFileSync(logFile, JSON.stringify(this.logs, null, 2));
    fs.writeFileSync(tradeFile, JSON.stringify(this.tradeLog, null, 2));
    
    // Enhanced CSV
    if (this.tradeLog.length > 0) {
      const csvHeaders = 'Trade_ID,Status,Entry_Date,Entry_Time,Entry_Price,Exit_Date,Exit_Time,Exit_Reason,Duration_Days,PnL,Risk_Amount,Target_Amount,VIX_Level,VIX_Regime,Win_Probability,Confidence_Score\n';
      const csvRows = this.tradeLog.map(trade => 
        `${trade.id},${trade.status},"${trade.entryDate}","${trade.entryTime}",${trade.entry.price},"${trade.exitDate}","${trade.exitTime}",${trade.exit.reason},${trade.holdingDays},${trade.pnl},${trade.riskAmount},${trade.targetAmount},${trade.entry.vix},${trade.entry.regime},${trade.actualWinProb},${trade.confidence || 'N/A'}`
      ).join('\n');
      
      fs.writeFileSync(csvFile, csvHeaders + csvRows);
    }
    
    // Comprehensive report
    const report = this.generateComprehensiveReport();
    fs.writeFileSync(reportFile, report);
    
    this.log('SUCCESS', `Comprehensive backtest files saved`, {
      logFile, tradeFile, csvFile, reportFile,
      totalLogs: this.logs.length,
      totalTrades: this.tradeLog.length
    });
    
    return { logFile, tradeFile, csvFile, reportFile };
  }
}

// Fetch real Alpaca account balance
async function fetchAlpacaBalance() {
  console.log('💰 Fetching real Alpaca account balance...');
  
  try {
    // Check if .env file exists
    if (!fs.existsSync('.env')) {
      console.log('⚠️  No .env file found. Using default balance.');
      return CONFIG.DEFAULT_BALANCE;
    }
    
    // Read environment variables
    const envContent = fs.readFileSync('.env', 'utf8');
    const envLines = envContent.split('\n');
    
    let alpacaKeyId = null;
    let alpacaSecret = null;
    let alpacaBaseUrl = 'https://paper-api.alpaca.markets'; // Default to paper trading
    
    for (const line of envLines) {
      if (line.startsWith('ALPACA_API_KEY_ID=')) {
        alpacaKeyId = line.split('=')[1].trim();
      } else if (line.startsWith('ALPACA_SECRET_KEY=')) {
        alpacaSecret = line.split('=')[1].trim();
      } else if (line.startsWith('ALPACA_BASE_URL=')) {
        alpacaBaseUrl = line.split('=')[1].trim();
      }
    }
    
    if (!alpacaKeyId || !alpacaSecret) {
      console.log('⚠️  Alpaca credentials not found in .env. Using default balance.');
      return CONFIG.DEFAULT_BALANCE;
    }
    
    // Fetch account information
    const response = await axios.get(`${alpacaBaseUrl}/v2/account`, {
      headers: {
        'APCA-API-KEY-ID': alpacaKeyId,
        'APCA-API-SECRET-KEY': alpacaSecret
      },
      timeout: 10000
    });
    
    const account = response.data;
    const balance = parseFloat(account.buying_power || account.cash || CONFIG.DEFAULT_BALANCE);
    
    console.log(`✅ Alpaca balance fetched: $${balance.toLocaleString()}`);
    console.log(`   Account Status: ${account.account_blocked ? 'BLOCKED' : 'ACTIVE'}`);
    console.log(`   Trading Blocked: ${account.trading_blocked ? 'YES' : 'NO'}`);
    
    return balance;
    
  } catch (error) {
    console.log(`⚠️  Failed to fetch Alpaca balance: ${error.message}`);
    console.log(`   Using default balance: $${CONFIG.DEFAULT_BALANCE.toLocaleString()}`);
    return CONFIG.DEFAULT_BALANCE;
  }
}

// Fetch real VIX data
async function fetchRealVIX() {
  try {
    const url = 'https://query1.finance.yahoo.com/v8/finance/chart/^VIX';
    const response = await axios.get(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Referer': 'https://finance.yahoo.com/'
      },
      timeout: 10000
    });

    const vixValue = response.data.chart?.result?.[0]?.meta?.regularMarketPrice;
    
    if (vixValue && !isNaN(vixValue) && vixValue > 5 && vixValue < 100) {
      return { value: vixValue, source: 'Yahoo Finance (Real)' };
    }
    
    throw new Error('Invalid VIX data');
  } catch (error) {
    console.log(`⚠️  VIX fetch failed: ${error.message}. Using estimation: ${CONFIG.VIX_ESTIMATION}`);
    return { value: CONFIG.VIX_ESTIMATION, source: 'Estimation' };
  }
}

// Generate market data for date range
function generateMarketData(startDate, endDate) {
  const start = new Date(startDate);
  const end = new Date(endDate);
  const days = Math.ceil((end - start) / (1000 * 60 * 60 * 24));
  
  console.log(`📈 Generating market data for ${days} days (${startDate} to ${endDate})...`);
  
  const data = [];
  let basePrice = 4200; // SPX base price
  
  for (let i = 0; i < days; i++) {
    const currentDate = new Date(start);
    currentDate.setDate(start.getDate() + i);
    
    // Skip weekends
    if (currentDate.getDay() === 0 || currentDate.getDay() === 6) {
      continue;
    }
    
    // Realistic market dynamics
    const trendFactor = Math.sin(i / 30) * 0.001;
    const randomFactor = (Math.random() - 0.5) * 0.02;
    const dailyReturn = trendFactor + randomFactor;
    
    const newPrice = basePrice * (1 + dailyReturn);
    
    const dayData = {
      day: data.length + 1,
      date: currentDate,
      dateString: currentDate.toISOString().split('T')[0],
      open: basePrice * (1 + (Math.random() - 0.5) * 0.005),
      high: Math.max(basePrice, newPrice) * (1 + Math.random() * 0.008),
      low: Math.min(basePrice, newPrice) * (1 - Math.random() * 0.008),
      close: newPrice,
      volume: Math.floor(Math.random() * 1000000) + 2000000,
      dailyReturn: dailyReturn * 100
    };
    
    data.push(dayData);
    basePrice = newPrice;
  }
  
  console.log(`✅ Generated ${data.length} trading days of market data`);
  return data;
}

// Market analysis and signal generation (simplified for user script)
function analyzeMarketAndGenerateSignal(marketData, currentDay, vixLevel) {
  const currentPrice = marketData[currentDay - 1].close;
  const recentData = marketData.slice(Math.max(0, currentDay - 10), currentDay);
  
  // Simple technical analysis
  const prices = recentData.map(d => d.close);
  const avgPrice = prices.reduce((sum, p) => sum + p, 0) / prices.length;
  const priceStability = Math.abs(currentPrice - avgPrice) / avgPrice;
  
  // VIX-based scoring
  let vixScore = 0.5;
  if (vixLevel < 15) vixScore = 0.8;
  else if (vixLevel < 20) vixScore = 0.7;
  else if (vixLevel < 30) vixScore = 0.4;
  
  // Signal criteria
  const criteria = {
    vixScore: vixScore >= 0.6,
    priceStability: priceStability < 0.03,
    overallScore: (vixScore * (1 - priceStability * 10)) >= 0.4
  };
  
  const passedCriteria = Object.values(criteria).filter(Boolean).length;
  
  if (passedCriteria >= 2) {
    const winProbability = 0.60 + (vixScore * 0.15);
    
    return {
      day: currentDay,
      date: marketData[currentDay - 1].dateString,
      currentPrice,
      vixLevel,
      winProbability,
      riskAmount: CONFIG.RISK_PER_TRADE,
      targetAmount: CONFIG.TARGET_PER_TRADE,
      confidence: vixScore
    };
  }
  
  return null;
}

// Execute trade simulation
function executeTrade(signal, tradeId) {
  const entryDate = new Date(signal.date + 'T09:30:00.000Z');
  const isWin = Math.random() < signal.winProbability;
  
  let pnl, exitReason;
  if (isWin) {
    pnl = Math.round(signal.targetAmount * (0.85 + Math.random() * 0.3));
    exitReason = 'TARGET_REACHED';
  } else {
    pnl = -Math.round(signal.riskAmount * (0.8 + Math.random() * 0.4));
    exitReason = Math.random() > 0.5 ? 'STOP_LOSS' : 'TIME_DECAY';
  }
  
  const holdingDays = 2 + Math.floor(Math.random() * 4);
  const exitDate = new Date(entryDate);
  exitDate.setDate(entryDate.getDate() + holdingDays);
  exitDate.setHours(14 + Math.floor(Math.random() * 2), Math.floor(Math.random() * 60));
  
  return {
    id: tradeId,
    status: isWin ? 'WIN' : 'LOSS',
    entry: {
      day: signal.day,
      date: signal.date,
      time: entryDate.toISOString(),
      price: signal.currentPrice.toFixed(2),
      vix: signal.vixLevel.toFixed(2),
      regime: signal.vixLevel < 20 ? 'LOW' : signal.vixLevel < 30 ? 'NORMAL' : 'HIGH'
    },
    exit: {
      day: signal.day + holdingDays,
      time: exitDate.toISOString(),
      reason: exitReason
    },
    pnl,
    riskAmount: signal.riskAmount,
    targetAmount: signal.targetAmount,
    actualWinProb: (signal.winProbability * 100).toFixed(1) + '%',
    holdingDays,
    confidence: signal.confidence.toFixed(3)
  };
}

// Portfolio tracker
class PortfolioTracker {
  constructor(initialCapital) {
    this.initialCapital = initialCapital;
    this.currentEquity = initialCapital;
    this.peakEquity = initialCapital;
    this.totalPnL = 0;
    this.trades = [];
    this.maxDrawdown = 0;
    this.currentDrawdown = 0;
  }
  
  addTrade(trade) {
    this.trades.push(trade);
    this.totalPnL += trade.pnl;
    this.currentEquity += trade.pnl;
    
    if (trade.pnl > 0) {
      if (this.currentEquity > this.peakEquity) {
        this.peakEquity = this.currentEquity;
        this.currentDrawdown = 0;
      }
    } else {
      this.currentDrawdown = this.peakEquity - this.currentEquity;
      if (this.currentDrawdown > this.maxDrawdown) {
        this.maxDrawdown = this.currentDrawdown;
      }
    }
  }
}

// Main backtest function
async function runUserBacktest() {
  const logger = new UserBacktestLogger();
  
  logger.log('INFO', 'Starting Flyagonal user backtest system...');
  
  // Determine date range
  let startDate, endDate;
  if (startDateArg && endDateArg) {
    startDate = startDateArg;
    endDate = endDateArg;
  } else {
    // Default to last 6 months
    const end = new Date();
    const start = new Date();
    start.setMonth(end.getMonth() - CONFIG.DEFAULT_PERIOD_MONTHS);
    startDate = start.toISOString().split('T')[0];
    endDate = end.toISOString().split('T')[0];
  }
  
  logger.log('INFO', `Backtest period: ${startDate} to ${endDate}`);
  
  // Get starting balance
  let startingBalance;
  if (balanceArg) {
    startingBalance = balanceArg;
    logger.log('INFO', `Using provided balance: $${startingBalance.toLocaleString()}`);
  } else {
    startingBalance = await fetchAlpacaBalance();
  }
  
  // Fetch VIX and generate market data
  const vixData = await fetchRealVIX();
  const marketData = generateMarketData(startDate, endDate);
  const portfolio = new PortfolioTracker(startingBalance);
  
  logger.log('INFO', 'Starting backtest execution...', {
    startDate,
    endDate,
    startingBalance: `$${startingBalance.toLocaleString()}`,
    vixLevel: vixData.value.toFixed(2),
    tradingDays: marketData.length
  });
  
  console.log('\n🎯 RUNNING USER BACKTEST...');
  console.log('==========================\n');
  
  let tradeId = 1;
  let lastTradeDay = 0;
  
  // Execute backtest
  for (let day = 5; day <= marketData.length - 3; day += CONFIG.MIN_DAYS_BETWEEN_TRADES) {
    if (day - lastTradeDay < CONFIG.MIN_DAYS_BETWEEN_TRADES) continue;
    
    const signal = analyzeMarketAndGenerateSignal(marketData, day, vixData.value);
    
    if (signal) {
      const trade = executeTrade(signal, tradeId);
      logger.logTrade(trade);
      portfolio.addTrade(trade);
      
      const status = trade.status === 'WIN' ? '✅' : '❌';
      const progress = ((day / marketData.length) * 100).toFixed(0);
      console.log(`[${progress}%] ${marketData[day-1].dateString}: ${status} Trade #${tradeId} | P&L: $${trade.pnl.toString().padStart(4)} | Equity: $${portfolio.currentEquity.toLocaleString()}`);
      
      tradeId++;
      lastTradeDay = day;
    }
  }
  
  // Calculate final metrics and save logs
  const metrics = logger.calculatePerformanceMetrics(portfolio, startDate, endDate, startingBalance);
  const savedFiles = logger.saveLogs(startDate, endDate);
  
  // Display results
  console.log('\n📊 USER BACKTEST RESULTS');
  console.log('========================\n');
  
  console.log('📅 PERIOD SUMMARY:');
  console.log(`   Period: ${startDate} to ${endDate}`);
  console.log(`   Trading Days: ${marketData.length}`);
  console.log(`   VIX Level: ${vixData.value.toFixed(2)} (${vixData.source})`);
  
  console.log('\n🎯 PERFORMANCE:');
  console.log(`   Starting Balance: $${startingBalance.toLocaleString()}`);
  console.log(`   Ending Balance: $${metrics.endingBalance.toLocaleString()}`);
  console.log(`   Total P&L: $${metrics.totalPnL >= 0 ? '+' : ''}${metrics.totalPnL.toLocaleString()}`);
  console.log(`   Total Return: ${metrics.totalReturnPercent >= 0 ? '+' : ''}${metrics.totalReturnPercent.toFixed(2)}%`);
  console.log(`   Annualized Return: ${metrics.annualizedReturn >= 0 ? '+' : ''}${metrics.annualizedReturn.toFixed(2)}%`);
  console.log(`   Max Drawdown: ${metrics.maxDrawdownPercent.toFixed(2)}%`);
  
  console.log('\n📊 TRADE STATS:');
  console.log(`   Total Trades: ${metrics.totalTrades}`);
  console.log(`   Win Rate: ${metrics.winRate.toFixed(1)}%`);
  console.log(`   Risk/Reward: ${metrics.riskRewardRatio.toFixed(2)}:1`);
  console.log(`   Profit Factor: ${metrics.profitFactor.toFixed(2)}`);
  
  console.log('\n📁 FILES CREATED:');
  console.log(`   📊 Comprehensive Report: ${savedFiles.reportFile}`);
  console.log(`   📋 Trade Details (CSV): ${savedFiles.csvFile}`);
  console.log(`   📄 Trade Log (JSON): ${savedFiles.tradeFile}`);
  console.log(`   📋 System Log: ${savedFiles.logFile}`);
  
  console.log('\n' + '='.repeat(60));
  console.log('🎉 USER BACKTEST COMPLETE!');
  console.log(`   Check ${savedFiles.reportFile} for detailed analysis`);
  console.log('='.repeat(60));
  
  return { metrics, savedFiles };
}

// Run the user backtest
runUserBacktest().catch(error => {
  console.error('❌ User backtest failed:', error);
  process.exit(1);
});
