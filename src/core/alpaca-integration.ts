
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import WebSocket from 'ws';
import { EventEmitter } from 'events';
import { MarketData, OptionsChain, Position } from '../utils/types';

export interface AlpacaConfig {
  apiKey: string;
  apiSecret: string;
  baseUrl?: string;
  dataUrl?: string;
  streamUrl?: string;
  isPaper?: boolean;
}

export interface OptionContract {
  id: string;
  symbol: string;
  name: string;
  status: string;
  tradable: boolean;
  expiration_date: string;
  root_symbol: string;
  underlying_symbol: string;
  underlying_asset_id: string;
  type: 'call' | 'put';
  style: 'american' | 'european';
  strike_price: string;
  size: string;
  open_interest?: string;
  open_interest_date?: string;
  close_price?: string;
  close_price_date?: string;
}

export interface BarData {
  t: string; // timestamp
  o: number; // open
  h: number; // high
  l: number; // low
  c: number; // close
  v: number; // volume
  n?: number; // trade count
  vw?: number; // volume weighted average price
}

export interface TradeData {
  T: string; // message type
  S: string; // symbol
  p: number; // price
  s: number; // size
  t: string; // timestamp
  c?: string[]; // conditions
  i?: number; // trade id
  x?: string; // exchange
}

export interface QuoteData {
  T: string; // message type
  S: string; // symbol
  bp: number; // bid price
  bs: number; // bid size
  ap: number; // ask price
  as: number; // ask size
  t: string; // timestamp
  c?: string[]; // conditions
  bx?: string; // bid exchange
  ax?: string; // ask exchange
}

interface RateLimitQueue {
  requests: number;
  resetTime: number;
  maxRequests: number;
  windowMs: number;
}

export class AlpacaIntegration extends EventEmitter {
  private config: AlpacaConfig;
  private httpClient: AxiosInstance;
  private dataClient: AxiosInstance;
  private ws: WebSocket | null = null;
  private rateLimitQueue: RateLimitQueue;
  private isConnected = false;
  private isAuthenticated = false;
  private subscriptions: Set<string> = new Set();

  constructor(config: AlpacaConfig) {
    super();
    this.config = {
      baseUrl: config.isPaper ? 'https://paper-api.alpaca.markets' : 'https://api.alpaca.markets',
      dataUrl: 'https://data.alpaca.markets',
      streamUrl: config.isPaper ? 'wss://paper-api.alpaca.markets/stream' : 'wss://api.alpaca.markets/stream',
      ...config
    };

    // Initialize rate limiting (200 RPM for basic plan)
    this.rateLimitQueue = {
      requests: 0,
      resetTime: Date.now() + 60000,
      maxRequests: 200,
      windowMs: 60000
    };

    // Initialize HTTP clients
    this.httpClient = axios.create({
      baseURL: this.config.baseUrl,
      headers: this.getAuthHeaders(),
      timeout: 30000
    });

    this.dataClient = axios.create({
      baseURL: this.config.dataUrl,
      headers: this.getAuthHeaders(),
      timeout: 30000
    });

    // Add request interceptor for rate limiting
    this.dataClient.interceptors.request.use(async (config) => {
      await this.checkRateLimit();
      return config;
    });

    // Add response interceptor for error handling
    this.dataClient.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('Alpaca API Error:', error.response?.data || error.message);
        throw error;
      }
    );
  }

  private getAuthHeaders() {
    return {
      'APCA-API-KEY-ID': this.config.apiKey,
      'APCA-API-SECRET-KEY': this.config.apiSecret,
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    };
  }

  private async checkRateLimit(): Promise<void> {
    const now = Date.now();
    
    // Reset counter if window has passed
    if (now >= this.rateLimitQueue.resetTime) {
      this.rateLimitQueue.requests = 0;
      this.rateLimitQueue.resetTime = now + this.rateLimitQueue.windowMs;
    }

    // Wait if rate limit exceeded
    if (this.rateLimitQueue.requests >= this.rateLimitQueue.maxRequests) {
      const waitTime = this.rateLimitQueue.resetTime - now;
      console.log(`Rate limit exceeded, waiting ${waitTime}ms`);
      await new Promise(resolve => setTimeout(resolve, waitTime));
      this.rateLimitQueue.requests = 0;
      this.rateLimitQueue.resetTime = Date.now() + this.rateLimitQueue.windowMs;
    }

    this.rateLimitQueue.requests++;
  }

  // Account and connection methods
  async testConnection(): Promise<boolean> {
    try {
      const response = await this.httpClient.get('/v2/account');
      console.log('✅ Alpaca connection successful');
      return response.status === 200;
    } catch (error) {
      console.error('❌ Alpaca connection failed:', error);
      return false;
    }
  }

  async getAccount(): Promise<any> {
    try {
      const response = await this.httpClient.get('/v2/account');
      return response.data;
    } catch (error) {
      console.error('Error fetching account:', error);
      throw error;
    }
  }

  // Options data methods
  async getOptionContracts(underlyingSymbol: string, expiration?: string): Promise<OptionContract[]> {
    try {
      const params: any = {
        underlying_symbols: underlyingSymbol,
        limit: 1000
      };

      if (expiration) {
        params.expiration_date = expiration;
      }

      console.log(`🔍 Fetching option contracts for ${underlyingSymbol}${expiration ? ` expiring ${expiration}` : ''}`);
      console.log(`📡 API call: GET /v2/options/contracts with params:`, params);

      const response = await this.httpClient.get('/v2/options/contracts', { params });
      const contracts = response.data.option_contracts || [];
      
      console.log(`📊 Received ${contracts.length} option contracts from Alpaca API`);
      if (contracts.length === 0) {
        console.warn(`⚠️ No option contracts found for ${underlyingSymbol}${expiration ? ` expiring ${expiration}` : ''}`);
        console.warn(`   This may indicate:`);
        console.warn(`   - Symbol ${underlyingSymbol} doesn't have options`);
        console.warn(`   - Expiration date ${expiration} has no contracts`);
        console.warn(`   - API permissions issue`);
        console.warn(`   - Historical date outside available range`);
      }
      
      return contracts;
    } catch (error) {
      console.error(`❌ Error fetching option contracts for ${underlyingSymbol}:`, error);
      throw error;
    }
  }

  async getOptionContract(symbolOrId: string): Promise<OptionContract | null> {
    try {
      const response = await this.httpClient.get(`/v2/options/contracts/${symbolOrId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching option contract:', error);
      return null;
    }
  }

  // Market data methods
  async getStockBars(
    symbol: string,
    timeframe: '1Min' | '5Min' | '15Min' | '1Hour' | '1Day',
    start: Date,
    end: Date,
    limit: number = 1000
  ): Promise<BarData[]> {
    try {
      const response = await this.dataClient.get(`/v2/stocks/${symbol}/bars`, {
        params: {
          timeframe,
          start: start.toISOString(),
          end: end.toISOString(),
          limit,
          adjustment: 'raw'
        }
      });

      return response.data.bars || [];
    } catch (error) {
      console.error('Error fetching stock bars:', error);
      throw error;
    }
  }

  async getOptionBars(
    symbol: string,
    timeframe: '1Min' | '5Min' | '15Min' | '1Hour' | '1Day',
    start: Date,
    end: Date,
    limit: number = 1000
  ): Promise<BarData[]> {
    try {
      // Use the correct Alpaca options API endpoint
      const response = await this.dataClient.get(`/v1beta1/options/bars`, {
        params: {
          symbols: symbol,
          timeframe,
          start: start.toISOString(),
          end: end.toISOString(),
          limit
        }
      });

      return response.data.bars?.[symbol] || [];
    } catch (error) {
      console.error('Error fetching option bars:', error);
      throw error;
    }
  }

  async getLatestQuote(symbol: string): Promise<QuoteData | null> {
    try {
      const response = await this.dataClient.get(`/v2/stocks/${symbol}/quotes/latest`);
      return response.data.quote;
    } catch (error) {
      console.error('Error fetching latest quote:', error);
      return null;
    }
  }

  async getOptionQuotes(symbols: string[]): Promise<{ [symbol: string]: QuoteData }> {
    try {
      // Handle empty symbols array to prevent API 404 error
      if (!symbols || symbols.length === 0) {
        console.warn('⚠️ getOptionQuotes called with empty symbols array - returning empty quotes');
        return {};
      }

      console.log(`🔍 Fetching option quotes for ${symbols.length} symbols...`);

      // Alpaca has a 100 symbol limit per API call, so we need to batch
      const BATCH_SIZE = 100;
      const allQuotes: { [symbol: string]: QuoteData } = {};
      
      for (let i = 0; i < symbols.length; i += BATCH_SIZE) {
        const batch = symbols.slice(i, i + BATCH_SIZE);
        const symbolsParam = batch.join(',');
        
        console.log(`📦 Fetching batch ${Math.floor(i / BATCH_SIZE) + 1}/${Math.ceil(symbols.length / BATCH_SIZE)} (${batch.length} symbols)`);

        try {
          // Use the correct Alpaca options API endpoint
          const response = await this.dataClient.get('/v1beta1/options/quotes/latest', {
            params: {
              symbols: symbolsParam
            }
          });

          const batchQuotes = response.data.quotes || {};
          Object.assign(allQuotes, batchQuotes);
          
          console.log(`✅ Batch ${Math.floor(i / BATCH_SIZE) + 1}: Received ${Object.keys(batchQuotes).length}/${batch.length} quotes`);
          
          // Add small delay between batches to respect rate limits
          if (i + BATCH_SIZE < symbols.length) {
            await new Promise(resolve => setTimeout(resolve, 100));
          }
        } catch (batchError) {
          console.error(`❌ Error fetching batch ${Math.floor(i / BATCH_SIZE) + 1}:`, batchError);
          // Continue with other batches even if one fails
        }
      }

      console.log(`📊 Total quotes received: ${Object.keys(allQuotes).length}/${symbols.length} option symbols`);
      return allQuotes;
    } catch (error) {
      console.error('❌ Error fetching option quotes:', error);
      return {};
    }
  }

  // WebSocket streaming methods
  async connectStream(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(`${this.config.streamUrl}`);

        this.ws.on('open', () => {
          console.log('✅ WebSocket connected');
          this.isConnected = true;
          this.authenticate();
        });

        this.ws.on('message', (data: Buffer) => {
          try {
            const message = JSON.parse(data.toString());
            this.handleWebSocketMessage(message);
            
            if (message.stream === 'authorization' && message.data?.status === 'authorized') {
              this.isAuthenticated = true;
              resolve();
            }
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        });

        this.ws.on('error', (error) => {
          console.error('WebSocket error:', error);
          this.isConnected = false;
          this.isAuthenticated = false;
          reject(error);
        });

        this.ws.on('close', () => {
          console.log('WebSocket disconnected');
          this.isConnected = false;
          this.isAuthenticated = false;
          this.emit('disconnected');
        });

      } catch (error) {
        reject(error);
      }
    });
  }

  private authenticate(): void {
    if (this.ws && this.isConnected) {
      const authMessage = {
        action: 'auth',
        key: this.config.apiKey,
        secret: this.config.apiSecret
      };
      this.ws.send(JSON.stringify(authMessage));
    }
  }

  private handleWebSocketMessage(message: any): void {
    switch (message.stream) {
      case 'authorization':
        if (message.data?.status === 'authorized') {
          console.log('✅ WebSocket authenticated');
          this.emit('authenticated');
        } else {
          console.error('❌ WebSocket authentication failed');
          this.emit('auth_failed');
        }
        break;

      case 'listening':
        console.log('✅ Subscribed to streams:', message.data?.streams);
        this.emit('subscribed', message.data?.streams);
        break;

      case 'trade_updates':
        this.emit('trade_update', message.data);
        break;

      default:
        this.emit('message', message);
        break;
    }
  }

  async subscribeToTradeUpdates(): Promise<void> {
    if (!this.isAuthenticated) {
      throw new Error('WebSocket not authenticated');
    }

    const subscribeMessage = {
      action: 'listen',
      data: {
        streams: ['trade_updates']
      }
    };

    this.ws?.send(JSON.stringify(subscribeMessage));
  }

  // Market data streaming (separate WebSocket)
  async connectMarketDataStream(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const marketDataUrl = 'wss://stream.data.alpaca.markets/v2/sip';
        this.ws = new WebSocket(marketDataUrl, {
          headers: this.getAuthHeaders()
        });

        this.ws.on('open', () => {
          console.log('✅ Market data stream connected');
          this.authenticateMarketData();
        });

        this.ws.on('message', (data: Buffer) => {
          try {
            const messages = JSON.parse(data.toString());
            if (Array.isArray(messages)) {
              messages.forEach(msg => this.handleMarketDataMessage(msg));
            }
            
            // Check for authentication success
            const authMsg = messages.find((m: any) => m.T === 'success' && m.msg === 'authenticated');
            if (authMsg) {
              resolve();
            }
          } catch (error) {
            console.error('Error parsing market data message:', error);
          }
        });

        this.ws.on('error', (error) => {
          console.error('Market data stream error:', error);
          reject(error);
        });

      } catch (error) {
        reject(error);
      }
    });
  }

  private authenticateMarketData(): void {
    if (this.ws) {
      const authMessage = {
        action: 'auth',
        key: this.config.apiKey,
        secret: this.config.apiSecret
      };
      this.ws.send(JSON.stringify(authMessage));
    }
  }

  private handleMarketDataMessage(message: any): void {
    switch (message.T) {
      case 'success':
        if (message.msg === 'authenticated') {
          console.log('✅ Market data stream authenticated');
          this.emit('market_data_authenticated');
        }
        break;

      case 'subscription':
        console.log('✅ Market data subscriptions:', message);
        this.emit('market_data_subscribed', message);
        break;

      case 't': // Trade
        this.emit('trade', message);
        break;

      case 'q': // Quote
        this.emit('quote', message);
        break;

      case 'b': // Bar
        this.emit('bar', message);
        break;

      case 'error':
        console.error('Market data error:', message);
        this.emit('market_data_error', message);
        break;

      default:
        this.emit('market_data_message', message);
        break;
    }
  }

  async subscribeToMarketData(symbols: string[], dataTypes: ('trades' | 'quotes' | 'bars')[] = ['trades', 'quotes']): Promise<void> {
    if (!this.ws) {
      throw new Error('Market data stream not connected');
    }

    const subscription: any = { action: 'subscribe' };
    
    if (dataTypes.includes('trades')) {
      subscription.trades = symbols;
    }
    if (dataTypes.includes('quotes')) {
      subscription.quotes = symbols;
    }
    if (dataTypes.includes('bars')) {
      subscription.bars = symbols;
    }

    this.ws.send(JSON.stringify(subscription));
    
    // Track subscriptions
    symbols.forEach(symbol => {
      dataTypes.forEach(type => {
        this.subscriptions.add(`${type}:${symbol}`);
      });
    });
  }

  // Trading methods
  async placeOrder(order: {
    symbol: string;
    qty: number;
    side: 'buy' | 'sell';
    type: 'market' | 'limit' | 'stop' | 'stop_limit';
    time_in_force: 'day' | 'gtc' | 'ioc' | 'fok';
    limit_price?: number;
    stop_price?: number;
    extended_hours?: boolean;
  }): Promise<any> {
    try {
      const response = await this.httpClient.post('/v2/orders', order);
      return response.data;
    } catch (error) {
      console.error('Error placing order:', error);
      throw error;
    }
  }

  async getPositions(): Promise<Position[]> {
    try {
      const response = await this.httpClient.get('/v2/positions');
      return response.data.map((pos: any) => this.mapToPosition(pos));
    } catch (error) {
      console.error('Error fetching positions:', error);
      throw error;
    }
  }

  private mapToPosition(alpacaPosition: any): Position {
    return {
      id: alpacaPosition.asset_id,
      symbol: alpacaPosition.symbol,
      side: alpacaPosition.side === 'long' ? 'CALL' : 'PUT', // Simplified mapping
      strike: 0, // Would need to parse from option symbol
      expiration: new Date(), // Would need to parse from option symbol
      quantity: parseInt(alpacaPosition.qty),
      entryPrice: parseFloat(alpacaPosition.avg_entry_price),
      currentPrice: parseFloat(alpacaPosition.market_value) / parseInt(alpacaPosition.qty),
      entryTime: new Date(alpacaPosition.created_at),
      unrealizedPnL: parseFloat(alpacaPosition.unrealized_pl),
      unrealizedPnLPercent: parseFloat(alpacaPosition.unrealized_plpc) * 100,
      is0DTE: false, // Would need to calculate based on expiration
      timeDecayRisk: 'MEDIUM',
      momentumScore: 0,
      exitStrategy: 'SIGNAL_BASED'
    };
  }

  // Cleanup
  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.isConnected = false;
    this.isAuthenticated = false;
    this.subscriptions.clear();
  }

  // Utility methods
  isMarketOpen(): boolean {
    const now = new Date();
    const marketOpen = new Date(now);
    marketOpen.setHours(9, 30, 0, 0);
    const marketClose = new Date(now);
    marketClose.setHours(16, 0, 0, 0);

    return now >= marketOpen && now <= marketClose && now.getDay() >= 1 && now.getDay() <= 5;
  }

  getSubscriptions(): string[] {
    return Array.from(this.subscriptions);
  }

  // Additional methods for backward compatibility
  async getMarketData(
    symbol: string,
    startDate: Date,
    endDate: Date,
    timeframe: '1Min' | '5Min' | '15Min' | '1Hour' | '1Day' = '1Min'
  ): Promise<MarketData[]> {
    const bars = await this.getStockBars(symbol, timeframe, startDate, endDate);
    return bars.map(bar => ({
      timestamp: new Date(bar.t),
      open: bar.o,
      high: bar.h,
      low: bar.l,
      close: bar.c,
      volume: bar.v,
      vwap: bar.vw,
      symbol
    }));
  }

  async getOptionsChain(symbol: string, expiration?: string): Promise<OptionsChain[]> {
    const contracts = await this.getOptionContracts(symbol, expiration);
    const quotes = await this.getOptionQuotes(contracts.map(c => c.symbol));
    
    return contracts.map(contract => {
      const quote = quotes[contract.symbol];
      return {
        symbol: contract.symbol,
        strike: parseFloat(contract.strike_price),
        expiration: new Date(contract.expiration_date),
        type: contract.type.toUpperCase() as 'CALL' | 'PUT',
        bid: quote?.bp || 0,
        ask: quote?.ap || 0,
        last: parseFloat(contract.close_price || '0'),
        volume: 0, // Would need separate API call
        openInterest: parseInt(contract.open_interest || '0'),
        impliedVolatility: 0.25, // Would need calculation
        delta: 0, // Would need calculation
        gamma: 0,
        theta: 0,
        vega: 0,
        rho: 0
      };
    });
  }

  /**
   * Get historical options chain for a specific date using REAL Alpaca data first, then Black-Scholes fallback:
   * 1. Try to get REAL historical options data from Polygon.io (Options Starter Plan - PRIMARY)
   * 2. If no Polygon data, try REAL historical options data from Alpaca (backup)
   * 3. If no real data available, fall back to Black-Scholes with real market inputs
   * 4. Use current option contracts for strikes/expirations structure
   * 5. Get historical stock price and VIX data from real sources
   */
  async getHistoricalOptionsChain(symbol: string, date: Date): Promise<OptionsChain[]> {
    try {
      console.log(`📊 Fetching historical options chain for ${symbol} on ${date.toDateString()}...`);

      // STEP 1: Try to get REAL historical options data from Polygon.io (Options Starter Plan)
      console.log(`🎯 STEP 1: Attempting to fetch REAL historical options data from Polygon.io...`);
      const polygonOptionsChain = await this.getHistoricalOptionsFromPolygon(symbol, date);
      
      if (polygonOptionsChain && Object.keys(polygonOptionsChain).length > 0) {
        console.log(`🎉 SUCCESS: Found REAL historical options data from Polygon.io!`);
        
        // Convert Polygon data to OptionsChain[] format expected by the system
        const allOptions: OptionsChain[] = [];
        Object.keys(polygonOptionsChain).forEach(expDate => {
          const optionsForExpiration = polygonOptionsChain[expDate];
          optionsForExpiration.forEach((option: any) => {
            allOptions.push({
              symbol: option.symbol,
              strike: option.strike_price,
              expiration: new Date(option.expiration_date),
              type: option.option_type.toUpperCase() as 'CALL' | 'PUT',
              bid: option.bid,
              ask: option.ask,
              last: option.last_price,
              volume: option.volume,
              openInterest: option.open_interest,
              impliedVolatility: option.implied_volatility,
              delta: option.delta,
              gamma: option.gamma,
              theta: option.theta,
              vega: option.vega,
              rho: option.rho
            });
          });
        });
        
        return allOptions; // Return as single array of all options
      }

      console.log(`⚠️ No historical options data from Polygon.io, falling back to hybrid approach...`);

      // Get historical stock price for fallback approach
      const endDate = new Date(date);
      endDate.setDate(endDate.getDate() + 1); // Add one day for end date
      
      const stockData = await this.getMarketData(symbol, date, endDate, '1Day');
      if (stockData.length === 0) {
        throw new Error(`No historical market data available for ${symbol} on ${date.toDateString()}`);
      }

      const historicalPrice = stockData[0].close;
      console.log(`📊 Historical ${symbol} price on ${date.toDateString()}: $${historicalPrice.toFixed(2)}`);

      // Get current option contracts for strikes/expirations structure
      console.log(`🔍 Fetching current option contracts for strike/expiration structure...`);
      const allCurrentContracts = await this.getOptionContracts(symbol);
      
      // Filter contracts for reasonable strikes (we'll create synthetic expirations for historical dates)
      // For historical backtesting, we use current strikes but create appropriate historical expirations
      const relevantContracts = allCurrentContracts.filter(contract => {
        const strike = parseFloat(contract.strike_price);
        
        return (
          strike >= historicalPrice * 0.7 && // Strike within 30% below historical price
          strike <= historicalPrice * 1.3    // Strike within 30% above historical price
        );
      }).slice(0, 200); // Limit to 200 most relevant contracts for performance

      console.log(`📊 Found ${relevantContracts.length} relevant contracts`);

      if (relevantContracts.length === 0) {
        console.warn(`⚠️ No relevant contracts found for ${date.toDateString()}`);
        return [];
      }

      // STEP 2: Try to get REAL historical options data from Alpaca (backup)
      console.log(`🎯 STEP 2: Attempting to fetch REAL historical options data from Alpaca...`);
      const contractSymbols = relevantContracts.map(c => c.symbol);
      const realHistoricalBars = await this.getHistoricalOptionBarsCorrect(contractSymbols, date);
      
      if (Object.keys(realHistoricalBars).length > 0) {
        console.log(`🎉 SUCCESS: Found ${Object.keys(realHistoricalBars).length} REAL historical options bars from Alpaca!`);
        
        // Convert real historical bars to OptionsChain format
        const optionsChain: OptionsChain[] = [];
        
        for (const contract of relevantContracts) {
          const bar = realHistoricalBars[contract.symbol];
          if (bar && bar.c > 0) { // Only include contracts with valid pricing data
            optionsChain.push({
              symbol: contract.symbol,
              strike: parseFloat(contract.strike_price),
              expiration: new Date(contract.expiration_date),
              type: contract.type.toUpperCase() as 'CALL' | 'PUT',
              bid: bar.c * 0.98, // Estimate bid as 2% below close
              ask: bar.c * 1.02, // Estimate ask as 2% above close
              last: bar.c,
              volume: bar.v || 0,
              openInterest: parseInt(contract.open_interest || '0'),
              impliedVolatility: 0.25, // Would need calculation from real price
              delta: 0, // Would need calculation from real price
              gamma: 0,
              theta: 0,
              vega: 0,
              rho: 0
            });
          }
        }
        
        console.log(`✅ Built options chain with ${optionsChain.length} REAL historical options from Alpaca`);
        return optionsChain;
      }

      // STEP 2: Fall back to Black-Scholes pricing with real market data
      console.log(`📊 STEP 2: No real options data available, falling back to Black-Scholes with real market inputs...`);
      
      // Get historical VIX data for volatility
      const vixData = await this.getHistoricalVIX(date);
      const impliedVolatility = vixData / 100; // Convert VIX percentage to decimal
      console.log(`📊 Historical VIX on ${date.toDateString()}: ${vixData.toFixed(2)}% (IV: ${(impliedVolatility * 100).toFixed(1)}%)`);

      // Get risk-free rate (approximate using 10-year Treasury rate)
      const riskFreeRate = await this.getRiskFreeRate(date);
      console.log(`📊 Risk-free rate on ${date.toDateString()}: ${(riskFreeRate * 100).toFixed(2)}%`);

      // Create appropriate historical expirations (weekly and monthly options that would have existed)
      const historicalExpirations = this.generateHistoricalExpirations(date);
      console.log(`📅 Generated ${historicalExpirations.length} historical expirations for ${date.toDateString()}`);

      // Calculate option prices using Black-Scholes model
      const optionsChain: OptionsChain[] = [];
      
      // Create options for each strike and expiration combination
      for (const contract of relevantContracts) {
        const strike = parseFloat(contract.strike_price);
        const contractType = contract.type.toUpperCase();
        
        for (const expDate of historicalExpirations) {
          const timeToExpiration = (expDate.getTime() - date.getTime()) / (1000 * 60 * 60 * 24 * 365.25); // Years
          
          if (timeToExpiration > 0 && timeToExpiration <= 0.25) { // Only options expiring within 3 months
            const isCall = contractType === 'CALL';
            
            // Calculate Black-Scholes price and Greeks
            const pricing = this.calculateBlackScholesPrice(
              historicalPrice,
              strike,
              timeToExpiration,
              riskFreeRate,
              impliedVolatility,
              isCall
            );
            
            // Create a historical option symbol
            const historicalSymbol = this.createHistoricalOptionSymbol(symbol, expDate, strike, isCall);
            
            optionsChain.push({
              symbol: historicalSymbol,
              strike: strike,
              expiration: expDate,
              type: contractType as 'CALL' | 'PUT',
              bid: pricing.price * 0.98, // Estimate bid as 2% below theoretical price
              ask: pricing.price * 1.02, // Estimate ask as 2% above theoretical price
              last: pricing.price,
              volume: 0, // Historical volume not available
              openInterest: 100, // Estimate reasonable open interest
              impliedVolatility: impliedVolatility,
              delta: pricing.delta,
              gamma: pricing.gamma,
              theta: pricing.theta,
              vega: pricing.vega,
              rho: pricing.rho
            });
          }
        }
      }

      console.log(`✅ Calculated ${optionsChain.length} historical option prices using Black-Scholes for ${date.toDateString()}`);
      return optionsChain;

    } catch (error) {
      console.error(`Error calculating historical options chain for ${date.toDateString()}:`, error);
      throw error;
    }
  }

  /**
   * Get historical option bars using the CORRECT Alpaca API endpoint
   * This uses the actual Alpaca historical options bars API that works with real data
   */
  private async getHistoricalOptionBarsCorrect(symbols: string[], date: Date): Promise<{ [symbol: string]: BarData }> {
    const results: { [symbol: string]: BarData } = {};
    
    // Batch symbols to avoid API limits
    const batchSize = 50; // Conservative batch size for historical data
    const batches = [];
    for (let i = 0; i < symbols.length; i += batchSize) {
      batches.push(symbols.slice(i, i + batchSize));
    }

    console.log(`📊 Fetching REAL historical option bars in ${batches.length} batches for ${date.toDateString()}...`);

    for (let i = 0; i < batches.length; i++) {
      const batch = batches[i];
      try {
        console.log(`📦 Processing batch ${i + 1}/${batches.length} (${batch.length} symbols)...`);
        
        const endDate = new Date(date);
        endDate.setDate(endDate.getDate() + 1);
        
        // Use the CORRECT Alpaca historical options bars API endpoint
        const response = await this.dataClient.get('/v1beta1/options/bars', {
          params: {
            symbols: batch.join(','),
            timeframe: '1Day',
            start: date.toISOString().split('T')[0], // Use date format YYYY-MM-DD
            end: endDate.toISOString().split('T')[0],   // Use date format YYYY-MM-DD
            limit: 1000
          }
        });

        console.log(`🔍 REAL API response for batch ${i + 1}:`, JSON.stringify(response.data, null, 2));
        const bars = response.data.bars || {};
        
        // Process each symbol's bars
        for (const symbol of batch) {
          const symbolBars = bars[symbol];
          if (symbolBars && symbolBars.length > 0) {
            const bar = symbolBars[0]; // Get the first (and likely only) bar for the date
            results[symbol] = {
              t: bar.t,
              o: bar.o,
              h: bar.h,
              l: bar.l,
              c: bar.c,
              v: bar.v,
              vw: bar.vw || bar.c
            };
          }
        }

        console.log(`✅ Batch ${i + 1} completed: ${Object.keys(bars).length} symbols with data`);
        
        // Add delay between batches to respect rate limits
        if (i < batches.length - 1) {
          await new Promise(resolve => setTimeout(resolve, 200));
        }
        
      } catch (error) {
        console.warn(`⚠️ Error fetching batch ${i + 1}:`, error);
      }
    }

    console.log(`📊 Retrieved REAL historical bars for ${Object.keys(results).length}/${symbols.length} option symbols`);
    return results;
  }

  /**
   * Get historical option bars for multiple symbols on a specific date (OLD METHOD - DEPRECATED)
   */
  private async getHistoricalOptionBars(symbols: string[], date: Date): Promise<{ [symbol: string]: BarData }> {
    const results: { [symbol: string]: BarData } = {};
    
    // Batch symbols to avoid API limits
    const batchSize = 50; // Conservative batch size for historical data
    const batches = [];
    for (let i = 0; i < symbols.length; i += batchSize) {
      batches.push(symbols.slice(i, i + batchSize));
    }

    console.log(`📊 Fetching historical option bars in ${batches.length} batches for ${date.toDateString()}...`);

    for (let i = 0; i < batches.length; i++) {
      const batch = batches[i];
      try {
        console.log(`📦 Processing batch ${i + 1}/${batches.length} (${batch.length} symbols)...`);
        
        const endDate = new Date(date);
        endDate.setDate(endDate.getDate() + 1);
        
        const response = await this.dataClient.get('/v1beta1/options/bars', {
          params: {
            symbols: batch.join(','),
            timeframe: '1Day',
            start: date.toISOString(),
            end: endDate.toISOString(),
            limit: 1000
          }
        });

        // DEBUG: Alpaca historical options bars API returns empty data - confirmed limitation
        const bars = response.data.bars || {};
        
        // Process each symbol's bars
        for (const symbol of batch) {
          const symbolBars = bars[symbol];
          if (symbolBars && symbolBars.length > 0) {
            const bar = symbolBars[0]; // Get the first (and likely only) bar for the date
            results[symbol] = {
              t: bar.t,
              o: bar.o,
              h: bar.h,
              l: bar.l,
              c: bar.c,
              v: bar.v,
              vw: bar.vw || bar.c
            };
          }
        }

        console.log(`✅ Batch ${i + 1} completed: ${Object.keys(bars).length} symbols with data`);
        
        // Add delay between batches to respect rate limits
        if (i < batches.length - 1) {
          await new Promise(resolve => setTimeout(resolve, 200));
        }
        
      } catch (error) {
        console.warn(`⚠️ Error fetching batch ${i + 1}:`, error);
      }
    }

    console.log(`📊 Retrieved historical bars for ${Object.keys(results).length}/${symbols.length} option symbols`);
    return results;
  }

  /**
   * Get expiration dates that would have been available on a historical date
   */
  private getHistoricalExpirations(date: Date): Date[] {
    const expirations: Date[] = [];
    const currentDate = new Date(date);
    
    // Find the next few Fridays from the given date (typical options expiration)
    for (let i = 0; i < 8; i++) { // Look ahead 8 weeks
      const nextFriday = new Date(currentDate);
      const daysUntilFriday = (5 - currentDate.getDay() + 7) % 7;
      nextFriday.setDate(currentDate.getDate() + daysUntilFriday + (i * 7));
      
      // Only include expirations that are in the future from the historical date
      if (nextFriday > date) {
        expirations.push(nextFriday);
      }
    }
    
    // Add monthly expirations (3rd Friday of each month)
    for (let monthOffset = 0; monthOffset < 6; monthOffset++) {
      const monthlyExp = new Date(date.getFullYear(), date.getMonth() + monthOffset, 1);
      const thirdFriday = this.getThirdFriday(monthlyExp);
      
      if (thirdFriday > date && !expirations.some(exp => exp.getTime() === thirdFriday.getTime())) {
        expirations.push(thirdFriday);
      }
    }
    
    return expirations.sort((a, b) => a.getTime() - b.getTime()).slice(0, 10); // Limit to 10 expirations
  }

  /**
   * Get the third Friday of a given month
   */
  private getThirdFriday(date: Date): Date {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1);
    const firstFriday = new Date(year, month, 1 + (5 - firstDay.getDay() + 7) % 7);
    return new Date(year, month, firstDay.getDate() + 14); // Third Friday is 14 days after first Friday
  }

  /**
   * Generate historical expirations that would have been available on a given date
   */
  private generateHistoricalExpirations(date: Date): Date[] {
    const expirations: Date[] = [];
    const currentDate = new Date(date);
    
    // Add weekly expirations (every Friday for the next 8 weeks)
    for (let weeks = 0; weeks < 8; weeks++) {
      const friday = new Date(currentDate);
      const daysUntilFriday = (5 - currentDate.getDay() + 7) % 7;
      friday.setDate(currentDate.getDate() + daysUntilFriday + (weeks * 7));
      
      if (friday > date) {
        expirations.push(friday);
      }
    }
    
    // Add monthly expirations (3rd Friday of each month for the next 6 months)
    for (let monthOffset = 0; monthOffset < 6; monthOffset++) {
      const monthlyExp = new Date(date.getFullYear(), date.getMonth() + monthOffset, 1);
      const thirdFriday = this.getThirdFriday(monthlyExp);
      
      if (thirdFriday > date && !expirations.some(exp => exp.getTime() === thirdFriday.getTime())) {
        expirations.push(thirdFriday);
      }
    }
    
    return expirations.sort((a, b) => a.getTime() - b.getTime()).slice(0, 12); // Limit to 12 expirations
  }

  /**
   * Create a historical option symbol in the standard format
   */
  private createHistoricalOptionSymbol(underlying: string, expiration: Date, strike: number, isCall: boolean): string {
    const year = expiration.getFullYear().toString().slice(-2);
    const month = String(expiration.getMonth() + 1).padStart(2, '0');
    const day = String(expiration.getDate()).padStart(2, '0');
    const callPut = isCall ? 'C' : 'P';
    const strikeStr = String(Math.round(strike * 1000)).padStart(8, '0');
    
    return `${underlying}${year}${month}${day}${callPut}${strikeStr}`;
  }

  /**
   * Get historical VIX data for a specific date
   */
  private async getHistoricalVIX(date: Date): Promise<number> {
    try {
      // Import VIX provider dynamically
      const FreeVIXDataProvider = (await import('../data/free-vix-providers')).default;
      const vixData = await FreeVIXDataProvider.getCurrentVIX(date);
      
      if (vixData && vixData.value > 0) {
        console.log(`📊 Using real VIX data: ${vixData.value.toFixed(2)}%`);
        return vixData.value;
      } else {
        // Fallback to estimated VIX based on historical averages
        const estimatedVIX = this.estimateHistoricalVIX(date);
        console.log(`📊 Using estimated VIX: ${estimatedVIX.toFixed(2)}%`);
        return estimatedVIX;
      }
    } catch (error) {
      console.warn(`⚠️ Could not fetch VIX data, using estimate:`, error);
      return this.estimateHistoricalVIX(date);
    }
  }

  /**
   * Estimate historical VIX based on date and market conditions
   */
  private estimateHistoricalVIX(date: Date): number {
    // Historical VIX averages by period
    const year = date.getFullYear();
    const month = date.getMonth();
    
    // 2024 VIX averages (approximate)
    if (year === 2024) {
      if (month >= 0 && month <= 2) return 16.5; // Q1 2024
      if (month >= 3 && month <= 5) return 14.2; // Q2 2024
      if (month >= 6 && month <= 8) return 18.8; // Q3 2024
      if (month >= 9 && month <= 11) return 20.1; // Q4 2024
    }
    
    // Default to long-term VIX average
    return 19.5;
  }

  /**
   * Get risk-free rate for a specific date (approximate using historical averages)
   */
  private async getRiskFreeRate(date: Date): Promise<number> {
    // Approximate 10-year Treasury rates by period
    const year = date.getFullYear();
    
    if (year === 2024) {
      return 0.042; // ~4.2% average for 2024
    } else if (year === 2023) {
      return 0.038; // ~3.8% average for 2023
    } else if (year >= 2025) {
      return 0.045; // ~4.5% estimate for 2025
    }
    
    // Default to long-term average
    return 0.035; // 3.5%
  }

  /**
   * Calculate Black-Scholes option price and Greeks
   */
  private calculateBlackScholesPrice(
    stockPrice: number,
    strikePrice: number,
    timeToExpiration: number,
    riskFreeRate: number,
    volatility: number,
    isCall: boolean
  ): {
    price: number;
    delta: number;
    gamma: number;
    theta: number;
    vega: number;
    rho: number;
  } {
    // Prevent division by zero and negative values
    if (timeToExpiration <= 0 || volatility <= 0 || stockPrice <= 0 || strikePrice <= 0) {
      return {
        price: 0,
        delta: 0,
        gamma: 0,
        theta: 0,
        vega: 0,
        rho: 0
      };
    }

    const d1 = (Math.log(stockPrice / strikePrice) + (riskFreeRate + 0.5 * volatility * volatility) * timeToExpiration) / 
               (volatility * Math.sqrt(timeToExpiration));
    const d2 = d1 - volatility * Math.sqrt(timeToExpiration);

    // Standard normal cumulative distribution function
    const N = (x: number) => {
      const a1 =  0.254829592;
      const a2 = -0.284496736;
      const a3 =  1.421413741;
      const a4 = -1.453152027;
      const a5 =  1.061405429;
      const p  =  0.3275911;
      
      const sign = x < 0 ? -1 : 1;
      x = Math.abs(x) / Math.sqrt(2.0);
      
      const t = 1.0 / (1.0 + p * x);
      const y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * Math.exp(-x * x);
      
      return 0.5 * (1.0 + sign * y);
    };

    // Standard normal probability density function
    const n = (x: number) => Math.exp(-0.5 * x * x) / Math.sqrt(2 * Math.PI);

    const Nd1 = N(d1);
    const Nd2 = N(d2);
    const nd1 = n(d1);

    let price: number;
    let delta: number;
    let rho: number;

    if (isCall) {
      price = stockPrice * Nd1 - strikePrice * Math.exp(-riskFreeRate * timeToExpiration) * Nd2;
      delta = Nd1;
      rho = strikePrice * timeToExpiration * Math.exp(-riskFreeRate * timeToExpiration) * Nd2;
    } else {
      price = strikePrice * Math.exp(-riskFreeRate * timeToExpiration) * N(-d2) - stockPrice * N(-d1);
      delta = -N(-d1);
      rho = -strikePrice * timeToExpiration * Math.exp(-riskFreeRate * timeToExpiration) * N(-d2);
    }

    // Greeks (same for calls and puts)
    const gamma = nd1 / (stockPrice * volatility * Math.sqrt(timeToExpiration));
    const theta = (-stockPrice * nd1 * volatility / (2 * Math.sqrt(timeToExpiration)) - 
                   riskFreeRate * strikePrice * Math.exp(-riskFreeRate * timeToExpiration) * 
                   (isCall ? Nd2 : N(-d2))) / 365.25; // Convert to daily theta
    const vega = stockPrice * nd1 * Math.sqrt(timeToExpiration) / 100; // Convert to 1% volatility change

    return {
      price: Math.max(0, price), // Ensure non-negative price
      delta,
      gamma,
      theta,
      vega,
      rho: rho / 100 // Convert to 1% rate change
    };
  }

  /**
   * Get historical options data from Polygon.io (Options Starter Plan)
   * This is the primary method for accessing real historical options data
   */
  async getHistoricalOptionsFromPolygon(
    underlyingSymbol: string,
    date: Date,
    expirationDates?: string[]
  ): Promise<{ [expiration: string]: any[] } | null> {
    const polygonApiKey = process.env.POLYGON_API_KEY;
    if (!polygonApiKey) {
      console.warn('⚠️ Polygon API key not found, cannot fetch historical options data');
      return null;
    }

    console.log(`📊 Fetching historical options data from Polygon.io for ${underlyingSymbol} on ${date.toDateString()}`);

    try {
      // Step 1: Get available options contracts for the underlying symbol
      const contractsUrl = `https://api.polygon.io/v3/reference/options/contracts`;
      const contractsParams = {
        'underlying_ticker': underlyingSymbol,
        'contract_type': 'option',
        'expiration_date.gte': date.toISOString().split('T')[0], // From target date
        'expiration_date.lte': this.getMaxExpirationDate(date), // Up to 60 days out
        'limit': 1000,
        'apikey': polygonApiKey
      };

      console.log(`🔍 Polygon.io API call parameters:`, contractsParams);

      console.log(`🔍 Fetching options contracts from Polygon.io...`);
      const contractsResponse = await axios.get(contractsUrl, {
        params: contractsParams,
        timeout: 30000
      });

      const contracts = contractsResponse.data.results || [];
      console.log(`📋 Found ${contracts.length} options contracts`);
      console.log(`🔍 Polygon.io response status:`, contractsResponse.data.status);
      console.log(`🔍 Polygon.io response count:`, contractsResponse.data.count);
      if (contracts.length === 0) {
        console.log(`🔍 Full Polygon.io response:`, JSON.stringify(contractsResponse.data, null, 2));
      }

      if (contracts.length === 0) {
        console.warn(`⚠️ No options contracts found for ${underlyingSymbol} on ${date.toDateString()}`);
        return null;
      }

      // Step 2: Get historical bars for each contract
      const dateStr = date.toISOString().split('T')[0];
      const optionsData: any[] = [];

      // Process contracts in batches to respect rate limits
      const batchSize = 10;
      for (let i = 0; i < contracts.length; i += batchSize) {
        const batch = contracts.slice(i, i + batchSize);
        
        const batchPromises = batch.map(async (contract: any) => {
          try {
            const barsUrl = `https://api.polygon.io/v2/aggs/ticker/${contract.ticker}/range/1/day/${dateStr}/${dateStr}`;
            const barsParams = {
              'adjusted': 'true',
              'sort': 'desc',
              'apikey': polygonApiKey
            };

            const barsResponse = await axios.get(barsUrl, {
              params: barsParams,
              timeout: 15000
            });

            const bars = barsResponse.data.results || [];
            if (bars.length > 0) {
              const bar = bars[0]; // Most recent bar for the date
              
              return {
                symbol: contract.ticker,
                underlying_symbol: contract.underlying_ticker,
                expiration_date: contract.expiration_date,
                strike_price: parseFloat(contract.strike_price),
                option_type: contract.contract_type.toLowerCase(),
                last_price: bar.c, // close price
                bid: bar.l, // use low as bid approximation
                ask: bar.h, // use high as ask approximation
                volume: bar.v,
                open_interest: contract.open_interest || 0,
                implied_volatility: null, // Not available from Polygon
                delta: null, // Will be calculated if needed
                gamma: null,
                theta: null,
                vega: null,
                rho: null,
                timestamp: new Date(bar.t)
              };
            }
            return null;
          } catch (error) {
            console.warn(`⚠️ Failed to fetch bars for ${contract.ticker}:`, error instanceof Error ? error.message : String(error));
            return null;
          }
        });

        const batchResults = await Promise.all(batchPromises);
        optionsData.push(...batchResults.filter(result => result !== null));

        // Add delay between batches to respect rate limits
        if (i + batchSize < contracts.length) {
          await new Promise(resolve => setTimeout(resolve, 100)); // 100ms delay
        }
      }

      console.log(`✅ Retrieved ${optionsData.length} options with historical data from Polygon.io`);

      if (optionsData.length === 0) {
        console.warn(`⚠️ No historical options data found for ${underlyingSymbol} on ${date.toDateString()}`);
        return null;
      }

      // Group by expiration date
      const optionsByExpiration: { [key: string]: any[] } = {};
      optionsData.forEach(option => {
        const expDate = option.expiration_date;
        if (!optionsByExpiration[expDate]) {
          optionsByExpiration[expDate] = [];
        }
        optionsByExpiration[expDate].push(option);
      });

      // Return the grouped options data
      return optionsByExpiration;

    } catch (error) {
      console.error('❌ Error fetching historical options data from Polygon.io:', error instanceof Error ? error.message : String(error));
      return null;
    }
  }

  /**
   * Get maximum expiration date for options contracts (60 days from target date)
   */
  private getMaxExpirationDate(date: Date): string {
    const maxDate = new Date(date);
    maxDate.setDate(maxDate.getDate() + 60); // 60 days out
    return maxDate.toISOString().split('T')[0];
  }
}

// Export a default instance for backward compatibility
export const alpacaClient = new AlpacaIntegration({
  apiKey: process.env.ALPACA_API_KEY || '',
  apiSecret: process.env.ALPACA_API_SECRET || '',
  isPaper: true
});
