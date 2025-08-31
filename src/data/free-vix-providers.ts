/**
 * 🌐 Free VIX Data Providers Integration
 * ====================================
 * 
 * Integration with free VIX data sources to comply with .cursorrules
 * requirement for real data usage in the Flyagonal strategy.
 * 
 * Free VIX Data Sources:
 * 1. Yahoo Finance (yfinance) - Most reliable
 * 2. Alpha Vantage (free tier) - 5 calls/minute, 500/day
 * 3. FRED (Federal Reserve) - Historical VIX data
 * 4. Quandl (free tier) - Limited but reliable
 * 5. Polygon.io (free tier) - 5 calls/minute
 * 6. Twelve Data (free tier) - 800 calls/day
 * 
 * @fileoverview Free VIX data provider integrations
 * @author Trading System Data Team
 * @version 1.0.0
 * @created 2025-08-30
 */

import axios from 'axios';

/**
 * VIX data point interface
 */
export interface VIXDataPoint {
  date: Date;
  value: number;
  source: string;
  timestamp: Date;
}

/**
 * VIX provider configuration
 */
export interface VIXProviderConfig {
  provider: 'yahoo' | 'alphavantage' | 'fred' | 'quandl' | 'polygon' | 'twelvedata';
  apiKey?: string;
  rateLimit?: {
    callsPerMinute: number;
    callsPerDay: number;
  };
  enabled: boolean;
}

/**
 * Free VIX Data Provider Manager
 */
export class FreeVIXDataProvider {
  private static providers: VIXProviderConfig[] = [
    {
      provider: 'yahoo',
      enabled: true,
      rateLimit: { callsPerMinute: 60, callsPerDay: 2000 } // Primary - working perfectly
    },
    {
      provider: 'alphavantage',
      apiKey: process.env.ALPHA_VANTAGE_API_KEY || 'XAZF4K40D1HMUEJK',
      enabled: true, // Backup provider
      rateLimit: { callsPerMinute: 5, callsPerDay: 500 }
    },
    {
      provider: 'polygon',
      apiKey: process.env.POLYGON_API_KEY || 'DX1NqXJ3L0Ru3vzeldlZ0hUeq1JJfdfP',
      enabled: true, // Backup (free tier doesn't include VIX)
      rateLimit: { callsPerMinute: 5, callsPerDay: 1000 }
    },
    {
      provider: 'fred',
      apiKey: process.env.FRED_API_KEY,
      enabled: !!process.env.FRED_API_KEY,
      rateLimit: { callsPerMinute: 120, callsPerDay: 1000 }
    },
    {
      provider: 'twelvedata',
      apiKey: process.env.TWELVE_DATA_API_KEY,
      enabled: !!process.env.TWELVE_DATA_API_KEY,
      rateLimit: { callsPerMinute: 8, callsPerDay: 800 }
    }
  ];

  private static cache = new Map<string, { data: VIXDataPoint; expiry: number }>();
  private static rateLimitTracker = new Map<string, { calls: number; resetTime: number }>();

  /**
   * Get current VIX value from the best available free source
   * 
   * @param date Date to fetch VIX for (defaults to today)
   * @returns VIX data point or null if unavailable
   */
  static async getCurrentVIX(date: Date = new Date()): Promise<VIXDataPoint | null> {
    const cacheKey = `vix_${date.toDateString()}`;
    
    // Check cache first (cache for 1 hour)
    const cached = this.cache.get(cacheKey);
    if (cached && cached.expiry > Date.now()) {
      console.log(`📊 VIX from cache: ${cached.data.value.toFixed(2)} (${cached.data.source})`);
      return cached.data;
    }

    // Try providers in order of reliability and rate limits
    const enabledProviders = this.providers.filter(p => p.enabled);
    
    for (const provider of enabledProviders) {
      try {
        // Check rate limits
        if (!this.checkRateLimit(provider)) {
          console.log(`⏱️ Rate limit exceeded for ${provider.provider}, trying next provider`);
          continue;
        }

        const vixData = await this.fetchVIXFromProvider(provider, date);
        
        if (vixData) {
          // Cache the result
          this.cache.set(cacheKey, {
            data: vixData,
            expiry: Date.now() + 60 * 60 * 1000 // 1 hour cache
          });
          
          // Update rate limit tracker
          this.updateRateLimit(provider);
          
          console.log(`📊 VIX from ${provider.provider}: ${vixData.value.toFixed(2)}`);
          return vixData;
        }
      } catch (error) {
        console.warn(`⚠️ Failed to fetch VIX from ${provider.provider}:`, error instanceof Error ? error.message : String(error));
        continue;
      }
    }

    console.warn('⚠️ All VIX providers failed, no real VIX data available');
    return null;
  }

  /**
   * Get historical VIX data for backtesting
   * 
   * @param startDate Start date
   * @param endDate End date
   * @returns Array of VIX data points
   */
  static async getHistoricalVIX(startDate: Date, endDate: Date): Promise<VIXDataPoint[]> {
    console.log(`📈 Fetching historical VIX data from ${startDate.toDateString()} to ${endDate.toDateString()}`);
    
    // Try Yahoo Finance first (best for historical data)
    try {
      const yahooData = await this.fetchHistoricalVIXFromYahoo(startDate, endDate);
      if (yahooData.length > 0) {
        console.log(`✅ Retrieved ${yahooData.length} VIX data points from Yahoo Finance`);
        return yahooData;
      }
    } catch (error) {
      console.warn('⚠️ Yahoo Finance historical VIX failed:', error instanceof Error ? error.message : String(error));
    }

    // Try Alpha Vantage as backup
    const alphaVantageProvider = this.providers.find(p => p.provider === 'alphavantage' && p.enabled);
    if (alphaVantageProvider) {
      try {
        const alphaData = await this.fetchHistoricalVIXFromAlphaVantage(alphaVantageProvider, startDate, endDate);
        if (alphaData.length > 0) {
          console.log(`✅ Retrieved ${alphaData.length} VIX data points from Alpha Vantage`);
          return alphaData;
        }
      } catch (error) {
        console.warn('⚠️ Alpha Vantage historical VIX failed:', error instanceof Error ? error.message : String(error));
      }
    }

    // Try FRED as final backup
    const fredProvider = this.providers.find(p => p.provider === 'fred' && p.enabled);
    if (fredProvider) {
      try {
        const fredData = await this.fetchHistoricalVIXFromFRED(fredProvider, startDate, endDate);
        if (fredData.length > 0) {
          console.log(`✅ Retrieved ${fredData.length} VIX data points from FRED`);
          return fredData;
        }
      } catch (error) {
        console.warn('⚠️ FRED historical VIX failed:', error instanceof Error ? error.message : String(error));
      }
    }

    console.warn('⚠️ All historical VIX providers failed');
    return [];
  }

  /**
   * Fetch VIX from a specific provider
   */
  private static async fetchVIXFromProvider(provider: VIXProviderConfig, date: Date): Promise<VIXDataPoint | null> {
    switch (provider.provider) {
      case 'yahoo':
        return this.fetchVIXFromYahoo(date);
      case 'alphavantage':
        return this.fetchVIXFromAlphaVantage(provider, date);
      case 'fred':
        return this.fetchVIXFromFRED(provider, date);
      case 'polygon':
        return this.fetchVIXFromPolygon(provider, date);
      case 'twelvedata':
        return this.fetchVIXFromTwelveData(provider, date);
      default:
        throw new Error(`Unknown provider: ${provider.provider}`);
    }
  }

  /**
   * Yahoo Finance VIX (Most reliable, no API key needed)
   * Using the working Yahoo Query API endpoint
   */
  private static async fetchVIXFromYahoo(date: Date): Promise<VIXDataPoint | null> {
    // Use the working Yahoo Query API endpoint
    const url = 'https://query1.finance.yahoo.com/v8/finance/chart/^VIX';
    
    try {
      const response = await axios.get(url, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
          'Accept': 'application/json',
          'Referer': 'https://finance.yahoo.com/'
        },
        timeout: 15000
      });

      const data = response.data;
      const vixValue = data.chart?.result?.[0]?.meta?.regularMarketPrice;
      
      if (vixValue && !isNaN(vixValue) && vixValue > 5 && vixValue < 100) {
        console.log(`✅ Yahoo Finance VIX: ${vixValue.toFixed(2)}`);
        return {
          date,
          value: vixValue,
          source: 'Yahoo Finance',
          timestamp: new Date()
        };
      }
      
      // Fallback to CSV download method if Query API fails
      console.log('📡 Yahoo Query API returned invalid data, trying CSV fallback...');
      return await this.fetchVIXFromYahooCSV(date);
      
    } catch (error) {
      console.warn('⚠️ Yahoo Query API failed, trying CSV fallback...');
      return await this.fetchVIXFromYahooCSV(date);
    }
  }

  /**
   * Yahoo Finance CSV fallback method
   */
  private static async fetchVIXFromYahooCSV(date: Date): Promise<VIXDataPoint | null> {
    const symbol = '^VIX';
    const period1 = Math.floor(date.getTime() / 1000) - 86400; // 1 day before
    const period2 = Math.floor(date.getTime() / 1000) + 86400; // 1 day after
    
    const url = `https://query1.finance.yahoo.com/v7/finance/download/${symbol}?period1=${period1}&period2=${period2}&interval=1d&events=history`;
    
    try {
      const response = await axios.get(url, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        },
        timeout: 10000
      });

      const lines = response.data.split('\n');
      if (lines.length < 2) return null;

      // Parse CSV data (Date,Open,High,Low,Close,Adj Close,Volume)
      const dataLine = lines[1]; // Skip header
      const columns = dataLine.split(',');
      
      if (columns.length >= 5) {
        const vixValue = parseFloat(columns[4]); // Close price
        
        if (!isNaN(vixValue) && vixValue > 0) {
          console.log(`✅ Yahoo Finance CSV VIX: ${vixValue.toFixed(2)}`);
          return {
            date,
            value: vixValue,
            source: 'Yahoo Finance CSV',
            timestamp: new Date()
          };
        }
      }
    } catch (error) {
      throw new Error(`Yahoo Finance CSV API error: ${error instanceof Error ? error.message : String(error)}`);
    }

    return null;
  }

  /**
   * Alpha Vantage VIX (Free tier: 5 calls/minute, 500/day)
   */
  private static async fetchVIXFromAlphaVantage(provider: VIXProviderConfig, date: Date): Promise<VIXDataPoint | null> {
    if (!provider.apiKey) {
      throw new Error('Alpha Vantage API key required');
    }

    const url = `https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=VIX&apikey=${provider.apiKey}`;
    
    try {
      const response = await axios.get(url, { timeout: 10000 });
      const data = response.data;

      if (data['Global Quote'] && data['Global Quote']['05. price']) {
        const vixValue = parseFloat(data['Global Quote']['05. price']);
        
        if (!isNaN(vixValue) && vixValue > 0) {
          return {
            date,
            value: vixValue,
            source: 'Alpha Vantage',
            timestamp: new Date()
          };
        }
      }
    } catch (error) {
      throw new Error(`Alpha Vantage API error: ${error instanceof Error ? error.message : String(error)}`);
    }

    return null;
  }

  /**
   * FRED (Federal Reserve Economic Data) - Historical VIX
   */
  private static async fetchVIXFromFRED(provider: VIXProviderConfig, date: Date): Promise<VIXDataPoint | null> {
    if (!provider.apiKey) {
      throw new Error('FRED API key required');
    }

    const dateStr = date.toISOString().split('T')[0]; // YYYY-MM-DD
    const url = `https://api.stlouisfed.org/fred/series/observations?series_id=VIXCLS&api_key=${provider.apiKey}&file_type=json&observation_start=${dateStr}&observation_end=${dateStr}`;
    
    try {
      const response = await axios.get(url, { timeout: 10000 });
      const observations = response.data.observations;

      if (observations && observations.length > 0) {
        const latestObs = observations[observations.length - 1];
        const vixValue = parseFloat(latestObs.value);
        
        if (!isNaN(vixValue) && vixValue > 0) {
          return {
            date,
            value: vixValue,
            source: 'FRED',
            timestamp: new Date()
          };
        }
      }
    } catch (error) {
      throw new Error(`FRED API error: ${error instanceof Error ? error.message : String(error)}`);
    }

    return null;
  }

  /**
   * Polygon.io VIX (Primary provider with provided API key)
   * Following official Polygon.io REST API documentation
   * @see https://polygon.io/docs/rest/quickstart
   */
  private static async fetchVIXFromPolygon(provider: VIXProviderConfig, date: Date): Promise<VIXDataPoint | null> {
    if (!provider.apiKey) {
      throw new Error('Polygon API key required');
    }

    // Use proper Polygon.io endpoints as per their documentation
    const dateStr = date.toISOString().split('T')[0]; // YYYY-MM-DD format
    
    const endpoints = [
      {
        name: 'Aggregates (Recommended)',
        url: `https://api.polygon.io/v2/aggs/ticker/I:VIX/range/1/day/${dateStr}/${dateStr}`,
        params: { adjusted: 'true', sort: 'desc', apikey: provider.apiKey },
        parser: (data: any) => data.results?.[0]?.c // close price
      },
      {
        name: 'Previous Close',
        url: `https://api.polygon.io/v1/open-close/I:VIX/${dateStr}`,
        params: { adjusted: 'true', apikey: provider.apiKey },
        parser: (data: any) => data.status === 'OK' ? data.close : null
      },
      {
        name: 'Last Quote',
        url: `https://api.polygon.io/v2/last/nbbo/I:VIX`,
        params: { apikey: provider.apiKey },
        parser: (data: any) => data.results?.last_quote?.midpoint || data.results?.last_quote?.ask
      }
    ];
    
    // Try each endpoint following Polygon.io best practices
    for (const endpoint of endpoints) {
      try {
        console.log(`📊 Trying Polygon ${endpoint.name} endpoint...`);
        
        // Use proper authentication as per Polygon docs
        const response = await axios.get(endpoint.url, {
          params: endpoint.params,
          timeout: 15000,
          headers: {
            'User-Agent': 'Trading-System/1.0',
            'Accept': 'application/json',
            // Alternative: Use Authorization header instead of query param
            // 'Authorization': `Bearer ${provider.apiKey}`
          }
        });
        
        const data = response.data;
        
        // Check for API errors first
        if (data.status === 'ERROR') {
          console.warn(`⚠️ Polygon API error: ${data.error || 'Unknown error'}`);
          continue;
        }
        
        const vixValue = parseFloat(endpoint.parser(data));
        
        // Validate VIX value (typical range: 9-80)
        if (!isNaN(vixValue) && vixValue > 5 && vixValue < 100) {
          console.log(`✅ Polygon VIX data retrieved: ${vixValue.toFixed(2)} (${endpoint.name})`);
          return {
            date,
            value: vixValue,
            source: 'Polygon.io',
            timestamp: new Date()
          };
        } else {
          console.warn(`⚠️ Invalid VIX value from ${endpoint.name}: ${vixValue}`);
        }
        
      } catch (error: any) {
        console.warn(`⚠️ Polygon ${endpoint.name} failed:`, error instanceof Error ? error.message : String(error));
        
        // Log specific error details for debugging
        if (error.response) {
          const status = error.response.status;
          const statusText = error.response.statusText;
          console.warn(`   HTTP ${status}: ${statusText}`);
          
          if (status === 401) {
            console.warn('   🔑 Authentication failed - check API key');
          } else if (status === 403) {
            console.warn('   🚫 Access forbidden - check API key permissions or plan limits');
          } else if (status === 429) {
            console.warn('   ⏱️ Rate limit exceeded - waiting before next attempt');
          }
          
          // Log response body for debugging (first 200 chars)
          if (error.response.data) {
            const responseStr = JSON.stringify(error.response.data).substring(0, 200);
            console.warn(`   📄 Response: ${responseStr}...`);
          }
        }
        
        continue; // Try next endpoint
      }
    }

    throw new Error('All Polygon VIX endpoints failed - check API key and account status');
  }

  /**
   * Twelve Data VIX (Free tier: 800 calls/day)
   */
  private static async fetchVIXFromTwelveData(provider: VIXProviderConfig, date: Date): Promise<VIXDataPoint | null> {
    if (!provider.apiKey) {
      throw new Error('Twelve Data API key required');
    }

    const url = `https://api.twelvedata.com/quote?symbol=VIX&apikey=${provider.apiKey}`;
    
    try {
      const response = await axios.get(url, { timeout: 10000 });
      const data = response.data;

      if (data.close) {
        const vixValue = parseFloat(data.close);
        
        if (!isNaN(vixValue) && vixValue > 0) {
          return {
            date,
            value: vixValue,
            source: 'Twelve Data',
            timestamp: new Date()
          };
        }
      }
    } catch (error) {
      throw new Error(`Twelve Data API error: ${error instanceof Error ? error.message : String(error)}`);
    }

    return null;
  }

  /**
   * Fetch historical VIX from Yahoo Finance
   */
  private static async fetchHistoricalVIXFromYahoo(startDate: Date, endDate: Date): Promise<VIXDataPoint[]> {
    const symbol = '^VIX';
    const period1 = Math.floor(startDate.getTime() / 1000);
    const period2 = Math.floor(endDate.getTime() / 1000);
    
    const url = `https://query1.finance.yahoo.com/v7/finance/download/${symbol}?period1=${period1}&period2=${period2}&interval=1d&events=history`;
    
    const response = await axios.get(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      },
      timeout: 30000
    });

    const lines = response.data.split('\n');
    const vixData: VIXDataPoint[] = [];

    // Skip header line
    for (let i = 1; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;

      const columns = line.split(',');
      if (columns.length >= 5) {
        const dateStr = columns[0];
        const closePrice = parseFloat(columns[4]);
        
        if (!isNaN(closePrice) && closePrice > 0) {
          vixData.push({
            date: new Date(dateStr),
            value: closePrice,
            source: 'Yahoo Finance',
            timestamp: new Date()
          });
        }
      }
    }

    return vixData.sort((a, b) => a.date.getTime() - b.date.getTime());
  }

  /**
   * Fetch historical VIX from Alpha Vantage
   */
  private static async fetchHistoricalVIXFromAlphaVantage(provider: VIXProviderConfig, startDate: Date, endDate: Date): Promise<VIXDataPoint[]> {
    const url = `https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=VIX&apikey=${provider.apiKey}&outputsize=full`;
    
    const response = await axios.get(url, { timeout: 30000 });
    const timeSeries = response.data['Time Series (Daily)'];
    
    if (!timeSeries) {
      throw new Error('No time series data from Alpha Vantage');
    }

    const vixData: VIXDataPoint[] = [];
    const startTime = startDate.getTime();
    const endTime = endDate.getTime();

    for (const [dateStr, data] of Object.entries(timeSeries)) {
      const date = new Date(dateStr);
      const dateTime = date.getTime();
      
      if (dateTime >= startTime && dateTime <= endTime) {
        const closePrice = parseFloat((data as any)['4. close']);
        
        if (!isNaN(closePrice) && closePrice > 0) {
          vixData.push({
            date,
            value: closePrice,
            source: 'Alpha Vantage',
            timestamp: new Date()
          });
        }
      }
    }

    return vixData.sort((a, b) => a.date.getTime() - b.date.getTime());
  }

  /**
   * Fetch historical VIX from FRED
   */
  private static async fetchHistoricalVIXFromFRED(provider: VIXProviderConfig, startDate: Date, endDate: Date): Promise<VIXDataPoint[]> {
    const startStr = startDate.toISOString().split('T')[0];
    const endStr = endDate.toISOString().split('T')[0];
    
    const url = `https://api.stlouisfed.org/fred/series/observations?series_id=VIXCLS&api_key=${provider.apiKey}&file_type=json&observation_start=${startStr}&observation_end=${endStr}`;
    
    const response = await axios.get(url, { timeout: 30000 });
    const observations = response.data.observations;
    
    if (!observations) {
      throw new Error('No observations from FRED');
    }

    const vixData: VIXDataPoint[] = [];

    for (const obs of observations) {
      if (obs.value !== '.') { // FRED uses '.' for missing data
        const vixValue = parseFloat(obs.value);
        
        if (!isNaN(vixValue) && vixValue > 0) {
          vixData.push({
            date: new Date(obs.date),
            value: vixValue,
            source: 'FRED',
            timestamp: new Date()
          });
        }
      }
    }

    return vixData.sort((a, b) => a.date.getTime() - b.date.getTime());
  }

  /**
   * Check rate limits for a provider
   */
  private static checkRateLimit(provider: VIXProviderConfig): boolean {
    if (!provider.rateLimit) return true;

    const key = provider.provider;
    const tracker = this.rateLimitTracker.get(key);
    const now = Date.now();

    if (!tracker) {
      this.rateLimitTracker.set(key, { calls: 0, resetTime: now + 60000 }); // Reset every minute
      return true;
    }

    // Reset if time window expired
    if (now > tracker.resetTime) {
      tracker.calls = 0;
      tracker.resetTime = now + 60000;
    }

    return tracker.calls < provider.rateLimit.callsPerMinute;
  }

  /**
   * Update rate limit tracker
   */
  private static updateRateLimit(provider: VIXProviderConfig): void {
    const key = provider.provider;
    const tracker = this.rateLimitTracker.get(key);
    
    if (tracker) {
      tracker.calls++;
    }
  }

  /**
   * Get provider status and configuration info
   */
  static getProviderStatus(): Array<{ provider: string; enabled: boolean; requiresApiKey: boolean; rateLimit?: any }> {
    return this.providers.map(p => ({
      provider: p.provider,
      enabled: p.enabled,
      requiresApiKey: !!p.apiKey || p.provider !== 'yahoo',
      rateLimit: p.rateLimit
    }));
  }

  /**
   * Test all providers and return working ones
   */
  static async testAllProviders(): Promise<Array<{ provider: string; working: boolean; latency?: number; error?: string }>> {
    const results = [];
    const testDate = new Date();

    for (const provider of this.providers.filter(p => p.enabled)) {
      const startTime = Date.now();
      
      try {
        const vixData = await this.fetchVIXFromProvider(provider, testDate);
        const latency = Date.now() - startTime;
        
        results.push({
          provider: provider.provider,
          working: !!vixData,
          latency,
          error: vixData ? undefined : 'No data returned'
        });
      } catch (error) {
        results.push({
          provider: provider.provider,
          working: false,
          error: error instanceof Error ? error.message : String(error)
        });
      }
    }

    return results;
  }
}

/**
 * Environment setup helper
 */
export class VIXProviderSetup {
  /**
   * Generate .env template for VIX providers
   */
  static generateEnvTemplate(): string {
    return `
# Free VIX Data Provider API Keys
# ================================

# Alpha Vantage (Free: 5 calls/minute, 500/day)
# Get free key at: https://www.alphavantage.co/support/#api-key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here

# FRED (Federal Reserve) (Free: 120 calls/minute, 1000/day)
# Get free key at: https://fred.stlouisfed.org/docs/api/api_key.html
FRED_API_KEY=your_fred_key_here

# Polygon.io (Free: 5 calls/minute, 1000/day)
# Get free key at: https://polygon.io/
POLYGON_API_KEY=your_polygon_key_here

# Twelve Data (Free: 800 calls/day)
# Get free key at: https://twelvedata.com/
TWELVE_DATA_API_KEY=your_twelve_data_key_here

# Note: Yahoo Finance requires no API key and is the primary provider
`;
  }

  /**
   * Setup instructions
   */
  static getSetupInstructions(): string {
    return `
🌐 FREE VIX DATA SETUP INSTRUCTIONS
==================================

1. NO API KEY NEEDED (Primary):
   • Yahoo Finance - Works immediately, no setup required
   • Most reliable for both current and historical VIX data

2. OPTIONAL API KEYS (Backup providers):
   
   Alpha Vantage (Free):
   • Visit: https://www.alphavantage.co/support/#api-key
   • Sign up for free account
   • Get API key instantly
   • Limits: 5 calls/minute, 500/day
   
   FRED (Federal Reserve):
   • Visit: https://fred.stlouisfed.org/docs/api/api_key.html
   • Create free account
   • Request API key (instant approval)
   • Limits: 120 calls/minute, 1000/day
   
   Polygon.io (Free):
   • Visit: https://polygon.io/
   • Sign up for free tier
   • Get API key
   • Limits: 5 calls/minute, 1000/day
   
   Twelve Data (Free):
   • Visit: https://twelvedata.com/
   • Create free account
   • Get API key
   • Limits: 800 calls/day

3. SETUP:
   • Copy API keys to .env file
   • Restart application
   • Test providers with: FreeVIXDataProvider.testAllProviders()

4. USAGE PRIORITY:
   1. Yahoo Finance (no key needed)
   2. Alpha Vantage (if key available)
   3. FRED (if key available)
   4. Polygon.io (if key available)
   5. Twelve Data (if key available)
`;
  }
}

export default FreeVIXDataProvider;
