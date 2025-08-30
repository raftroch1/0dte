
import { EventEmitter } from 'events';
import { AlpacaIntegration } from './alpaca-integration';
import { AlpacaPaperTrading } from './alpaca-paper-trading_improved';
import { AdaptiveStrategySelector } from './adaptive-strategy-selector_improved';
import { MarketRegimeDetector } from './market-regime-detector_improved';
import { TechnicalAnalysis } from './technical-indicators_improved';
import { MarketData, OptionsChain, TradeSignal, Position, Strategy, AccountConfig } from './types';
import { GreeksSimulator } from './greeks-simulator';

export interface LiveTradingConfig {
  alpacaConfig: {
    apiKey: string;
    apiSecret: string;
    isPaper: boolean;
  };
  accountConfig: AccountConfig;
  strategy: Strategy;
  underlyingSymbol: string;
  enablePaperTrading: boolean;
  riskManagement: {
    maxDailyLoss: number;
    maxPositionSize: number;
    maxOpenPositions: number;
    stopLossPercent: number;
    takeProfitPercent: number;
  };
  notifications: {
    enableSlack?: boolean;
    enableEmail?: boolean;
    slackWebhook?: string;
    emailConfig?: any;
  };
}

export interface TradingSession {
  id: string;
  startTime: Date;
  endTime?: Date;
  totalTrades: number;
  totalPnL: number;
  maxDrawdown: number;
  winRate: number;
  isActive: boolean;
}

export interface RiskCheck {
  passed: boolean;
  violations: string[];
  riskScore: number; // 0-100, higher is riskier
}

export class LiveTradingConnector extends EventEmitter {
  private config: LiveTradingConfig;
  private alpacaClient: AlpacaIntegration;
  private paperTrading: AlpacaPaperTrading | null = null;
  private strategySelector: AdaptiveStrategySelector;
  private regimeDetector: MarketRegimeDetector;
  private technicalAnalysis: TechnicalAnalysis;
  
  private isRunning = false;
  private isPaused = false;
  private currentSession: TradingSession | null = null;
  private marketDataBuffer: MarketData[] = [];
  private currentOptionsChain: OptionsChain[] = [];
  private positions: Map<string, Position> = new Map();
  private lastSignalTime: Date = new Date(0);
  private dailyStats = {
    trades: 0,
    pnl: 0,
    maxDrawdown: 0,
    startingBalance: 0
  };

  // Risk management state
  private riskState = {
    dailyLossExceeded: false,
    maxPositionsReached: false,
    accountDrawdownExceeded: false,
    lastRiskCheck: new Date()
  };

  constructor(config: LiveTradingConfig) {
    super();
    this.config = config;
    
    // Initialize Alpaca client
    this.alpacaClient = new AlpacaIntegration({
      apiKey: config.alpacaConfig.apiKey,
      apiSecret: config.alpacaConfig.apiSecret,
      isPaper: config.alpacaConfig.isPaper
    });

    // Initialize paper trading if enabled
    if (config.enablePaperTrading) {
      this.paperTrading = new AlpacaPaperTrading({
        initialBalance: config.accountConfig.balance,
        commissionPerContract: 0.65,
        bidAskSpreadPercent: 0.02,
        slippagePercent: 0.001,
        maxPositions: config.riskManagement.maxOpenPositions,
        riskFreeRate: 0.05
      });
    }

    // Initialize strategy components
    this.strategySelector = new AdaptiveStrategySelector();
    this.regimeDetector = new MarketRegimeDetector();
    this.technicalAnalysis = new TechnicalAnalysis();

    this.setupEventHandlers();
  }

  private setupEventHandlers(): void {
    // Alpaca client events
    this.alpacaClient.on('authenticated', () => {
      console.log('✅ Live trading authenticated');
      this.emit('authenticated');
    });

    this.alpacaClient.on('trade_update', (update) => {
      this.handleTradeUpdate(update);
    });

    this.alpacaClient.on('quote', (quote) => {
      this.handleQuoteUpdate(quote);
    });

    this.alpacaClient.on('trade', (trade) => {
      this.handleTradeData(trade);
    });

    this.alpacaClient.on('bar', (bar) => {
      this.handleBarData(bar);
    });

    // Paper trading events
    if (this.paperTrading) {
      this.paperTrading.on('trade_executed', (trade) => {
        console.log('📊 Paper trade executed:', trade);
        this.emit('paper_trade_executed', trade);
      });

      this.paperTrading.on('order_filled', (order) => {
        console.log('✅ Paper order filled:', order);
        this.emit('paper_order_filled', order);
      });
    }
  }

  // Main trading control methods
  async start(): Promise<void> {
    if (this.isRunning) {
      throw new Error('Trading connector is already running');
    }

    console.log('🚀 Starting live trading connector...');
    
    try {
      // Test connection
      const connected = await this.alpacaClient.testConnection();
      if (!connected) {
        throw new Error('Failed to connect to Alpaca API');
      }

      // Connect to WebSocket streams
      await this.alpacaClient.connectStream();
      await this.alpacaClient.connectMarketDataStream();

      // Subscribe to trade updates
      await this.alpacaClient.subscribeToTradeUpdates();

      // Subscribe to market data
      await this.alpacaClient.subscribeToMarketData([this.config.underlyingSymbol], ['trades', 'quotes', 'bars']);

      // Load initial positions
      await this.loadCurrentPositions();

      // Start trading session
      this.startTradingSession();

      this.isRunning = true;
      this.emit('started');
      
      console.log('✅ Live trading connector started successfully');
      
      // Start main trading loop
      this.startTradingLoop();

    } catch (error) {
      console.error('❌ Failed to start live trading connector:', error);
      throw error;
    }
  }

  async stop(): Promise<void> {
    if (!this.isRunning) {
      return;
    }

    console.log('🛑 Stopping live trading connector...');
    
    this.isRunning = false;
    this.isPaused = false;

    // Close all positions if configured to do so
    if (this.config.riskManagement.maxDailyLoss > 0) {
      await this.closeAllPositions('SYSTEM_SHUTDOWN');
    }

    // Disconnect from streams
    this.alpacaClient.disconnect();

    // End trading session
    this.endTradingSession();

    this.emit('stopped');
    console.log('✅ Live trading connector stopped');
  }

  pause(): void {
    if (!this.isRunning) {
      return;
    }

    this.isPaused = true;
    this.emit('paused');
    console.log('⏸️ Live trading paused');
  }

  resume(): void {
    if (!this.isRunning || !this.isPaused) {
      return;
    }

    this.isPaused = false;
    this.emit('resumed');
    console.log('▶️ Live trading resumed');
  }

  // Trading session management
  private startTradingSession(): void {
    this.currentSession = {
      id: `session_${Date.now()}`,
      startTime: new Date(),
      totalTrades: 0,
      totalPnL: 0,
      maxDrawdown: 0,
      winRate: 0,
      isActive: true
    };

    // Reset daily stats
    this.dailyStats = {
      trades: 0,
      pnl: 0,
      maxDrawdown: 0,
      startingBalance: this.config.accountConfig.balance
    };

    this.emit('session_started', this.currentSession);
  }

  private endTradingSession(): void {
    if (this.currentSession) {
      this.currentSession.endTime = new Date();
      this.currentSession.isActive = false;
      this.emit('session_ended', this.currentSession);
    }
  }

  // Main trading loop
  private async startTradingLoop(): Promise<void> {
    const loopInterval = 1000; // 1 second

    const tradingLoop = async () => {
      if (!this.isRunning) {
        return;
      }

      try {
        // Check if market is open
        if (!this.alpacaClient.isMarketOpen()) {
          setTimeout(tradingLoop, loopInterval * 60); // Check every minute when market is closed
          return;
        }

        // Skip if paused
        if (this.isPaused) {
          setTimeout(tradingLoop, loopInterval);
          return;
        }

        // Perform risk checks
        const riskCheck = await this.performRiskCheck();
        if (!riskCheck.passed) {
          console.warn('⚠️ Risk check failed:', riskCheck.violations);
          this.handleRiskViolation(riskCheck);
          setTimeout(tradingLoop, loopInterval * 5); // Wait 5 seconds before next check
          return;
        }

        // Update market regime and technical indicators
        await this.updateMarketAnalysis();

        // Generate trading signals
        const signal = await this.generateTradingSignal();

        if (signal) {
          await this.processTradingSignal(signal);
        }

        // Check for position exits
        await this.checkPositionExits();

        // Update session metrics
        this.updateSessionMetrics();

      } catch (error) {
        console.error('Error in trading loop:', error);
        this.emit('error', error);
      }

      // Schedule next iteration
      setTimeout(tradingLoop, loopInterval);
    };

    // Start the loop
    tradingLoop();
  }

  // Market data handlers
  private handleTradeUpdate(update: any): void {
    console.log('📈 Trade update received:', update);
    
    // Update position tracking
    if (update.event === 'fill') {
      this.updatePositionFromFill(update);
    }

    this.emit('trade_update', update);
  }

  private handleQuoteUpdate(quote: any): void {
    // Update options chain with latest quotes
    this.updateOptionsChainFromQuote(quote);
    this.emit('quote_update', quote);
  }

  private handleTradeData(trade: any): void {
    // Convert to MarketData format and add to buffer
    const marketData: MarketData = {
      timestamp: new Date(trade.t),
      open: trade.p,
      high: trade.p,
      low: trade.p,
      close: trade.p,
      volume: trade.s
    };

    this.addToMarketDataBuffer(marketData);
    this.emit('trade_data', trade);
  }

  private handleBarData(bar: any): void {
    const marketData: MarketData = {
      timestamp: new Date(bar.t),
      open: bar.o,
      high: bar.h,
      low: bar.l,
      close: bar.c,
      volume: bar.v
    };

    this.addToMarketDataBuffer(marketData);
    this.emit('bar_data', bar);
  }

  private addToMarketDataBuffer(data: MarketData): void {
    this.marketDataBuffer.push(data);
    
    // Keep only last 200 bars for analysis
    if (this.marketDataBuffer.length > 200) {
      this.marketDataBuffer.shift();
    }

    // Update paper trading if enabled
    if (this.paperTrading) {
      this.paperTrading.updateMarketData(this.config.underlyingSymbol, data);
    }
  }

  // Signal generation and processing
  private async generateTradingSignal(): Promise<TradeSignal | null> {
    if (this.marketDataBuffer.length < 50) {
      return null; // Need sufficient data
    }

    // Prevent too frequent signals
    const timeSinceLastSignal = Date.now() - this.lastSignalTime.getTime();
    if (timeSinceLastSignal < 60000) { // 1 minute minimum
      return null;
    }

    try {
      // Get current market regime
      const regime = this.regimeDetector.detectRegime(this.marketDataBuffer);
      
      // Calculate technical indicators
      const indicators = this.technicalAnalysis.calculateIndicators(this.marketDataBuffer);
      
      // Generate signal using adaptive strategy selector
      const strategySelection = AdaptiveStrategySelector.selectStrategy(
        this.marketDataBuffer,
        this.currentOptionsChain,
        indicators,
        regime
      );

      if (strategySelection.signal) {
        this.lastSignalTime = new Date();
        return strategySelection.signal;
      }

      return null;
    } catch (error) {
      console.error('Error generating trading signal:', error);
      return null;
    }
  }

  private async processTradingSignal(signal: TradeSignal): Promise<void> {
    console.log('🎯 Processing trading signal:', signal);

    try {
      // Execute through paper trading if enabled
      if (this.paperTrading) {
        await this.paperTrading.executeTradeSignal(signal, this.config.underlyingSymbol);
        return;
      }

      // Execute live trade
      const order = await this.executeLiveOrder(signal);
      if (order) {
        console.log('✅ Live order placed:', order);
        this.emit('order_placed', order);
      }

    } catch (error) {
      console.error('Error processing trading signal:', error);
      this.emit('signal_error', { signal, error });
    }
  }

  private async executeLiveOrder(signal: TradeSignal): Promise<any> {
    // Find appropriate option contract
    const optionSymbol = this.findBestOptionContract(signal);
    if (!optionSymbol) {
      console.warn('No suitable option contract found');
      return null;
    }

    // Calculate position size
    const positionSize = this.calculatePositionSize(signal.confidence);

    // Place order
    const order = await this.alpacaClient.placeOrder({
      symbol: optionSymbol,
      qty: positionSize,
      side: signal.action.includes('BUY') ? 'buy' : 'sell',
      type: 'market',
      time_in_force: 'day'
    });

    return order;
  }

  // Risk management
  private async performRiskCheck(): Promise<RiskCheck> {
    const violations: string[] = [];
    let riskScore = 0;

    try {
      // Check daily P&L
      if (this.dailyStats.pnl < -this.config.riskManagement.maxDailyLoss) {
        violations.push(`Daily loss limit exceeded: $${this.dailyStats.pnl.toFixed(2)}`);
        this.riskState.dailyLossExceeded = true;
        riskScore += 50;
      }

      // Check position count
      if (this.positions.size >= this.config.riskManagement.maxOpenPositions) {
        violations.push(`Maximum positions reached: ${this.positions.size}`);
        this.riskState.maxPositionsReached = true;
        riskScore += 30;
      }

      // Check account drawdown
      const currentBalance = this.config.enablePaperTrading ? 
        this.paperTrading?.getAccountMetrics().equity || 0 :
        (await this.alpacaClient.getAccount()).equity;

      const drawdown = (this.dailyStats.startingBalance - currentBalance) / this.dailyStats.startingBalance;
      if (drawdown > 0.20) { // 20% drawdown limit
        violations.push(`Account drawdown exceeded: ${(drawdown * 100).toFixed(1)}%`);
        this.riskState.accountDrawdownExceeded = true;
        riskScore += 40;
      }

      // Check individual position sizes
      for (const [symbol, position] of this.positions) {
        const positionValue = Math.abs(position.quantity * position.currentPrice * 100);
        if (positionValue > this.config.riskManagement.maxPositionSize) {
          violations.push(`Position size exceeded for ${symbol}: $${positionValue.toFixed(2)}`);
          riskScore += 20;
        }
      }

      // Check time-based risks for 0DTE options
      const now = new Date();
      for (const [symbol, position] of this.positions) {
        if (position.is0DTE) {
          const minutesToExpiration = (position.expiration.getTime() - now.getTime()) / (1000 * 60);
          if (minutesToExpiration < 30) {
            violations.push(`0DTE position near expiration: ${symbol} (${minutesToExpiration.toFixed(0)} min)`);
            riskScore += 25;
          }
        }
      }

      this.riskState.lastRiskCheck = new Date();

      return {
        passed: violations.length === 0,
        violations,
        riskScore: Math.min(100, riskScore)
      };

    } catch (error) {
      console.error('Error performing risk check:', error);
      return {
        passed: false,
        violations: ['Risk check system error'],
        riskScore: 100
      };
    }
  }

  private handleRiskViolation(riskCheck: RiskCheck): void {
    console.error('🚨 Risk violation detected:', riskCheck.violations);

    // Pause trading if risk score is too high
    if (riskCheck.riskScore >= 80) {
      this.pause();
      this.emit('risk_violation', { level: 'CRITICAL', riskCheck });
    } else if (riskCheck.riskScore >= 50) {
      this.emit('risk_violation', { level: 'HIGH', riskCheck });
    } else {
      this.emit('risk_violation', { level: 'MEDIUM', riskCheck });
    }

    // Send notifications if configured
    this.sendRiskNotification(riskCheck);
  }

  // Position management
  private async loadCurrentPositions(): Promise<void> {
    try {
      const alpacaPositions = await this.alpacaClient.getPositions();
      
      this.positions.clear();
      alpacaPositions.forEach(pos => {
        this.positions.set(pos.symbol, pos);
      });

      console.log(`📊 Loaded ${this.positions.size} current positions`);
    } catch (error) {
      console.error('Error loading current positions:', error);
    }
  }

  private async checkPositionExits(): Promise<void> {
    const now = new Date();

    for (const [symbol, position] of this.positions) {
      let shouldExit = false;
      let exitReason = '';

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

      // Check time decay for 0DTE
      if (position.is0DTE) {
        const minutesToExpiration = (position.expiration.getTime() - now.getTime()) / (1000 * 60);
        if (minutesToExpiration <= 30) {
          shouldExit = true;
          exitReason = 'TIME_DECAY';
        }
      }

      // Check maximum holding time
      const holdingMinutes = (now.getTime() - position.entryTime.getTime()) / (1000 * 60);
      if (holdingMinutes >= this.config.strategy.maxHoldingTimeMinutes) {
        shouldExit = true;
        exitReason = 'MAX_HOLD_TIME';
      }

      if (shouldExit) {
        await this.exitPosition(symbol, exitReason);
      }
    }
  }

  private async exitPosition(symbol: string, reason: string): Promise<void> {
    const position = this.positions.get(symbol);
    if (!position) return;

    try {
      console.log(`🚪 Exiting position ${symbol} - Reason: ${reason}`);

      if (this.paperTrading) {
        await this.paperTrading.submitOrder({
          symbol,
          side: 'SELL',
          quantity: position.quantity,
          orderType: 'MARKET'
        });
      } else {
        await this.alpacaClient.placeOrder({
          symbol,
          qty: position.quantity,
          side: 'sell',
          type: 'market',
          time_in_force: 'day'
        });
      }

      this.emit('position_exited', { symbol, reason, position });
    } catch (error) {
      console.error(`Error exiting position ${symbol}:`, error);
    }
  }

  private async closeAllPositions(reason: string): Promise<void> {
    console.log(`🚪 Closing all positions - Reason: ${reason}`);
    
    const exitPromises = Array.from(this.positions.keys()).map(symbol => 
      this.exitPosition(symbol, reason)
    );

    await Promise.allSettled(exitPromises);
  }

  // Utility methods
  private updatePositionFromFill(update: any): void {
    // Update position tracking based on fill
    // This would be more complex in practice
    console.log('Updating position from fill:', update);
  }

  private updateOptionsChainFromQuote(quote: any): void {
    // Update options chain with latest quote data
    // This would involve parsing option symbols and updating the chain
  }

  private async updateMarketAnalysis(): Promise<void> {
    if (this.marketDataBuffer.length < 20) return;

    try {
      // Update market regime
      const regime = this.regimeDetector.detectRegime(this.marketDataBuffer);
      
      // Update technical indicators
      const indicators = this.technicalAnalysis.calculateIndicators(this.marketDataBuffer);
      
      this.emit('market_analysis_updated', { regime, indicators });
    } catch (error) {
      console.error('Error updating market analysis:', error);
    }
  }

  private findBestOptionContract(signal: TradeSignal): string | null {
    // Find the best option contract based on the signal
    // This is a simplified implementation
    const currentPrice = this.marketDataBuffer[this.marketDataBuffer.length - 1]?.close;
    if (!currentPrice) return null;

    // For 0DTE trading, find ATM options
    const targetStrike = Math.round(currentPrice);
    const optionType = signal.action.includes('CALL') ? 'C' : 'P';
    
    // Generate option symbol (simplified)
    const today = new Date();
    const expString = today.toISOString().slice(2, 10).replace(/-/g, '');
    const strikeString = (targetStrike * 1000).toString().padStart(8, '0');
    
    return `${this.config.underlyingSymbol}${expString}${optionType}${strikeString}`;
  }

  private calculatePositionSize(confidence: number): number {
    const baseSize = Math.floor(this.config.accountConfig.balance / 20000); // $20k per contract
    const confidenceMultiplier = confidence / 100;
    return Math.max(1, Math.floor(baseSize * confidenceMultiplier));
  }

  private updateSessionMetrics(): void {
    if (!this.currentSession) return;

    // Update session metrics
    const metrics = this.config.enablePaperTrading ? 
      this.paperTrading?.getAccountMetrics() : null;

    if (metrics) {
      this.currentSession.totalTrades = metrics.totalTrades;
      this.currentSession.totalPnL = metrics.totalPnL;
      this.currentSession.maxDrawdown = metrics.maxDrawdown;
      this.currentSession.winRate = metrics.winRate;
    }

    this.emit('session_updated', this.currentSession);
  }

  private sendRiskNotification(riskCheck: RiskCheck): void {
    // Send notifications via configured channels
    if (this.config.notifications.enableSlack && this.config.notifications.slackWebhook) {
      // Send Slack notification
      console.log('📱 Sending Slack notification for risk violation');
    }

    if (this.config.notifications.enableEmail && this.config.notifications.emailConfig) {
      // Send email notification
      console.log('📧 Sending email notification for risk violation');
    }
  }

  // Public getters
  getStatus(): {
    isRunning: boolean;
    isPaused: boolean;
    currentSession: TradingSession | null;
    positionCount: number;
    dailyPnL: number;
    riskState: any;
  } {
    return {
      isRunning: this.isRunning,
      isPaused: this.isPaused,
      currentSession: this.currentSession,
      positionCount: this.positions.size,
      dailyPnL: this.dailyStats.pnl,
      riskState: this.riskState
    };
  }

  getCurrentPositions(): Position[] {
    return Array.from(this.positions.values());
  }

  getMarketDataBuffer(): MarketData[] {
    return [...this.marketDataBuffer];
  }

  // Configuration updates
  updateStrategy(newStrategy: Partial<Strategy>): void {
    this.config.strategy = { ...this.config.strategy, ...newStrategy };
    this.emit('strategy_updated', this.config.strategy);
  }

  updateRiskManagement(newRiskConfig: Partial<LiveTradingConfig['riskManagement']>): void {
    this.config.riskManagement = { ...this.config.riskManagement, ...newRiskConfig };
    this.emit('risk_config_updated', this.config.riskManagement);
  }
}
