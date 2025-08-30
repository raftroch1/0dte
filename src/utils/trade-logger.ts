/**
 * Comprehensive Trade Logging System
 * 
 * Provides detailed logging and analysis capabilities for individual trades
 * during backtesting. Helps analyze strategy performance at the trade level.
 */

import { writeFileSync, appendFileSync, existsSync, mkdirSync } from 'fs';
import { join } from 'path';

export interface TradeLogEntry {
  // Trade Identification
  tradeId: string;
  strategy: string;
  symbol: string;
  timestamp: Date;
  
  // Entry Details
  entryTime: Date;
  entryPrice: number;
  entryReason: string;
  quantity: number;
  
  // Exit Details (filled when trade closes)
  exitTime?: Date;
  exitPrice?: number;
  exitReason?: string;
  
  // P&L Analysis
  grossPnL?: number;
  netPnL?: number; // After commissions
  pnlPercent?: number;
  commission?: number;
  
  // Risk Metrics
  maxDrawdown?: number;
  maxProfit?: number;
  holdingTime?: number; // in minutes
  
  // Market Context
  underlyingPrice?: number;
  vixLevel?: number;
  marketRegime?: string;
  
  // Strategy-Specific Data
  legs?: Array<{
    type: 'CALL' | 'PUT';
    strike: number;
    quantity: number;
    side: 'BUY' | 'SELL';
    entryPrice: number;
    exitPrice?: number;
  }>;
  
  // Metadata
  metadata?: { [key: string]: any };
}

export class TradeLogger {
  private logDir: string;
  private csvPath: string;
  private jsonPath: string;
  private trades: TradeLogEntry[] = [];
  private isInitialized: boolean = false;

  constructor(strategy: string, dateRange: string) {
    this.logDir = join(process.cwd(), 'logs', 'trades');
    this.csvPath = join(this.logDir, `${strategy}_${dateRange}_trades.csv`);
    this.jsonPath = join(this.logDir, `${strategy}_${dateRange}_trades.json`);
    this.initializeLogger();
  }

  private initializeLogger(): void {
    // Create logs directory if it doesn't exist
    if (!existsSync(this.logDir)) {
      mkdirSync(this.logDir, { recursive: true });
    }

    // Initialize CSV with headers
    const csvHeaders = [
      'TradeId', 'Strategy', 'Symbol', 'Timestamp',
      'EntryTime', 'EntryPrice', 'EntryReason', 'Quantity',
      'ExitTime', 'ExitPrice', 'ExitReason',
      'GrossPnL', 'NetPnL', 'PnLPercent', 'Commission',
      'MaxDrawdown', 'MaxProfit', 'HoldingTime',
      'UnderlyingPrice', 'VixLevel', 'MarketRegime',
      'LegsCount', 'Metadata'
    ].join(',');

    writeFileSync(this.csvPath, csvHeaders + '\n');
    writeFileSync(this.jsonPath, '[]');
    
    this.isInitialized = true;
    console.log(`📊 Trade Logger initialized:`);
    console.log(`   CSV: ${this.csvPath}`);
    console.log(`   JSON: ${this.jsonPath}`);
  }

  /**
   * Log trade entry
   */
  logTradeEntry(entry: Omit<TradeLogEntry, 'timestamp'>): void {
    const tradeEntry: TradeLogEntry = {
      ...entry,
      timestamp: new Date()
    };

    this.trades.push(tradeEntry);
    
    console.log(`📝 TRADE ENTRY: ${entry.tradeId}`);
    console.log(`   Strategy: ${entry.strategy} | Symbol: ${entry.symbol}`);
    console.log(`   Entry: $${entry.entryPrice} x ${entry.quantity} | Reason: ${entry.entryReason}`);
    console.log(`   Legs: ${entry.legs?.length || 1} | Underlying: $${entry.underlyingPrice?.toFixed(2) || 'N/A'}`);
  }

  /**
   * Update trade with exit information
   */
  logTradeExit(
    tradeId: string, 
    exitData: {
      exitTime: Date;
      exitPrice: number;
      exitReason: string;
      grossPnL: number;
      netPnL: number;
      commission: number;
      maxDrawdown?: number;
      maxProfit?: number;
    }
  ): void {
    const trade = this.trades.find(t => t.tradeId === tradeId);
    if (!trade) {
      console.warn(`⚠️ Trade ${tradeId} not found for exit logging`);
      return;
    }

    // Update trade with exit data
    trade.exitTime = exitData.exitTime;
    trade.exitPrice = exitData.exitPrice;
    trade.exitReason = exitData.exitReason;
    trade.grossPnL = exitData.grossPnL;
    trade.netPnL = exitData.netPnL;
    trade.commission = exitData.commission;
    trade.pnlPercent = ((exitData.exitPrice - trade.entryPrice) / trade.entryPrice) * 100;
    trade.holdingTime = (exitData.exitTime.getTime() - trade.entryTime.getTime()) / (1000 * 60); // minutes
    trade.maxDrawdown = exitData.maxDrawdown;
    trade.maxProfit = exitData.maxProfit;

    // Write to CSV immediately
    this.appendToCsv(trade);

    console.log(`🚪 TRADE EXIT: ${tradeId}`);
    console.log(`   Exit: $${exitData.exitPrice} | Reason: ${exitData.exitReason}`);
    console.log(`   P&L: $${exitData.netPnL.toFixed(2)} (${trade.pnlPercent?.toFixed(2)}%) | Hold: ${trade.holdingTime?.toFixed(0)}min`);
    console.log(`   Commission: $${exitData.commission.toFixed(2)} | Max Profit: $${exitData.maxProfit?.toFixed(2) || 'N/A'}`);
  }

  /**
   * Update trade with real-time P&L data
   */
  updateTradeMetrics(
    tradeId: string, 
    currentPrice: number, 
    unrealizedPnL: number,
    maxDrawdown?: number,
    maxProfit?: number
  ): void {
    const trade = this.trades.find(t => t.tradeId === tradeId);
    if (!trade || trade.exitTime) return; // Skip if trade not found or already closed

    // Update running metrics
    if (maxDrawdown !== undefined) trade.maxDrawdown = Math.min(trade.maxDrawdown || 0, maxDrawdown);
    if (maxProfit !== undefined) trade.maxProfit = Math.max(trade.maxProfit || 0, maxProfit);
  }

  private appendToCsv(trade: TradeLogEntry): void {
    const csvRow = [
      trade.tradeId,
      trade.strategy,
      trade.symbol,
      trade.timestamp.toISOString(),
      trade.entryTime.toISOString(),
      trade.entryPrice,
      trade.entryReason,
      trade.quantity,
      trade.exitTime?.toISOString() || '',
      trade.exitPrice || '',
      trade.exitReason || '',
      trade.grossPnL || '',
      trade.netPnL || '',
      trade.pnlPercent || '',
      trade.commission || '',
      trade.maxDrawdown || '',
      trade.maxProfit || '',
      trade.holdingTime || '',
      trade.underlyingPrice || '',
      trade.vixLevel || '',
      trade.marketRegime || '',
      trade.legs?.length || 1,
      JSON.stringify(trade.metadata || {})
    ].join(',');

    appendFileSync(this.csvPath, csvRow + '\n');
  }

  /**
   * Finalize logging and generate summary
   */
  finalize(): void {
    // Write complete JSON log
    writeFileSync(this.jsonPath, JSON.stringify(this.trades, null, 2));

    // Generate summary
    const completedTrades = this.trades.filter(t => t.exitTime);
    const winners = completedTrades.filter(t => (t.netPnL || 0) > 0);
    const losers = completedTrades.filter(t => (t.netPnL || 0) < 0);

    console.log(`\n📊 TRADE LOGGING SUMMARY:`);
    console.log(`   Total Trades: ${completedTrades.length}`);
    console.log(`   Winners: ${winners.length} (${((winners.length / completedTrades.length) * 100).toFixed(1)}%)`);
    console.log(`   Losers: ${losers.length} (${((losers.length / completedTrades.length) * 100).toFixed(1)}%)`);
    console.log(`   Avg P&L: $${(completedTrades.reduce((sum, t) => sum + (t.netPnL || 0), 0) / completedTrades.length).toFixed(2)}`);
    console.log(`   Avg Hold Time: ${(completedTrades.reduce((sum, t) => sum + (t.holdingTime || 0), 0) / completedTrades.length).toFixed(0)} minutes`);
    console.log(`   Files saved:`);
    console.log(`     📄 CSV: ${this.csvPath}`);
    console.log(`     📄 JSON: ${this.jsonPath}`);
  }

  /**
   * Get trade statistics
   */
  getTradeStats(): {
    totalTrades: number;
    completedTrades: number;
    winRate: number;
    avgPnL: number;
    avgHoldTime: number;
    maxWin: number;
    maxLoss: number;
  } {
    const completedTrades = this.trades.filter(t => t.exitTime);
    const winners = completedTrades.filter(t => (t.netPnL || 0) > 0);
    const pnls = completedTrades.map(t => t.netPnL || 0);

    return {
      totalTrades: this.trades.length,
      completedTrades: completedTrades.length,
      winRate: completedTrades.length > 0 ? (winners.length / completedTrades.length) * 100 : 0,
      avgPnL: pnls.length > 0 ? pnls.reduce((sum, pnl) => sum + pnl, 0) / pnls.length : 0,
      avgHoldTime: completedTrades.length > 0 ? completedTrades.reduce((sum, t) => sum + (t.holdingTime || 0), 0) / completedTrades.length : 0,
      maxWin: pnls.length > 0 ? Math.max(...pnls) : 0,
      maxLoss: pnls.length > 0 ? Math.min(...pnls) : 0
    };
  }
}
