
import { EventEmitter } from 'events';
import { v4 as uuidv4 } from 'uuid';
import { MarketData, OptionsChain, Position, TradeSignal } from '../utils/types';
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
  private highWaterMark: number;
  private maxDrawdown: number = 0;

  constructor(config: PaperTradingConfig) {
    super();
    this.config = config;
    this.balance = config.initialBalance;
    this.startingBalance = config.initialBalance;
    this.highWaterMark = config.initialBalance;
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
      // Find appropriate option contract based on signal
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
    // Base position size on confidence and account balance
    const baseSize = Math.floor(this.balance / 10000); // $10k per contract
    const confidenceMultiplier = confidence / 100;
    return Math.max(1, Math.floor(baseSize * confidenceMultiplier));
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
