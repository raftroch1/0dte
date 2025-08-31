
import { EventEmitter } from 'events';
import { MarketData, OptionsChain, TradeSignal, Strategy, DailyMetrics } from '../utils/types';
import { AlpacaPaperTrading, PaperTradingConfig } from '../trading/alpaca-paper-trading';
import { GreeksSimulator, OptionPricingInputs } from '../data/greeks-simulator';
import { AlpacaIntegration } from './alpaca-integration';
import { StrategyBacktestingAdapter } from './strategy-backtesting-adapter';
import { TradeLogger } from '../utils/trade-logger';
import { StrategyRegistry } from '../strategies/registry';

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
  private strategyAdapter: StrategyBacktestingAdapter | null = null;
  private tradeLogger: TradeLogger;
  private positionToTradeIdMap: Map<string, string> = new Map(); // Maps position keys to trade IDs

  constructor(config: BacktestConfig, alpacaClient: AlpacaIntegration, strategyName: string = 'unknown') {
    super();
    this.config = config;
    this.alpacaClient = alpacaClient;
    this.currentDate = new Date(config.startDate);
    
    // Initialize trade logger
    const dateRange = `${config.startDate.toISOString().split('T')[0]}_to_${config.endDate.toISOString().split('T')[0]}`;
    this.tradeLogger = new TradeLogger(strategyName, dateRange);

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
      // Load strategy-specific backtesting adapter
      await this.loadStrategyAdapter();
      
      // Load underlying stock data - Use 15-minute bars for optimal Flyagonal analysis
      // 15-minute bars provide best balance: sufficient data + realistic VIX + trade generation
      // ~26 bars per trading day allows precise multi-day strategy execution
      const stockBars = await this.alpacaClient.getStockBars(
        this.config.underlyingSymbol,
        '15Min',
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

      // Load options data for each trading day (strategy-specific or default)
      await this.loadOptionsData();

      // Pass strategy adapter to paper trading system
      if (this.strategyAdapter) {
        this.paperTrading.setStrategyAdapter(this.strategyAdapter);
      }

      console.log(`✅ Loaded ${marketData.length} bars of market data`);
    } catch (error) {
      console.error('Error loading historical data:', error);
      throw error;
    }
  }

  /**
   * Load strategy-specific backtesting adapter
   * This enables custom options generation and position management per strategy
   */
  private async loadStrategyAdapter(): Promise<void> {
    const strategyName = this.config.strategy.name;
    if (!strategyName) {
      console.log('📊 No strategy name provided, using default backtesting behavior');
      return;
    }

    try {
      this.strategyAdapter = await StrategyRegistry.loadBacktestingAdapter(strategyName);
      if (this.strategyAdapter) {
        console.log(`🎯 Using strategy-specific backtesting adapter for: ${strategyName}`);
      } else {
        console.log(`📊 No custom adapter for ${strategyName}, using default backtesting behavior`);
      }
    } catch (error) {
      console.warn(`⚠️ Failed to load adapter for ${strategyName}, using default behavior:`, error);
    }
  }

  private async loadOptionsData(): Promise<void> {
    const marketData = this.marketData.get(this.config.underlyingSymbol);
    if (!marketData) return;

    console.log(`📊 Loading REAL options data from Alpaca API for ${this.config.underlyingSymbol}...`);

    // Group data by date to get daily options chains
    const dailyData = new Map<string, MarketData[]>();
    marketData.forEach(bar => {
      const dateKey = bar.timestamp.toISOString().split('T')[0];
      if (!dailyData.has(dateKey)) {
        dailyData.set(dateKey, []);
      }
      dailyData.get(dateKey)!.push(bar);
    });

    // For each trading day, fetch REAL options data from Alpaca (per .cursorrules)
    let successfulDays = 0;

    for (const [dateKey, dayBars] of dailyData) {
      const date = new Date(dateKey);
      const lastBar = dayBars[dayBars.length - 1];
      
      let optionsChain: OptionsChain[];
      
      try {
        // 🎯 FETCH HISTORICAL OPTIONS DATA FROM ALPACA API
        console.log(`🔍 Fetching HISTORICAL options for ${this.config.underlyingSymbol} on ${dateKey}...`);
        
        // Use the new historical options API to get options that existed on this specific date
        let realOptionsChain: OptionsChain[] = [];
        realOptionsChain = await this.alpacaClient.getHistoricalOptionsChain(this.config.underlyingSymbol, date);
        
        console.log(`   Found ${realOptionsChain.length} historical options contracts for ${dateKey}`);
        
        if (realOptionsChain && realOptionsChain.length > 0) {
          // Filter for relevant strikes and calculate Greeks
          optionsChain = this.processRealOptionsData(realOptionsChain, lastBar.close, date);
          console.log(`✅ Loaded ${optionsChain.length} REAL options contracts for ${dateKey}`);
          successfulDays++;
        } else {
          throw new Error('No real options data available');
        }
        
      } catch (error) {
        console.error(`❌ CRITICAL: Failed to fetch real options data for ${dateKey}:`, error);
        console.error(`❌ .cursorrules VIOLATION: Synthetic/fallback data is prohibited`);
        console.error(`❌ Backtesting cannot continue without real Alpaca options data`);
        throw new Error(`Real options data required per .cursorrules - cannot use synthetic data for ${dateKey}`);
      }

      this.optionsData.set(dateKey, optionsChain);
    }

    console.log(`✅ Options data loaded: ${successfulDays} days with REAL data only (per .cursorrules)`);
    
    if (successfulDays === 0) {
      throw new Error(`CRITICAL: No real options data was loaded! .cursorrules prohibits synthetic data.`);
    }
  }



  /**
   * Process real options data from Alpaca API
   * - Filter for relevant strikes around current price
   * - Calculate missing Greeks using GreeksSimulator
   * - Preserve real bid/ask/last prices
   */
  private processRealOptionsData(
    realOptions: OptionsChain[], 
    currentPrice: number, 
    currentDate: Date
  ): OptionsChain[] {
    const processedOptions: OptionsChain[] = [];
    
    // Filter for options within reasonable strike range (±30% for 0DTE trading)
    // 0DTE options need wider range due to volatility and intraday movements
    const minStrike = currentPrice * 0.7;
    const maxStrike = currentPrice * 1.3;
    
    // For 0DTE trading, we want options expiring on the same day or very close
    // Allow up to 3 days for flexibility in case exact 0DTE options aren't available
    const maxExpiration = new Date(currentDate.getTime() + 3 * 24 * 60 * 60 * 1000);
    const minExpiration = new Date(currentDate.getTime() - 1 * 24 * 60 * 60 * 1000); // Allow 1 day before
    
    console.log(`🔍 Filtering options for ${currentDate.toISOString().split('T')[0]}:`);
    console.log(`   Strike range: $${minStrike.toFixed(0)} - $${maxStrike.toFixed(0)} (current: $${currentPrice.toFixed(2)})`);
    console.log(`   Expiration range: ${minExpiration.toISOString().split('T')[0]} to ${maxExpiration.toISOString().split('T')[0]}`);
    
    for (const option of realOptions) {
      // Filter by strike range and expiration
      if (option.strike >= minStrike && 
          option.strike <= maxStrike && 
          option.expiration >= minExpiration &&
          option.expiration <= maxExpiration) {
        
        // Calculate missing Greeks using our GreeksSimulator
        const timeToExpiration = GreeksSimulator.timeToExpiration(option.expiration, currentDate);
        
        if (timeToExpiration > 0) {
          const pricingInputs: OptionPricingInputs = {
            underlyingPrice: currentPrice,
            strikePrice: option.strike,
            timeToExpiration,
            riskFreeRate: this.config.riskFreeRate,
            volatility: option.impliedVolatility || 0.25, // Use real IV if available, fallback to 25%
            optionType: option.type.toLowerCase() as 'call' | 'put'
          };
          
          const greeksResult = GreeksSimulator.calculateOptionPrice(pricingInputs);
          
          // Create enhanced option with real prices + calculated Greeks
          const enhancedOption: OptionsChain = {
            ...option, // Keep all real data (bid, ask, last, volume, openInterest)
            // Add calculated Greeks (directly from OptionPriceResult)
            delta: greeksResult.delta,
            gamma: greeksResult.gamma,
            theta: greeksResult.theta,
            vega: greeksResult.vega,
            rho: greeksResult.rho,
            // Use real implied volatility if available, otherwise estimate from prices
            impliedVolatility: option.impliedVolatility || this.estimateImpliedVolatility(option, currentPrice, timeToExpiration)
          };
          
          processedOptions.push(enhancedOption);
        }
      }
    }
    
    console.log(`✅ Filtered ${processedOptions.length} relevant options from ${realOptions.length} total contracts`);
    
    if (processedOptions.length === 0) {
      console.warn(`⚠️ NO OPTIONS MATCHED FILTERS!`);
      console.warn(`   Available strikes: ${realOptions.map(o => o.strike).sort((a,b) => a-b).slice(0, 10).join(', ')}${realOptions.length > 10 ? '...' : ''}`);
      console.warn(`   Available expirations: ${[...new Set(realOptions.map(o => o.expiration.toISOString().split('T')[0]))].slice(0, 5).join(', ')}`);
      console.warn(`   Current price: $${currentPrice.toFixed(2)}, Date: ${currentDate.toISOString().split('T')[0]}`);
    } else {
      console.log(`   ✅ Selected strikes: ${processedOptions.map(o => `${o.type}${o.strike}`).slice(0, 10).join(', ')}`);
      console.log(`   ✅ Expirations: ${[...new Set(processedOptions.map(o => o.expiration.toISOString().split('T')[0]))].join(', ')}`);
    }
    
    return processedOptions;
  }

  /**
   * Estimate implied volatility from option prices when not provided
   */
  private estimateImpliedVolatility(option: OptionsChain, underlyingPrice: number, timeToExpiration: number): number {
    // Simple estimation based on option price relative to intrinsic value
    const intrinsicValue = option.type === 'CALL' 
      ? Math.max(0, underlyingPrice - option.strike)
      : Math.max(0, option.strike - underlyingPrice);
    
    const timeValue = Math.max(0, option.last - intrinsicValue);
    
    // Rough estimation: higher time value suggests higher IV
    if (timeValue <= 0 || timeToExpiration <= 0) return 0.20; // Default 20%
    
    // Simple heuristic: time value as percentage of underlying price
    const estimatedIV = Math.min(2.0, Math.max(0.1, (timeValue / underlyingPrice) * Math.sqrt(365 / (timeToExpiration * 365))));
    
    return estimatedIV;
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
  async runBacktest(strategyFunction: (data: MarketData[], options: OptionsChain[]) => TradeSignal | null | Promise<TradeSignal | null>): Promise<BacktestResult> {
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
      
      // Generate trade signal (handle both sync and async strategies)
      const signal = await Promise.resolve(strategyFunction(recentBars, optionsChain));
      
      if (signal) {
        // Execute trade through paper trading engine
        const order = await this.paperTrading.executeTradeSignal(signal, this.config.underlyingSymbol);
        
        // Log trade entry if order was successful
        if (order) {
          this.logTradeEntry(signal, order, currentBar);
        }
      }

      // Check for position exits based on time, profit targets, stop losses
      await this.checkPositionExits(currentBar, optionsChain);

      // Record daily metrics
      if (this.isEndOfDay(currentBar.timestamp)) {
        this.recordDailyMetrics();
      }

      dataIndex++;
    }

    console.log('✅ Backtest completed, closing remaining positions...');
    
    // Close all remaining positions at the end of backtest
    const remainingPositions = await this.paperTrading.closeAllPositions();
    for (const closedTrade of remainingPositions) {
      const backtestTrade: BacktestTrade = {
        id: closedTrade.id,
        entryDate: new Date(), // We'll need to get this from position data
        exitDate: closedTrade.timestamp,
        symbol: closedTrade.symbol,
        side: 'BUY',
        quantity: closedTrade.quantity,
        entryPrice: 0, // We'll need to get this from position data
        exitPrice: closedTrade.price,
        pnl: closedTrade.pnl || 0,
        pnlPercent: 0,
        commission: this.config.commissionPerContract * closedTrade.quantity,
        slippage: 0,
        holdingPeriod: 0,
        signal: {} as TradeSignal,
        exitReason: 'EOD',
        greeksAtEntry: { delta: 0, gamma: 0, theta: 0, vega: 0 },
        greeksAtExit: { delta: 0, gamma: 0, theta: 0, vega: 0 }
      };
      this.trades.push(backtestTrade);
    }
    
    console.log(`📊 Total completed trades: ${this.trades.length}`);
    
    // Finalize trade logging and generate comprehensive logs
    this.tradeLogger.finalize();
    
    console.log('🔄 Generating results...');
    return this.generateResults();
  }

  private async checkPositionExits(currentBar: MarketData, optionsChain: OptionsChain[]): Promise<void> {
    const metrics = this.paperTrading.getAccountMetrics();
    
    if (metrics.positions.length > 0) {
      console.log(`🔍 Checking ${metrics.positions.length} positions for exits at ${this.currentDate.toISOString()}`);
      
      // Log detailed position info
      for (const pos of metrics.positions) {
        const holdTime = (this.currentDate.getTime() - pos.openedAt.getTime()) / (1000 * 60); // minutes
        console.log(`   📊 Position ${pos.id}: Entry=$${pos.averagePrice.toFixed(2)}, Current=$${pos.currentPrice.toFixed(2)}, P&L=$${pos.unrealizedPnL.toFixed(2)}, Hold=${holdTime.toFixed(0)}min`);
      }
    }
    
    for (const position of metrics.positions) {
      let shouldExit = false;
      let exitReason: BacktestTrade['exitReason'] = 'SIGNAL_EXIT';

      // Check profit target
      if (position.unrealizedPnLPercent >= this.config.strategy.takeProfitPercent) {
        shouldExit = true;
        exitReason = 'PROFIT_TARGET';
        console.log(`   ✅ PROFIT TARGET HIT: ${position.id} - P&L: ${position.unrealizedPnLPercent.toFixed(2)}% >= ${this.config.strategy.takeProfitPercent}%`);
      }

      // Check stop loss
      if (position.unrealizedPnLPercent <= -this.config.strategy.stopLossPercent) {
        shouldExit = true;
        exitReason = 'STOP_LOSS';
        console.log(`   🛑 STOP LOSS HIT: ${position.id} - P&L: ${position.unrealizedPnLPercent.toFixed(2)}% <= -${this.config.strategy.stopLossPercent}%`);
      }

      // Check time decay for 0DTE options
      if (position.is0DTE) {
        const minutesToExpiration = (position.expiration.getTime() - this.currentDate.getTime()) / (1000 * 60);
        
        if (minutesToExpiration <= this.config.strategy.timeDecayExitMinutes) {
          shouldExit = true;
          exitReason = 'TIME_DECAY';
          console.log(`   ⚡ 0DTE TIME DECAY: ${position.id} - ${minutesToExpiration.toFixed(0)}min to expiry <= ${this.config.strategy.timeDecayExitMinutes}min`);
        }
      }

      // Check maximum holding time
      const holdingMinutes = (this.currentDate.getTime() - position.openedAt.getTime()) / (1000 * 60);
      if (holdingMinutes >= this.config.strategy.maxHoldingTimeMinutes) {
        shouldExit = true;
        exitReason = 'TIME_DECAY';
        console.log(`   ⏰ MAX HOLD TIME: ${position.id} - Held: ${holdingMinutes.toFixed(0)}min >= ${this.config.strategy.maxHoldingTimeMinutes}min`);
      }

      // Check end of day
      if (this.isEndOfDay(this.currentDate)) {
        shouldExit = true;
        exitReason = 'EOD';
        console.log(`   🌅 END OF DAY: ${position.id} - Closing at EOD`);
      }

      if (shouldExit) {
        console.log(`🚪 EXITING POSITION: ${position.id || position.symbol} due to ${exitReason}`);
        await this.exitPosition(position, exitReason);
      } else {
        console.log(`   ⏳ HOLDING: ${position.id} - No exit conditions met (P&L: ${position.unrealizedPnLPercent.toFixed(2)}%, Hold: ${holdingMinutes.toFixed(0)}min)`);
      }
    }
  }

  private async exitPosition(position: any, exitReason: BacktestTrade['exitReason']): Promise<void> {
    try {
      // Use the proper closePosition method with the correct position identifier
      // For strategy-specific positions, use the position ID, otherwise use symbol
      const positionKey = position.id || position.symbol;
      const closedTrade = await this.paperTrading.closePosition(positionKey);
      
      if (closedTrade) {
        // Create a BacktestTrade record for analysis
        const backtestTrade: BacktestTrade = {
          id: closedTrade.id,
          entryDate: position.openedAt,
          exitDate: closedTrade.timestamp,
          symbol: position.symbol,
          side: 'BUY', // Original entry was BUY
          quantity: position.quantity,
          entryPrice: position.averagePrice,
          exitPrice: closedTrade.price,
          pnl: closedTrade.pnl || 0,
          pnlPercent: position.averagePrice !== 0 ? (closedTrade.pnl || 0) / (position.averagePrice * position.quantity * 100) * 100 : 0,
          commission: this.config.commissionPerContract * position.quantity,
          slippage: 0,
          holdingPeriod: (closedTrade.timestamp.getTime() - position.openedAt.getTime()) / (1000 * 60), // minutes
          signal: {} as TradeSignal, // We'll need to store the original signal
          exitReason: exitReason,
          greeksAtEntry: position.greeks || { delta: 0, gamma: 0, theta: 0, vega: 0 },
          greeksAtExit: position.greeks || { delta: 0, gamma: 0, theta: 0, vega: 0 }
        };
        
        this.trades.push(backtestTrade);
        
        // Log trade exit for comprehensive analysis
        const tradeId = this.positionToTradeIdMap.get(positionKey);
        if (tradeId) {
          this.logTradeExit(
            tradeId, 
            closedTrade.price, 
            exitReason, 
            {
              grossPnL: closedTrade.pnl || 0,
              netPnL: (closedTrade.pnl || 0) - (this.config.commissionPerContract * position.quantity),
              commission: this.config.commissionPerContract * position.quantity,
              maxDrawdown: position.maxDrawdown,
              maxProfit: position.maxProfit
            }
          );
          // Clean up the mapping
          this.positionToTradeIdMap.delete(positionKey);
        } else {
          console.warn(`⚠️ Trade ID not found for position ${positionKey} - exit logging skipped`);
        }
        
        console.log(`📊 Recorded completed trade: ${position.symbol} P&L: $${closedTrade.pnl?.toFixed(2)} (${exitReason})`);
      }
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

    // Use the completed trades from BacktestingEngine instead of paper trading metrics
    const completedTrades = this.trades;
    const winningTrades = completedTrades.filter(t => t.pnl > 0);
    const losingTrades = completedTrades.filter(t => t.pnl < 0);
    const winRate = completedTrades.length > 0 ? (winningTrades.length / completedTrades.length) * 100 : 0;
    const avgWin = winningTrades.length > 0 ? winningTrades.reduce((sum, t) => sum + t.pnl, 0) / winningTrades.length : 0;
    const avgLoss = losingTrades.length > 0 ? losingTrades.reduce((sum, t) => sum + t.pnl, 0) / losingTrades.length : 0;
    const profitFactor = Math.abs(avgLoss) > 0 ? Math.abs(avgWin * winningTrades.length) / Math.abs(avgLoss * losingTrades.length) : 0;

    const summary = {
      totalReturn,
      totalReturnPercent,
      annualizedReturn,
      maxDrawdown: finalMetrics.maxDrawdown * 100,
      sharpeRatio: finalMetrics.sharpeRatio,
      sortinoRatio,
      winRate,
      profitFactor,
      totalTrades: completedTrades.length,
      avgTradeReturn: completedTrades.length > 0 ? totalReturn / completedTrades.length : 0,
      avgWinningTrade: avgWin,
      avgLosingTrade: avgLoss,
      largestWin: Math.max(...completedTrades.map(t => t.pnl), 0),
      largestLoss: Math.min(...completedTrades.map(t => t.pnl), 0),
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

  /**
   * Log trade entry with comprehensive details
   */
  private logTradeEntry(signal: TradeSignal, order: any, marketData: MarketData): void {
    const tradeId = `${signal.action}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    // Extract legs information for Flyagonal strategies
    let legs: any[] | undefined;
    if (signal.flyagonalComponents) {
      legs = [];
      
      // Add butterfly legs
      if (signal.flyagonalComponents.butterfly) {
        const bf = signal.flyagonalComponents.butterfly;
        legs.push(
          { type: 'CALL', strike: bf.longLower, quantity: 1, side: 'BUY', entryPrice: 0 },
          { type: 'CALL', strike: bf.short, quantity: 2, side: 'SELL', entryPrice: 0 },
          { type: 'CALL', strike: bf.longUpper, quantity: 1, side: 'BUY', entryPrice: 0 }
        );
      }
      
      // Add diagonal legs
      if (signal.flyagonalComponents.diagonal) {
        const diag = signal.flyagonalComponents.diagonal;
        legs.push(
          { type: 'PUT', strike: diag.shortStrike, quantity: 1, side: 'SELL', entryPrice: 0 },
          { type: 'PUT', strike: diag.longStrike, quantity: 1, side: 'BUY', entryPrice: 0 }
        );
      }
    }

    this.tradeLogger.logTradeEntry({
      tradeId,
      strategy: this.strategyAdapter?.strategyName || 'unknown',
      symbol: order.symbol,
      entryTime: signal.timestamp || new Date(),
      entryPrice: order.fillPrice || 0,
      entryReason: signal.action,
      quantity: order.quantity,
      underlyingPrice: marketData.close,
      vixLevel: signal.metadata?.vixLevel || signal.confidence, // Use actual VIX level from strategy metadata
      marketRegime: signal.action.includes('CALL') ? 'BULLISH' : signal.action.includes('PUT') ? 'BEARISH' : 'NEUTRAL',
      legs,
      metadata: {
        signalConfidence: signal.confidence,
        stopLoss: signal.stopLoss,
        takeProfit: signal.takeProfit,
        positionSize: signal.positionSize,
        timestamp: signal.timestamp?.toISOString(),
        flyagonalComponents: signal.flyagonalComponents
      }
    });

    // Store mapping between position key and trade ID for exit logging
    const positionKey = order.symbol; // This should match what's used in closePosition
    this.positionToTradeIdMap.set(positionKey, tradeId);
  }

  /**
   * Log trade exit with P&L analysis
   */
  private logTradeExit(positionId: string, exitPrice: number, exitReason: string, pnlData: any): void {
    this.tradeLogger.logTradeExit(positionId, {
      exitTime: new Date(),
      exitPrice,
      exitReason,
      grossPnL: pnlData.grossPnL || 0,
      netPnL: pnlData.netPnL || 0,
      commission: pnlData.commission || 0,
      maxDrawdown: pnlData.maxDrawdown,
      maxProfit: pnlData.maxProfit
    });
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
