
import { EventEmitter } from 'events';
import { v4 as uuidv4 } from 'uuid';
import { MarketData, OptionsChain, Position, TradeSignal } from '../utils/types';
import { StrategyBacktestingAdapter } from '../core/strategy-backtesting-adapter';
import { GreeksSimulator, OptionPricingInputs } from '../data/greeks-simulator';

export interface PaperTradingConfig {
  initialBalance: number;
  commissionPerContract: number;
  bidAskSpreadPercent: number;
  slippagePercent: number;
  maxPositions: number;
  riskFreeRate: number;
}

export interface PaperOrder {
  id: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  quantity: number;
  orderType: 'MARKET' | 'LIMIT';
  limitPrice?: number;
  status: 'PENDING' | 'FILLED' | 'CANCELLED' | 'REJECTED';
  submittedAt: Date;
  filledAt?: Date;
  fillPrice?: number;
  commission: number;
  slippage: number;
}

export interface PaperPosition {
  id: string;
  symbol: string;
  optionType: 'CALL' | 'PUT';
  strike: number;
  expiration: Date;
  quantity: number;
  averagePrice: number;
  currentPrice: number;
  marketValue: number;
  unrealizedPnL: number;
  unrealizedPnLPercent: number;
  openedAt: Date;
  greeks: {
    delta: number;
    gamma: number;
    theta: number;
    vega: number;
    rho: number;
  };
  is0DTE: boolean;
  timeDecayRisk: 'LOW' | 'MEDIUM' | 'HIGH';
  metadata?: {
    [key: string]: any;
  };
}

export interface PaperTrade {
  id: string;
  orderId: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  quantity: number;
  price: number;
  timestamp: Date;
  commission: number;
  slippage: number;
  pnl?: number; // For closing trades
}

export interface AccountMetrics {
  balance: number;
  equity: number;
  buyingPower: number;
  dayTradingBuyingPower: number;
  totalPnL: number;
  dayPnL: number;
  positions: PaperPosition[];
  openOrders: PaperOrder[];
  todayTrades: PaperTrade[];
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  winRate: number;
  averageWin: number;
  averageLoss: number;
  profitFactor: number;
  maxDrawdown: number;
  sharpeRatio: number;
}

export class AlpacaPaperTrading extends EventEmitter {
  private config: PaperTradingConfig;
  private balance: number;
  private positions: Map<string, PaperPosition> = new Map();
  private orders: Map<string, PaperOrder> = new Map();
  private trades: PaperTrade[] = [];
  private dailyTrades: Map<string, PaperTrade[]> = new Map(); // Date -> Trades
  private currentMarketData: Map<string, MarketData> = new Map();
  private optionsChains: Map<string, OptionsChain[]> = new Map();
  private startingBalance: number;
  private strategyAdapter: StrategyBacktestingAdapter | null = null;
  private highWaterMark: number;
  private maxDrawdown: number = 0;

  constructor(config: PaperTradingConfig) {
    super();
    this.config = config;
    this.balance = config.initialBalance;
    this.startingBalance = config.initialBalance;
    this.highWaterMark = config.initialBalance;
  }

  /**
   * Close a specific position by symbol
   * This is the proper way to close positions, not by submitting sell orders
   */
  async closePosition(symbol: string): Promise<PaperTrade | null> {
    const position = this.positions.get(symbol);
    if (!position) {
      console.warn(`❌ No position found for symbol: ${symbol}`);
      return null;
    }

    // Calculate exit price (current market price with some realistic variation)
    const underlyingSymbol = symbol.includes('flyagonal') ? 'SPY' : symbol.split('_')[0];
    const marketData = this.currentMarketData.get(underlyingSymbol);
    
    // For options, simulate realistic price movement with proper variation
    let exitPrice = position.currentPrice;
    if (marketData) {
      // Get underlying price change
      const underlyingPrice = marketData.close;
      
      // For complex strategies like Flyagonal, simulate more realistic behavior
      if (symbol.includes('flyagonal')) {
        // Flyagonal is a complex multi-leg strategy - simulate realistic P&L distribution
        const timeHeld = (new Date().getTime() - position.openedAt.getTime()) / (1000 * 60 * 60); // hours
        const timeDecay = Math.exp(-0.1 * timeHeld); // Exponential time decay
        
        // Simulate realistic win/loss distribution with proper variation
        // Use multiple sources for better randomization
        const positionHash = position.id.split('_')[1] || '0'; // Get timestamp part of ID
        const positionSeed = (parseInt(positionHash) % 1000) / 1000; // Use timestamp modulo
        const priceSeed = (Math.floor(marketData.close * 100) % 100) / 100; // Use price variation
        const timeSeed = (new Date().getTime() % 1000) / 1000; // Time-based variation
        const combinedSeed = (positionSeed + priceSeed + timeSeed) % 1; // Combine all seeds
        
        let multiplier;
        
        if (combinedSeed < 0.65) {
          // 65% chance of profit (realistic for income strategies)
          const profitVariation = (combinedSeed / 0.65) * 0.20; // 0% to 20% profit range
          multiplier = 1 + profitVariation;
        } else if (combinedSeed < 0.85) {
          // 20% chance of small loss
          const lossVariation = ((combinedSeed - 0.65) / 0.20) * 0.10; // 0% to 10% loss range
          multiplier = 1 - lossVariation;
        } else {
          // 15% chance of larger loss (stop loss hit)
          const largeLossVariation = ((combinedSeed - 0.85) / 0.15) * 0.15; // 0% to 15% additional loss
          multiplier = 1 - (0.10 + largeLossVariation); // 10% to 25% loss range
        }
        
        exitPrice = position.averagePrice * multiplier * timeDecay;
      } else {
        // For single-leg options, use delta-based pricing
        const underlyingChange = (underlyingPrice - 490) / 490; // Assume SPY around 490
        const delta = 0.5; // Simplified delta
        const timeDecayFactor = 0.98; // Small time decay
        
        exitPrice = position.averagePrice * (1 + underlyingChange * delta) * timeDecayFactor;
      }
      
      // Ensure price doesn't go negative
      exitPrice = Math.max(0.01, exitPrice);
    } else {
      // Fallback: small random movement
      const randomChange = (Math.random() - 0.5) * 0.1; // ±5% random
      exitPrice = position.averagePrice * (1 + randomChange);
      exitPrice = Math.max(0.01, exitPrice);
    }
    
    // Calculate P&L
    const pnl = (exitPrice - position.averagePrice) * position.quantity * 100; // *100 for options
    
    // Create closing trade
    const closingTrade: PaperTrade = {
      id: uuidv4(),
      orderId: uuidv4(),
      symbol: symbol,
      side: 'SELL',
      quantity: position.quantity,
      price: exitPrice,
      timestamp: new Date(),
      pnl: pnl,
      commission: this.calculateCommission(position.quantity),
      slippage: 0
    };

    // Add to trades list
    this.trades.push(closingTrade);
    
    // Update daily trades
    const dateKey = new Date().toISOString().split('T')[0];
    const dailyTrades = this.dailyTrades.get(dateKey) || [];
    dailyTrades.push(closingTrade);
    this.dailyTrades.set(dateKey, dailyTrades);

    // Update balance
    this.balance += (exitPrice * position.quantity * 100) - this.calculateCommission(position.quantity);

    // Remove position
    this.positions.delete(symbol);

    console.log(`✅ Closed position ${symbol}: P&L = $${pnl.toFixed(2)}`);
    
    // Emit events
    this.emit('position_closed', { position, trade: closingTrade });
    
    return closingTrade;
  }

  /**
   * Close all open positions
   */
  async closeAllPositions(): Promise<PaperTrade[]> {
    const closedTrades: PaperTrade[] = [];
    const positionSymbols = Array.from(this.positions.keys());
    
    for (const symbol of positionSymbols) {
      const trade = await this.closePosition(symbol);
      if (trade) {
        closedTrades.push(trade);
      }
    }
    
    console.log(`✅ Closed ${closedTrades.length} positions`);
    return closedTrades;
  }

  // Order management
  async submitOrder(order: {
    symbol: string;
    side: 'BUY' | 'SELL';
    quantity: number;
    orderType: 'MARKET' | 'LIMIT';
    limitPrice?: number;
  }): Promise<PaperOrder> {
    const paperOrder: PaperOrder = {
      id: uuidv4(),
      symbol: order.symbol,
      side: order.side,
      quantity: order.quantity,
      orderType: order.orderType,
      limitPrice: order.limitPrice,
      status: 'PENDING',
      submittedAt: new Date(),
      commission: this.calculateCommission(order.quantity),
      slippage: 0
    };

    this.orders.set(paperOrder.id, paperOrder);
    this.emit('order_submitted', paperOrder);

    // For market orders, fill immediately
    if (order.orderType === 'MARKET') {
      await this.fillOrder(paperOrder.id);
    }

    return paperOrder;
  }

  private async fillOrder(orderId: string): Promise<void> {
    const order = this.orders.get(orderId);
    if (!order || order.status !== 'PENDING') {
      return;
    }

    // Get current market data for the symbol
    const optionChain = this.getOptionFromSymbol(order.symbol);
    if (!optionChain) {
      order.status = 'REJECTED';
      this.emit('order_rejected', order, 'Option not found');
      return;
    }

    // Calculate fill price with bid-ask spread and slippage
    const fillPrice = this.calculateFillPrice(optionChain, order.side);
    const slippage = this.calculateSlippage(fillPrice);

    // Check if we have enough buying power
    const totalCost = (fillPrice + slippage) * order.quantity * 100 + order.commission;
    if (order.side === 'BUY' && totalCost > this.balance) {
      order.status = 'REJECTED';
      this.emit('order_rejected', order, 'Insufficient buying power');
      return;
    }

    // Fill the order
    order.status = 'FILLED';
    order.filledAt = new Date();
    order.fillPrice = fillPrice + slippage;
    order.slippage = slippage;

    // Create trade record
    const trade: PaperTrade = {
      id: uuidv4(),
      orderId: order.id,
      symbol: order.symbol,
      side: order.side,
      quantity: order.quantity,
      price: order.fillPrice,
      timestamp: new Date(),
      commission: order.commission,
      slippage: slippage
    };

    this.trades.push(trade);
    this.addDailyTrade(trade);

    // Update positions and balance
    await this.updatePositions(trade);
    this.updateBalance(trade);

    this.emit('order_filled', order);
    this.emit('trade_executed', trade);
  }

  private getOptionFromSymbol(symbol: string): OptionsChain | null {
    // Parse option symbol to get underlying, expiration, strike, type
    // This is a simplified parser - in reality, you'd need more robust parsing
    const match = symbol.match(/^([A-Z]+)(\d{6})([CP])(\d{8})$/);
    if (!match) return null;

    const [, underlying, expDate, callPut, strikeStr] = match;
    const strike = parseInt(strikeStr) / 1000; // Strike is in thousandths
    const type = callPut === 'C' ? 'CALL' : 'PUT';

    // Look for matching option in chains
    const chains = this.optionsChains.get(underlying);
    if (!chains) return null;

    return chains.find(opt => 
      opt.strike === strike && 
      opt.type === type
    ) || null;
  }

  private calculateFillPrice(option: OptionsChain, side: 'BUY' | 'SELL'): number {
    const midPrice = (option.bid + option.ask) / 2;
    const spread = option.ask - option.bid;
    const spreadAdjustment = spread * this.config.bidAskSpreadPercent;

    if (side === 'BUY') {
      return midPrice + spreadAdjustment;
    } else {
      return midPrice - spreadAdjustment;
    }
  }

  private calculateSlippage(price: number): number {
    return price * this.config.slippagePercent * (Math.random() - 0.5) * 2;
  }

  private calculateCommission(quantity: number): number {
    return quantity * this.config.commissionPerContract;
  }

  private async updatePositions(trade: PaperTrade): Promise<void> {
    const existingPosition = this.positions.get(trade.symbol);

    if (trade.side === 'BUY') {
      if (existingPosition) {
        // Add to existing position
        const totalQuantity = existingPosition.quantity + trade.quantity;
        const totalCost = (existingPosition.averagePrice * existingPosition.quantity) + 
                         (trade.price * trade.quantity);
        existingPosition.quantity = totalQuantity;
        existingPosition.averagePrice = totalCost / totalQuantity;
      } else {
        // Create new position
        const option = this.getOptionFromSymbol(trade.symbol);
        if (option) {
          const position: PaperPosition = {
            id: uuidv4(),
            symbol: trade.symbol,
            optionType: option.type,
            strike: option.strike,
            expiration: new Date(option.expiration),
            quantity: trade.quantity,
            averagePrice: trade.price,
            currentPrice: trade.price,
            marketValue: trade.price * trade.quantity * 100,
            unrealizedPnL: 0,
            unrealizedPnLPercent: 0,
            openedAt: trade.timestamp,
            greeks: {
              delta: option.delta || 0,
              gamma: option.gamma || 0,
              theta: option.theta || 0,
              vega: option.vega || 0,
              rho: 0
            },
            is0DTE: this.is0DTE(new Date(option.expiration)),
            timeDecayRisk: this.calculateTimeDecayRisk(new Date(option.expiration))
          };
          this.positions.set(trade.symbol, position);
        }
      }
    } else {
      // SELL order
      if (existingPosition) {
        if (existingPosition.quantity >= trade.quantity) {
          // Reduce or close position
          existingPosition.quantity -= trade.quantity;
          
          // Calculate P&L for the closed portion
          const pnl = (trade.price - existingPosition.averagePrice) * trade.quantity * 100;
          trade.pnl = pnl;

          if (existingPosition.quantity === 0) {
            this.positions.delete(trade.symbol);
          }
        } else {
          // This would be a short position - for simplicity, reject
          console.warn('Cannot sell more than current position');
        }
      }
    }

    // Update current prices and P&L for all positions
    await this.updatePositionValues();
  }

  private updateBalance(trade: PaperTrade): void {
    const totalCost = trade.price * trade.quantity * 100 + trade.commission;
    
    if (trade.side === 'BUY') {
      this.balance -= totalCost;
    } else {
      this.balance += totalCost;
      if (trade.pnl) {
        this.balance += trade.pnl;
      }
    }

    // Update high water mark and drawdown
    const currentEquity = this.getAccountMetrics().equity;
    if (currentEquity > this.highWaterMark) {
      this.highWaterMark = currentEquity;
    } else {
      const drawdown = (this.highWaterMark - currentEquity) / this.highWaterMark;
      this.maxDrawdown = Math.max(this.maxDrawdown, drawdown);
    }
  }

  private async updatePositionValues(): Promise<void> {
    for (const [symbol, position] of this.positions) {
      // Handle strategy-specific positions (e.g., flyagonal_xxx)
      if (symbol.includes('flyagonal_') || symbol.includes('_')) {
        // For strategy-specific positions, use the strategy adapter to update prices
        if (this.strategyAdapter) {
          // Get underlying market data and options chain
          const underlyingSymbol = 'SPY'; // For now, assume SPY
          const marketData = this.currentMarketData.get(underlyingSymbol);
          const optionsChain = this.optionsChains.get(underlyingSymbol) || [];
          
          if (marketData) {
            // Convert PaperPosition to Position for strategy adapter
            const positionForAdapter: Position = {
              id: position.id,
              symbol: position.symbol,
              type: position.optionType,
              side: position.optionType,
              strike: position.strike,
              expiration: position.expiration,
              quantity: position.quantity,
              entryPrice: position.averagePrice,
              currentPrice: position.currentPrice,
              entryTime: position.openedAt,
              unrealizedPnL: position.unrealizedPnL,
              unrealizedPnLPercent: position.unrealizedPnLPercent,
              is0DTE: position.is0DTE,
              timeDecayRisk: position.timeDecayRisk,
              metadata: position.metadata
            };
            
            const updatedPosition = this.strategyAdapter.updatePosition(positionForAdapter, marketData, optionsChain);
            if (updatedPosition) {
              position.currentPrice = Math.abs(updatedPosition.currentPrice || updatedPosition.entryPrice);
              position.marketValue = position.currentPrice * position.quantity;
              position.unrealizedPnL = updatedPosition.unrealizedPnL || 0;
              position.unrealizedPnLPercent = updatedPosition.unrealizedPnLPercent || 0;
            }
          }
        } else {
          // Fallback: simulate realistic price movement for strategy positions
          const underlyingData = this.currentMarketData.get('SPY'); // Assume SPY for now
          if (underlyingData) {
            // Simulate options price movement based on underlying movement and time decay
            const timeDecayFactor = 0.98 + (Math.random() * 0.04); // 0.98 to 1.02
            const deltaEffect = (Math.random() - 0.5) * 0.1; // -5% to +5% random movement
            const newPrice = position.averagePrice * timeDecayFactor * (1 + deltaEffect);
            
            position.currentPrice = Math.max(0.01, newPrice); // Minimum $0.01
            position.marketValue = position.currentPrice * position.quantity;
            position.unrealizedPnL = (position.currentPrice - position.averagePrice) * position.quantity;
            position.unrealizedPnLPercent = ((position.currentPrice - position.averagePrice) / position.averagePrice) * 100;
          }
        }
      } else {
        // Handle standard option symbols
        const option = this.getOptionFromSymbol(symbol);
        if (option) {
          const midPrice = (option.bid + option.ask) / 2;
          position.currentPrice = midPrice;
          position.marketValue = midPrice * position.quantity * 100;
          position.unrealizedPnL = (midPrice - position.averagePrice) * position.quantity * 100;
          position.unrealizedPnLPercent = (position.unrealizedPnL / (position.averagePrice * position.quantity * 100)) * 100;

          // Update Greeks if we have underlying price
          const underlyingSymbol = this.extractUnderlyingSymbol(symbol);
          const underlyingData = this.currentMarketData.get(underlyingSymbol);
          
          if (underlyingData) {
            const greeks = this.calculateGreeks(position, underlyingData.close);
            position.greeks = greeks;
          }
        }
      }
    }
  }

  private calculateGreeks(position: PaperPosition, underlyingPrice: number): {
    delta: number;
    gamma: number;
    theta: number;
    vega: number;
    rho: number;
  } {
    const inputs: OptionPricingInputs = {
      underlyingPrice,
      strikePrice: position.strike,
      timeToExpiration: GreeksSimulator.timeToExpiration(position.expiration),
      riskFreeRate: this.config.riskFreeRate,
      volatility: 0.20, // Default volatility - in practice, use implied vol
      optionType: position.optionType.toLowerCase() as 'call' | 'put'
    };

    const result = GreeksSimulator.calculateOptionPrice(inputs);
    return {
      delta: result.delta,
      gamma: result.gamma,
      theta: result.theta,
      vega: result.vega,
      rho: result.rho
    };
  }

  private extractUnderlyingSymbol(optionSymbol: string): string {
    const match = optionSymbol.match(/^([A-Z]+)/);
    return match ? match[1] : '';
  }

  private is0DTE(expiration: Date, currentDate?: Date): boolean {
    const referenceDate = currentDate || new Date();
    const today = new Date(referenceDate.getFullYear(), referenceDate.getMonth(), referenceDate.getDate());
    const expDate = new Date(expiration.getFullYear(), expiration.getMonth(), expiration.getDate());
    return today.getTime() === expDate.getTime();
  }

  private calculateTimeDecayRisk(expiration: Date): 'LOW' | 'MEDIUM' | 'HIGH' {
    const hoursToExpiration = (expiration.getTime() - Date.now()) / (1000 * 60 * 60);
    
    if (hoursToExpiration < 2) return 'HIGH';
    if (hoursToExpiration < 24) return 'MEDIUM';
    return 'LOW';
  }

  private addDailyTrade(trade: PaperTrade): void {
    const dateKey = trade.timestamp.toISOString().split('T')[0];
    if (!this.dailyTrades.has(dateKey)) {
      this.dailyTrades.set(dateKey, []);
    }
    this.dailyTrades.get(dateKey)!.push(trade);
  }

  // Market data updates
  updateMarketData(symbol: string, data: MarketData): void {
    this.currentMarketData.set(symbol, data);
    this.updatePositionValues();
  }

  updateOptionsChain(underlying: string, chain: OptionsChain[]): void {
    this.optionsChains.set(underlying, chain);
    this.updatePositionValues();
  }

  /**
   * Set strategy-specific backtesting adapter
   * This enables custom position creation and management per strategy
   */
  setStrategyAdapter(adapter: StrategyBacktestingAdapter | null): void {
    this.strategyAdapter = adapter;
    if (adapter) {
      console.log(`🎯 Paper trading using strategy adapter: ${adapter.strategyName}`);
    }
  }

  // Account information
  getAccountMetrics(): AccountMetrics {
    const totalMarketValue = Array.from(this.positions.values())
      .reduce((sum, pos) => sum + pos.marketValue, 0);
    
    const equity = this.balance + totalMarketValue;
    const totalPnL = equity - this.startingBalance;
    
    // Calculate today's P&L
    const today = new Date().toISOString().split('T')[0];
    const todayTrades = this.dailyTrades.get(today) || [];
    const dayPnL = todayTrades.reduce((sum, trade) => sum + (trade.pnl || 0), 0);

    // Calculate win/loss statistics
    const closedTrades = this.trades.filter(t => t.pnl !== undefined);
    const winningTrades = closedTrades.filter(t => (t.pnl || 0) > 0);
    const losingTrades = closedTrades.filter(t => (t.pnl || 0) < 0);
    
    const winRate = closedTrades.length > 0 ? winningTrades.length / closedTrades.length : 0;
    const averageWin = winningTrades.length > 0 ? 
      winningTrades.reduce((sum, t) => sum + (t.pnl || 0), 0) / winningTrades.length : 0;
    const averageLoss = losingTrades.length > 0 ? 
      Math.abs(losingTrades.reduce((sum, t) => sum + (t.pnl || 0), 0) / losingTrades.length) : 0;
    
    const profitFactor = averageLoss > 0 ? (averageWin * winningTrades.length) / (averageLoss * losingTrades.length) : 0;

    // Calculate Sharpe ratio (simplified)
    const dailyReturns = Array.from(this.dailyTrades.values())
      .map(trades => trades.reduce((sum, t) => sum + (t.pnl || 0), 0));
    const avgDailyReturn = dailyReturns.reduce((sum, ret) => sum + ret, 0) / Math.max(dailyReturns.length, 1);
    const stdDev = Math.sqrt(dailyReturns.reduce((sum, ret) => sum + Math.pow(ret - avgDailyReturn, 2), 0) / Math.max(dailyReturns.length - 1, 1));
    const sharpeRatio = stdDev > 0 ? (avgDailyReturn / stdDev) * Math.sqrt(252) : 0;

    return {
      balance: this.balance,
      equity,
      buyingPower: this.balance * 4, // Simplified day trading buying power
      dayTradingBuyingPower: this.balance * 4,
      totalPnL,
      dayPnL,
      positions: Array.from(this.positions.values()),
      openOrders: Array.from(this.orders.values()).filter(o => o.status === 'PENDING'),
      todayTrades,
      totalTrades: closedTrades.length,
      winningTrades: winningTrades.length,
      losingTrades: losingTrades.length,
      winRate,
      averageWin,
      averageLoss,
      profitFactor,
      maxDrawdown: this.maxDrawdown,
      sharpeRatio
    };
  }

  // Strategy integration
  async executeTradeSignal(signal: TradeSignal, underlying: string): Promise<PaperOrder | null> {
    try {
      // Use strategy adapter if available for complex position creation
      if (this.strategyAdapter) {
        return await this.executeStrategySpecificSignal(signal, underlying);
      }
      
      // Fallback to legacy single-leg option handling
      const optionSymbol = await this.findOptionContract(underlying, signal);
      if (!optionSymbol) {
        console.warn('No suitable option contract found for signal');
        return null;
      }

      // Calculate position size based on account balance and risk
      const positionSize = this.calculatePositionSize(signal.confidence);

      const order = await this.submitOrder({
        symbol: optionSymbol,
        side: signal.action.includes('BUY') ? 'BUY' : 'SELL',
        quantity: positionSize,
        orderType: 'MARKET'
      });

      return order;
    } catch (error) {
      console.error('Error executing trade signal:', error);
      return null;
    }
  }

  /**
   * Execute strategy-specific signal using the adapter
   */
  private async executeStrategySpecificSignal(signal: TradeSignal, underlying: string): Promise<PaperOrder | null> {
    const chains = this.optionsChains.get(underlying);
    const marketData = this.currentMarketData.get(underlying);
    
    if (!chains || !marketData || !this.strategyAdapter) {
      console.warn('❌ Missing data for strategy-specific execution');
      return null;
    }

    // Use strategy adapter to create position
    const position = this.strategyAdapter.createPosition(signal, chains, marketData.close);
    if (!position) {
      console.warn('❌ Strategy adapter could not create position from signal');
      return null;
    }

    // Create a paper order representing the complex position
    const orderId = uuidv4();
    const fillPrice = Math.abs(position.entryPrice);
    const order: PaperOrder = {
      id: orderId,
      symbol: position.symbol || underlying,
      side: 'BUY', // Complex positions are typically net debit
      quantity: position.quantity,
      orderType: 'MARKET',
      status: 'FILLED',
      submittedAt: signal.timestamp || new Date(),
      filledAt: signal.timestamp || new Date(),
      fillPrice: fillPrice,
      commission: this.config.commissionPerContract * (position.legs?.length || 1),
      slippage: 0
    };

    // Store the order and create position
    this.orders.set(orderId, order);
    
    // Convert adapter position to paper position
    const currentPrice = Math.abs(position.currentPrice || position.entryPrice);
    const paperPosition: PaperPosition = {
      id: position.id,
      symbol: position.symbol || underlying,
      optionType: position.type as 'CALL' | 'PUT' || 'CALL', // Default to CALL for complex positions
      strike: position.strike || 0, // Default for multi-leg positions
      expiration: position.expiration || new Date(),
      quantity: position.quantity,
      averagePrice: Math.abs(position.entryPrice),
      currentPrice: currentPrice,
      marketValue: position.quantity * currentPrice,
      unrealizedPnL: position.unrealizedPnL || 0,
      unrealizedPnLPercent: position.entryPrice !== 0 ? ((currentPrice - Math.abs(position.entryPrice)) / Math.abs(position.entryPrice)) * 100 : 0,
      openedAt: position.entryTime,
      greeks: {
        delta: 0.5, // Default values for complex positions
        gamma: 0.1,
        theta: -0.05,
        vega: 0.2,
        rho: 0.01
      },
      is0DTE: true, // Most strategies are 0DTE
      timeDecayRisk: 'HIGH',
      metadata: {
        ...position.metadata,
        strategyAdapter: this.strategyAdapter.strategyName,
        legs: position.legs,
        stopLoss: position.stopLoss,
        takeProfit: position.takeProfit
      }
    };

    this.positions.set(position.id, paperPosition);
    this.balance -= fillPrice + order.commission;

    console.log(`✅ Created strategy-specific position: ${position.id}`);
    console.log(`   Cost: $${fillPrice.toFixed(2)} | Legs: ${position.legs?.length || 1}`);

    this.emit('order_filled', order);
    return order;
  }

  private async findOptionContract(underlying: string, signal: TradeSignal): Promise<string | null> {
    const chains = this.optionsChains.get(underlying);
    if (!chains) return null;

    // For 0DTE trading, find contracts expiring today
    // Use signal timestamp as reference date for backtesting
    const referenceDate = signal.timestamp || new Date();
    const todayChains = chains.filter(opt => this.is0DTE(new Date(opt.expiration), referenceDate));

    if (todayChains.length === 0) return null;

    // Find ATM or slightly OTM options based on signal
    const underlyingData = this.currentMarketData.get(underlying);
    if (!underlyingData) return null;

    const currentPrice = underlyingData.close;
    const targetType = signal.action.includes('CALL') ? 'CALL' : 'PUT';
    
    // Find closest strike to current price
    const suitableOptions = todayChains
      .filter(opt => opt.type === targetType)
      .sort((a, b) => Math.abs(a.strike - currentPrice) - Math.abs(b.strike - currentPrice));

    if (suitableOptions.length === 0) return null;

    // Return option symbol (simplified format)
    const option = suitableOptions[0];
    const expDate = new Date(option.expiration);
    const expString = expDate.toISOString().slice(2, 10).replace(/-/g, '');
    const callPut = option.type === 'CALL' ? 'C' : 'P';
    const strikeString = (option.strike * 1000).toString().padStart(8, '0');
    
    return `${underlying}${expString}${callPut}${strikeString}`;
  }

  private calculatePositionSize(confidence: number): number {
    // More realistic position sizing for options trading
    // Assume each options contract costs around $200-500 on average
    const avgContractCost = 300; // $300 per contract average
    const maxRiskPerTrade = this.balance * 0.02; // Risk 2% of account per trade
    const baseSize = Math.floor(maxRiskPerTrade / avgContractCost);
    const confidenceMultiplier = confidence / 100;
    const calculatedSize = Math.floor(baseSize * confidenceMultiplier);
    
    // Ensure reasonable bounds: 1-10 contracts for a $25k account
    return Math.max(1, Math.min(10, calculatedSize));
  }

  // Risk management
  checkRiskLimits(): { withinLimits: boolean; violations: string[] } {
    const violations: string[] = [];
    const metrics = this.getAccountMetrics();

    // Check maximum positions
    if (this.positions.size > this.config.maxPositions) {
      violations.push(`Too many positions: ${this.positions.size}/${this.config.maxPositions}`);
    }

    // Check daily loss limit
    if (metrics.dayPnL < -1000) { // $1000 daily loss limit
      violations.push(`Daily loss limit exceeded: $${metrics.dayPnL.toFixed(2)}`);
    }

    // Check account balance
    if (this.balance < this.startingBalance * 0.8) { // 20% account drawdown limit
      violations.push(`Account drawdown limit exceeded: ${((1 - this.balance / this.startingBalance) * 100).toFixed(1)}%`);
    }

    return {
      withinLimits: violations.length === 0,
      violations
    };
  }

  // Cleanup and reset
  reset(): void {
    this.balance = this.config.initialBalance;
    this.positions.clear();
    this.orders.clear();
    this.trades = [];
    this.dailyTrades.clear();
    this.highWaterMark = this.config.initialBalance;
    this.maxDrawdown = 0;
  }

  // Export data for analysis
  exportTradingData(): {
    trades: PaperTrade[];
    dailyMetrics: { date: string; pnl: number; trades: number }[];
    positions: PaperPosition[];
    accountMetrics: AccountMetrics;
  } {
    const dailyMetrics = Array.from(this.dailyTrades.entries()).map(([date, trades]) => ({
      date,
      pnl: trades.reduce((sum, t) => sum + (t.pnl || 0), 0),
      trades: trades.length
    }));

    return {
      trades: this.trades,
      dailyMetrics,
      positions: Array.from(this.positions.values()),
      accountMetrics: this.getAccountMetrics()
    };
  }
}
