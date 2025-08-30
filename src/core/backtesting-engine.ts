
import { EventEmitter } from 'events';
import { MarketData, OptionsChain, TradeSignal, Strategy, DailyMetrics } from '../utils/types';
import { AlpacaPaperTrading, PaperTradingConfig } from '../trading/alpaca-paper-trading';
import { GreeksSimulator, OptionPricingInputs } from '../data/greeks-simulator';
import { AlpacaIntegration } from './alpaca-integration';

export interface BacktestConfig {
  startDate: Date;
  endDate: Date;
  initialBalance: number;
  strategy: Strategy;
  underlyingSymbol: string;
  commissionPerContract: number;
  slippagePercent: number;
  bidAskSpreadPercent: number;
  riskFreeRate: number;
}

export interface BacktestResult {
  summary: {
    totalReturn: number;
    totalReturnPercent: number;
    annualizedReturn: number;
    maxDrawdown: number;
    sharpeRatio: number;
    sortinoRatio: number;
    winRate: number;
    profitFactor: number;
    totalTrades: number;
    avgTradeReturn: number;
    avgWinningTrade: number;
    avgLosingTrade: number;
    largestWin: number;
    largestLoss: number;
    consecutiveWins: number;
    consecutiveLosses: number;
  };
  dailyMetrics: DailyMetrics[];
  trades: BacktestTrade[];
  equityCurve: { date: Date; equity: number; drawdown: number }[];
  monthlyReturns: { month: string; return: number }[];
  riskMetrics: {
    volatility: number;
    beta: number;
    alpha: number;
    informationRatio: number;
    calmarRatio: number;
  };
}

export interface BacktestTrade {
  id: string;
  entryDate: Date;
  exitDate: Date;
  symbol: string;
  side: 'BUY' | 'SELL';
  quantity: number;
  entryPrice: number;
  exitPrice: number;
  pnl: number;
  pnlPercent: number;
  commission: number;
  slippage: number;
  holdingPeriod: number; // minutes
  signal: TradeSignal;
  exitReason: 'PROFIT_TARGET' | 'STOP_LOSS' | 'TIME_DECAY' | 'SIGNAL_EXIT' | 'EOD';
  greeksAtEntry: {
    delta: number;
    gamma: number;
    theta: number;
    vega: number;
  };
  greeksAtExit: {
    delta: number;
    gamma: number;
    theta: number;
    vega: number;
  };
}

export class BacktestingEngine extends EventEmitter {
  private config: BacktestConfig;
  private paperTrading: AlpacaPaperTrading;
  private alpacaClient: AlpacaIntegration;
  private currentDate: Date;
  private marketData: Map<string, MarketData[]> = new Map();
  private optionsData: Map<string, OptionsChain[]> = new Map();
  private trades: BacktestTrade[] = [];
  private dailyMetrics: DailyMetrics[] = [];
  private equityCurve: { date: Date; equity: number; drawdown: number }[] = [];

  constructor(config: BacktestConfig, alpacaClient: AlpacaIntegration) {
    super();
    this.config = config;
    this.alpacaClient = alpacaClient;
    this.currentDate = new Date(config.startDate);

    // Initialize paper trading engine
    const paperConfig: PaperTradingConfig = {
      initialBalance: config.initialBalance,
      commissionPerContract: config.commissionPerContract,
      bidAskSpreadPercent: config.bidAskSpreadPercent,
      slippagePercent: config.slippagePercent,
      maxPositions: config.strategy.maxPositions,
      riskFreeRate: config.riskFreeRate
    };

    this.paperTrading = new AlpacaPaperTrading(paperConfig);
    this.setupEventHandlers();
  }

  private setupEventHandlers(): void {
    this.paperTrading.on('trade_executed', (trade) => {
      this.emit('trade_executed', trade);
    });

    this.paperTrading.on('order_filled', (order) => {
      this.emit('order_filled', order);
    });
  }

  // Load historical data
  async loadHistoricalData(): Promise<void> {
    console.log(`📊 Loading historical data for ${this.config.underlyingSymbol}...`);
    
    try {
      // Load underlying stock data
      const stockBars = await this.alpacaClient.getStockBars(
        this.config.underlyingSymbol,
        '1Min',
        this.config.startDate,
        this.config.endDate,
        10000
      );

      // Convert to MarketData format
      const marketData: MarketData[] = stockBars.map(bar => ({
        timestamp: new Date(bar.t),
        open: bar.o,
        high: bar.h,
        low: bar.l,
        close: bar.c,
        volume: bar.v
      }));

      this.marketData.set(this.config.underlyingSymbol, marketData);

      // Load options data for each trading day
      await this.loadOptionsData();

      console.log(`✅ Loaded ${marketData.length} bars of market data`);
    } catch (error) {
      console.error('Error loading historical data:', error);
      throw error;
    }
  }

  private async loadOptionsData(): Promise<void> {
    const marketData = this.marketData.get(this.config.underlyingSymbol);
    if (!marketData) return;

    // Group data by date to get daily options chains
    const dailyData = new Map<string, MarketData[]>();
    marketData.forEach(bar => {
      const dateKey = bar.timestamp.toISOString().split('T')[0];
      if (!dailyData.has(dateKey)) {
        dailyData.set(dateKey, []);
      }
      dailyData.get(dateKey)!.push(bar);
    });

    // For each trading day, simulate options chain
    for (const [dateKey, dayBars] of dailyData) {
      const date = new Date(dateKey);
      const lastBar = dayBars[dayBars.length - 1];
      
      // Generate synthetic options chain for 0DTE trading
      const optionsChain = this.generateSyntheticOptionsChain(
        lastBar.close,
        date,
        0.20 // Assumed volatility
      );

      this.optionsData.set(dateKey, optionsChain);
    }

    console.log(`✅ Generated options data for ${dailyData.size} trading days`);
  }

  private generateSyntheticOptionsChain(
    underlyingPrice: number,
    date: Date,
    impliedVol: number
  ): OptionsChain[] {
    const chain: OptionsChain[] = [];
    const strikes = this.generateStrikes(underlyingPrice);
    
    // Create 0DTE options (expiring same day)
    const expiration = new Date(date);
    expiration.setHours(16, 0, 0, 0); // 4 PM expiration

    const timeToExpiration = GreeksSimulator.timeToExpiration(expiration, date);

    strikes.forEach(strike => {
      // Generate CALL option
      const callInputs: OptionPricingInputs = {
        underlyingPrice,
        strikePrice: strike,
        timeToExpiration,
        riskFreeRate: this.config.riskFreeRate,
        volatility: impliedVol,
        optionType: 'call'
      };

      const callResult = GreeksSimulator.calculateOptionPrice(callInputs);
      const callSpread = callResult.theoreticalPrice * 0.05; // 5% bid-ask spread

      chain.push({
        symbol: `SPY${expiration.toISOString().slice(0, 10).replace(/-/g, '')}C${strike.toString().padStart(8, '0')}`,
        strike,
        expiration: expiration,
        type: 'CALL',
        bid: Math.max(0.01, callResult.theoreticalPrice - callSpread / 2),
        ask: callResult.theoreticalPrice + callSpread / 2,
        last: callResult.theoreticalPrice,
        impliedVolatility: impliedVol,
        delta: callResult.delta,
        gamma: callResult.gamma,
        theta: callResult.theta,
        vega: callResult.vega,
        volume: Math.floor(Math.random() * 1000) + 100,
        openInterest: Math.floor(Math.random() * 5000) + 500
      });

      // Generate PUT option
      const putInputs: OptionPricingInputs = {
        ...callInputs,
        optionType: 'put'
      };

      const putResult = GreeksSimulator.calculateOptionPrice(putInputs);
      const putSpread = putResult.theoreticalPrice * 0.05;

      chain.push({
        symbol: `SPY${expiration.toISOString().slice(0, 10).replace(/-/g, '')}P${strike.toString().padStart(8, '0')}`,
        strike,
        expiration: expiration,
        type: 'PUT',
        bid: Math.max(0.01, putResult.theoreticalPrice - putSpread / 2),
        ask: putResult.theoreticalPrice + putSpread / 2,
        last: putResult.theoreticalPrice,
        impliedVolatility: impliedVol,
        delta: putResult.delta,
        gamma: putResult.gamma,
        theta: putResult.theta,
        vega: putResult.vega,
        volume: Math.floor(Math.random() * 1000) + 100,
        openInterest: Math.floor(Math.random() * 5000) + 500
      });
    });

    return chain;
  }

  private generateStrikes(underlyingPrice: number): number[] {
    const strikes: number[] = [];
    const baseStrike = Math.round(underlyingPrice);
    const strikeInterval = underlyingPrice > 100 ? 5 : 1;
    
    // Generate strikes from 20% below to 20% above current price
    const minStrike = baseStrike * 0.8;
    const maxStrike = baseStrike * 1.2;

    for (let strike = minStrike; strike <= maxStrike; strike += strikeInterval) {
      strikes.push(Math.round(strike / strikeInterval) * strikeInterval);
    }

    return strikes;
  }

  // Run backtest
  async runBacktest(strategyFunction: (data: MarketData[], options: OptionsChain[]) => TradeSignal | null): Promise<BacktestResult> {
    console.log(`🚀 Starting backtest from ${this.config.startDate.toDateString()} to ${this.config.endDate.toDateString()}`);
    
    const marketData = this.marketData.get(this.config.underlyingSymbol);
    if (!marketData) {
      throw new Error('No market data loaded');
    }

    let dataIndex = 0;
    const totalBars = marketData.length;
    let lastProgressUpdate = 0;

    // Process each bar
    while (dataIndex < totalBars && this.currentDate <= this.config.endDate) {
      const currentBar = marketData[dataIndex];
      this.currentDate = new Date(currentBar.timestamp);

      // Update progress
      const progress = (dataIndex / totalBars) * 100;
      if (progress - lastProgressUpdate >= 10) {
        console.log(`📈 Backtest progress: ${progress.toFixed(1)}%`);
        lastProgressUpdate = progress;
        this.emit('progress', progress);
      }

      // Get options data for current date
      const dateKey = this.currentDate.toISOString().split('T')[0];
      const optionsChain = this.optionsData.get(dateKey) || [];

      // Update paper trading with current market data
      this.paperTrading.updateMarketData(this.config.underlyingSymbol, currentBar);
      this.paperTrading.updateOptionsChain(this.config.underlyingSymbol, optionsChain);

      // Get recent bars for strategy analysis
      const recentBars = marketData.slice(Math.max(0, dataIndex - 100), dataIndex + 1);
      
      // Generate trade signal
      const signal = strategyFunction(recentBars, optionsChain);
      
      if (signal) {
        // Execute trade through paper trading engine
        await this.paperTrading.executeTradeSignal(signal, this.config.underlyingSymbol);
      }

      // Check for position exits based on time, profit targets, stop losses
      await this.checkPositionExits(currentBar, optionsChain);

      // Record daily metrics
      if (this.isEndOfDay(currentBar.timestamp)) {
        this.recordDailyMetrics();
      }

      dataIndex++;
    }

    console.log('✅ Backtest completed, generating results...');
    return this.generateResults();
  }

  private async checkPositionExits(currentBar: MarketData, optionsChain: OptionsChain[]): Promise<void> {
    const metrics = this.paperTrading.getAccountMetrics();
    
    for (const position of metrics.positions) {
      let shouldExit = false;
      let exitReason: BacktestTrade['exitReason'] = 'SIGNAL_EXIT';

      // Check profit target
      if (position.unrealizedPnLPercent >= this.config.strategy.takeProfitPercent) {
        shouldExit = true;
        exitReason = 'PROFIT_TARGET';
      }

      // Check stop loss
      if (position.unrealizedPnLPercent <= -this.config.strategy.stopLossPercent) {
        shouldExit = true;
        exitReason = 'STOP_LOSS';
      }

      // Check time decay for 0DTE options
      if (position.is0DTE) {
        const minutesToExpiration = (position.expiration.getTime() - this.currentDate.getTime()) / (1000 * 60);
        
        if (minutesToExpiration <= this.config.strategy.timeDecayExitMinutes) {
          shouldExit = true;
          exitReason = 'TIME_DECAY';
        }
      }

      // Check maximum holding time
      const holdingMinutes = (this.currentDate.getTime() - position.openedAt.getTime()) / (1000 * 60);
      if (holdingMinutes >= this.config.strategy.maxHoldingTimeMinutes) {
        shouldExit = true;
        exitReason = 'TIME_DECAY';
      }

      // Check end of day
      if (this.isEndOfDay(this.currentDate)) {
        shouldExit = true;
        exitReason = 'EOD';
      }

      if (shouldExit) {
        await this.exitPosition(position, exitReason);
      }
    }
  }

  private async exitPosition(position: any, exitReason: BacktestTrade['exitReason']): Promise<void> {
    try {
      await this.paperTrading.submitOrder({
        symbol: position.symbol,
        side: 'SELL',
        quantity: position.quantity,
        orderType: 'MARKET'
      });

      // Record the trade details for analysis
      // This would be enhanced to capture more detailed trade information
    } catch (error) {
      console.error('Error exiting position:', error);
    }
  }

  private isEndOfDay(timestamp: Date): boolean {
    const hour = timestamp.getHours();
    const minute = timestamp.getMinutes();
    return hour === 15 && minute >= 45; // 3:45 PM or later
  }

  private recordDailyMetrics(): void {
    const metrics = this.paperTrading.getAccountMetrics();
    const dateKey = this.currentDate.toISOString().split('T')[0];

    const dailyMetric: DailyMetrics = {
      date: new Date(dateKey),
      trades: metrics.todayTrades.length,
      pnl: metrics.dayPnL,
      winRate: metrics.winRate,
      maxDrawdown: metrics.maxDrawdown,
      sharpeRatio: metrics.sharpeRatio,
      totalVolume: metrics.todayTrades.length * 1000, // Approximate volume per trade
      avgHoldTime: this.calculateAverageHoldTime(metrics.todayTrades),
      totalPnL: metrics.dayPnL,
      totalTrades: metrics.todayTrades.length,
      winningTrades: metrics.todayTrades.filter(t => (t.pnl || 0) > 0).length,
      losingTrades: metrics.todayTrades.filter(t => (t.pnl || 0) < 0).length,
      maxProfit: Math.max(...metrics.todayTrades.map(t => t.pnl || 0), 0)
    };

    this.dailyMetrics.push(dailyMetric);

    // Record equity curve point
    this.equityCurve.push({
      date: new Date(dateKey),
      equity: metrics.equity,
      drawdown: metrics.maxDrawdown
    });
  }

  private calculateAverageHoldTime(trades: any[]): number {
    if (trades.length === 0) return 0;
    
    // This is simplified - in practice, you'd track entry and exit times
    return trades.reduce((sum, trade) => sum + 60, 0) / trades.length; // Assume 60 minutes average
  }

  // Generate comprehensive backtest results
  private generateResults(): BacktestResult {
    const finalMetrics = this.paperTrading.getAccountMetrics();
    const tradingData = this.paperTrading.exportTradingData();

    // Calculate summary statistics
    const totalReturn = finalMetrics.equity - this.config.initialBalance;
    const totalReturnPercent = (totalReturn / this.config.initialBalance) * 100;
    
    const tradingDays = this.dailyMetrics.length;
    const annualizedReturn = tradingDays > 0 ? 
      (Math.pow(finalMetrics.equity / this.config.initialBalance, 252 / tradingDays) - 1) * 100 : 0;

    // Calculate additional risk metrics
    const dailyReturns = this.dailyMetrics.map(d => d.totalPnL);
    const volatility = this.calculateVolatility(dailyReturns);
    const sortinoRatio = this.calculateSortinoRatio(dailyReturns);

    // Find consecutive wins/losses
    const { consecutiveWins, consecutiveLosses } = this.calculateConsecutiveWinsLosses(tradingData.trades);

    // Calculate monthly returns
    const monthlyReturns = this.calculateMonthlyReturns();

    const summary = {
      totalReturn,
      totalReturnPercent,
      annualizedReturn,
      maxDrawdown: finalMetrics.maxDrawdown * 100,
      sharpeRatio: finalMetrics.sharpeRatio,
      sortinoRatio,
      winRate: finalMetrics.winRate * 100,
      profitFactor: finalMetrics.profitFactor,
      totalTrades: finalMetrics.totalTrades,
      avgTradeReturn: finalMetrics.totalTrades > 0 ? totalReturn / finalMetrics.totalTrades : 0,
      avgWinningTrade: finalMetrics.averageWin,
      avgLosingTrade: finalMetrics.averageLoss,
      largestWin: Math.max(...tradingData.trades.map(t => t.pnl || 0), 0),
      largestLoss: Math.min(...tradingData.trades.map(t => t.pnl || 0), 0),
      consecutiveWins,
      consecutiveLosses
    };

    const riskMetrics = {
      volatility,
      beta: 0, // Would need benchmark data to calculate
      alpha: 0, // Would need benchmark data to calculate
      informationRatio: 0, // Would need benchmark data to calculate
      calmarRatio: annualizedReturn / Math.max(finalMetrics.maxDrawdown * 100, 0.01)
    };

    return {
      summary,
      dailyMetrics: this.dailyMetrics,
      trades: [], // Would need to convert paper trades to BacktestTrade format
      equityCurve: this.equityCurve,
      monthlyReturns,
      riskMetrics
    };
  }

  private calculateVolatility(returns: number[]): number {
    if (returns.length < 2) return 0;
    
    const mean = returns.reduce((sum, ret) => sum + ret, 0) / returns.length;
    const variance = returns.reduce((sum, ret) => sum + Math.pow(ret - mean, 2), 0) / (returns.length - 1);
    return Math.sqrt(variance * 252); // Annualized volatility
  }

  private calculateSortinoRatio(returns: number[]): number {
    if (returns.length === 0) return 0;
    
    const mean = returns.reduce((sum, ret) => sum + ret, 0) / returns.length;
    const negativeReturns = returns.filter(ret => ret < 0);
    
    if (negativeReturns.length === 0) return mean > 0 ? Infinity : 0;
    
    const downside = Math.sqrt(negativeReturns.reduce((sum, ret) => sum + ret * ret, 0) / negativeReturns.length);
    return downside > 0 ? (mean / downside) * Math.sqrt(252) : 0;
  }

  private calculateConsecutiveWinsLosses(trades: any[]): { consecutiveWins: number; consecutiveLosses: number } {
    let maxConsecutiveWins = 0;
    let maxConsecutiveLosses = 0;
    let currentWins = 0;
    let currentLosses = 0;

    trades.forEach(trade => {
      const pnl = trade.pnl || 0;
      
      if (pnl > 0) {
        currentWins++;
        currentLosses = 0;
        maxConsecutiveWins = Math.max(maxConsecutiveWins, currentWins);
      } else if (pnl < 0) {
        currentLosses++;
        currentWins = 0;
        maxConsecutiveLosses = Math.max(maxConsecutiveLosses, currentLosses);
      }
    });

    return {
      consecutiveWins: maxConsecutiveWins,
      consecutiveLosses: maxConsecutiveLosses
    };
  }

  private calculateMonthlyReturns(): { month: string; return: number }[] {
    const monthlyData = new Map<string, number>();
    
    this.dailyMetrics.forEach(daily => {
      const monthKey = daily.date.toISOString().slice(0, 7); // YYYY-MM
      const currentReturn = monthlyData.get(monthKey) || 0;
      monthlyData.set(monthKey, currentReturn + daily.totalPnL);
    });

    return Array.from(monthlyData.entries()).map(([month, returnValue]) => ({
      month,
      return: returnValue
    }));
  }

  // Utility methods
  getProgress(): number {
    const marketData = this.marketData.get(this.config.underlyingSymbol);
    if (!marketData) return 0;
    
    const totalDays = (this.config.endDate.getTime() - this.config.startDate.getTime()) / (1000 * 60 * 60 * 24);
    const elapsedDays = (this.currentDate.getTime() - this.config.startDate.getTime()) / (1000 * 60 * 60 * 24);
    
    return Math.min(100, (elapsedDays / totalDays) * 100);
  }

  getCurrentMetrics(): any {
    return this.paperTrading.getAccountMetrics();
  }

  // Export results for external analysis
  exportResults(format: 'json' | 'csv' = 'json'): string {
    const results = this.generateResults();
    
    if (format === 'json') {
      return JSON.stringify(results, null, 2);
    } else {
      // Convert to CSV format (simplified)
      const csvData = this.dailyMetrics.map(daily => ({
        date: daily.date.toISOString().split('T')[0],
        totalPnL: daily.totalPnL,
        totalTrades: daily.totalTrades,
        winRate: daily.winRate,
        maxDrawdown: daily.maxDrawdown
      }));
      
      const headers = Object.keys(csvData[0] || {}).join(',');
      const rows = csvData.map(row => Object.values(row).join(','));
      return [headers, ...rows].join('\n');
    }
  }
}
