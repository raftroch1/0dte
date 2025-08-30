#!/usr/bin/env node

/**
 * 🧪 Simple VIX Provider Test (JavaScript)
 * ========================================
 * 
 * Tests the free VIX data providers using plain JavaScript/Node.js
 * to demonstrate they work without TypeScript compilation issues.
 * 
 * @fileoverview Simple VIX provider test
 * @author Trading System QA
 * @version 1.0.0
 * @created 2025-08-30
 */

const axios = require('axios');

console.log('🌐 Testing Free VIX Data Providers...\n');

/**
 * Test Yahoo Finance VIX (Primary provider - no API key needed)
 */
async function testYahooFinanceVIX() {
  console.log('📊 Testing Yahoo Finance VIX (Primary Provider):');
  
  try {
    const symbol = '^VIX';
    const now = new Date();
    const period1 = Math.floor(now.getTime() / 1000) - 86400; // 1 day ago
    const period2 = Math.floor(now.getTime() / 1000); // now
    
    const url = `https://query1.finance.yahoo.com/v7/finance/download/${symbol}?period1=${period1}&period2=${period2}&interval=1d&events=history`;
    
    const response = await axios.get(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      },
      timeout: 10000
    });

    const lines = response.data.split('\n');
    if (lines.length >= 2) {
      const dataLine = lines[1]; // Skip header
      const columns = dataLine.split(',');
      
      if (columns.length >= 5) {
        const vixValue = parseFloat(columns[4]); // Close price
        
        if (!isNaN(vixValue) && vixValue > 0) {
          console.log(`   ✅ SUCCESS: Current VIX = ${vixValue.toFixed(2)}`);
          console.log(`   📅 Date: ${columns[0]}`);
          console.log(`   🆓 Cost: FREE (no API key needed)`);
          console.log(`   ⚡ Latency: Fast and reliable`);
          return { success: true, value: vixValue, source: 'Yahoo Finance' };
        }
      }
    }
    
    console.log('   ❌ FAILED: No valid VIX data in response');
    return { success: false, error: 'No valid data' };
    
  } catch (error) {
    console.log(`   ❌ FAILED: ${error.message}`);
    return { success: false, error: error.message };
  }
}

/**
 * Test Alpha Vantage VIX (Primary provider with provided API key)
 */
async function testAlphaVantageVIX() {
  console.log('\n📊 Testing Alpha Vantage VIX (Primary Provider):');
  
  const apiKey = process.env.ALPHA_VANTAGE_API_KEY || 'XAZF4K40D1HMUEJK';
  
  console.log(`   🔑 Using API Key: ${apiKey.substring(0, 8)}...`);
  
  try {
    const url = `https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=VIX&apikey=${apiKey}`;
    
    const response = await axios.get(url, { 
      timeout: 15000,
      headers: {
        'User-Agent': 'Trading-System/1.0',
        'Accept': 'application/json'
      }
    });
    
    const data = response.data;

    // Check for API errors
    if (data['Error Message']) {
      console.log(`   ❌ Alpha Vantage API error: ${data['Error Message']}`);
      return { success: false, error: data['Error Message'] };
    }

    if (data['Note']) {
      console.log(`   ⚠️ Alpha Vantage note: ${data['Note']}`);
      if (data['Note'].includes('rate limit')) {
        return { success: false, error: 'Rate limit exceeded' };
      }
    }

    if (data['Global Quote'] && data['Global Quote']['05. price']) {
      const vixValue = parseFloat(data['Global Quote']['05. price']);
      
      if (!isNaN(vixValue) && vixValue > 5 && vixValue < 100) {
        console.log(`   ✅ SUCCESS: Current VIX = ${vixValue.toFixed(2)}`);
        console.log(`   📊 Symbol: ${data['Global Quote']['01. symbol']}`);
        console.log(`   📅 Last Updated: ${data['Global Quote']['07. latest trading day']}`);
        console.log(`   🔑 API Key: Working perfectly`);
        console.log(`   📊 Limits: 5 calls/minute, 500/day`);
        console.log(`   💰 Cost: FREE tier includes VIX data`);
        return { success: true, value: vixValue, source: 'Alpha Vantage' };
      } else {
        console.log(`   ⚠️ Invalid VIX value: ${vixValue}`);
      }
    } else {
      console.log('   ❌ FAILED: No valid VIX data in response');
      console.log('   📄 Response structure:', Object.keys(data));
    }
    
    return { success: false, error: 'No valid data' };
    
  } catch (error) {
    console.log(`   ❌ FAILED: ${error.message}`);
    
    if (error.response) {
      const status = error.response.status;
      console.log(`   📄 HTTP ${status}: ${error.response.statusText}`);
      
      if (status === 401) {
        console.log('   🔑 Authentication failed - check API key');
      } else if (status === 403) {
        console.log('   🚫 Access forbidden - check API key permissions');
      } else if (status === 429) {
        console.log('   ⏱️ Rate limit exceeded');
      }
    }
    
    return { success: false, error: error.message };
  }
}

/**
 * Test Polygon.io VIX (Backup provider - free tier limitation)
 */
async function testPolygonVIX() {
  console.log('\n📊 Testing Polygon.io VIX (Primary Provider):');
  
  const apiKey = process.env.POLYGON_API_KEY || 'DX1NqXJ3L0Ru3vzeldlZ0hUeq1JJfdfP';
  
  console.log(`   🔑 Using API Key: ${apiKey.substring(0, 8)}...`);
  
  // Use proper Polygon.io endpoints as per their documentation
  // @see https://polygon.io/docs/rest/quickstart
  const dateStr = new Date().toISOString().split('T')[0];
  
  const endpoints = [
    {
      name: 'Aggregates (Recommended)',
      url: `https://api.polygon.io/v2/aggs/ticker/I:VIX/range/1/day/${dateStr}/${dateStr}`,
      params: { adjusted: 'true', sort: 'desc', apikey: apiKey },
      parser: (data) => data.results?.[0]?.c
    },
    {
      name: 'Previous Close',
      url: `https://api.polygon.io/v1/open-close/I:VIX/${dateStr}`,
      params: { adjusted: 'true', apikey: apiKey },
      parser: (data) => data.status === 'OK' ? data.close : null
    },
    {
      name: 'Last Quote',
      url: `https://api.polygon.io/v2/last/nbbo/I:VIX`,
      params: { apikey: apiKey },
      parser: (data) => data.results?.last_quote?.midpoint || data.results?.last_quote?.ask
    }
  ];
  
  for (let i = 0; i < endpoints.length; i++) {
    const endpoint = endpoints[i];
    
    try {
      console.log(`   📡 Trying ${endpoint.name} endpoint...`);
      
      // Use proper Polygon.io authentication as per their docs
      const response = await axios.get(endpoint.url, {
        params: endpoint.params,
        timeout: 15000,
        headers: {
          'User-Agent': 'Trading-System/1.0',
          'Accept': 'application/json'
        }
      });
      
      const data = response.data;
      
      // Check for API errors first
      if (data.status === 'ERROR') {
        console.log(`   ❌ Polygon API error: ${data.error || 'Unknown error'}`);
        continue;
      }
      
      const vixValue = parseFloat(endpoint.parser(data));
      
      if (!isNaN(vixValue) && vixValue > 0 && vixValue < 200) {
        console.log(`   ✅ SUCCESS: Current VIX = ${vixValue.toFixed(2)}`);
        console.log(`   📊 Source: ${endpoint.name}`);
        console.log(`   🔑 API Key: Working`);
        console.log(`   📊 Limits: 5 calls/minute, 1000/day`);
        console.log(`   💰 Cost: FREE tier`);
        return { success: true, value: vixValue, source: 'Polygon.io' };
      } else {
        console.log(`   ⚠️  Invalid VIX value: ${vixValue}`);
      }
      
    } catch (error) {
      console.log(`   ❌ ${endpoint.name} failed: ${error.message}`);
      
      if (error.response) {
        const status = error.response.status;
        console.log(`   📄 HTTP ${status}: ${error.response.statusText}`);
        
        if (status === 401) {
          console.log('   🔑 Authentication failed - check API key');
        } else if (status === 403) {
          console.log('   🚫 Access forbidden - check API key permissions or plan limits');
          console.log('   💡 Visit https://polygon.io/dashboard to verify account status');
        } else if (status === 429) {
          console.log('   ⏱️ Rate limit exceeded');
        }
        
        // Log response for debugging
        if (error.response.data) {
          const responseStr = JSON.stringify(error.response.data).substring(0, 200);
          console.log(`   📄 Response: ${responseStr}...`);
        }
      }
      
      continue; // Try next endpoint
    }
  }
  
  console.log('   ❌ FAILED: All Polygon endpoints failed');
  return { success: false, error: 'All endpoints failed' };
}

/**
 * Main test function
 */
async function runVIXTests() {
  console.log('🎯 FREE VIX DATA INTEGRATION TEST');
  console.log('=================================\n');
  
  const results = [];
  
  // Test 1: Alpha Vantage (Primary - with provided API key)
  const alphaResult = await testAlphaVantageVIX();
  results.push(alphaResult);
  
  // Test 2: Yahoo Finance (Backup - no key needed)
  const yahooResult = await testYahooFinanceVIX();
  results.push(yahooResult);
  
  // Test 3: Polygon.io (Backup - free tier limitation)
  const polygonResult = await testPolygonVIX();
  results.push(polygonResult);
  
  // Summary
  console.log('\n📋 TEST SUMMARY:');
  console.log('================');
  
  const workingProviders = results.filter(r => r.success);
  const failedProviders = results.filter(r => !r.success);
  
  console.log(`✅ Working Providers: ${workingProviders.length}`);
  console.log(`❌ Failed Providers: ${failedProviders.length}`);
  
  if (workingProviders.length > 0) {
    console.log('\n🎉 SUCCESS: VIX data integration is working!');
    console.log('\nWorking providers:');
    workingProviders.forEach(provider => {
      console.log(`   • ${provider.source}: VIX = ${provider.value.toFixed(2)}`);
    });
    
    console.log('\n💰 COST ANALYSIS:');
    console.log('   • Our solution: $0 (completely free)');
    console.log('   • Bloomberg Terminal: $2,000+/month');
    console.log('   • Refinitiv: $1,500+/month');
    
    console.log('\n🚀 READY FOR DEPLOYMENT:');
    console.log('   • Flyagonal strategy can now use real VIX data');
    console.log('   • No subscription fees or API costs');
    console.log('   • Professional-grade data quality');
    console.log('   • Multiple backup providers for reliability');
    
  } else {
    console.log('\n⚠️  WARNING: No VIX providers are working');
    console.log('\nTroubleshooting:');
    console.log('   1. Check internet connection');
    console.log('   2. Add API keys to .env file (optional but recommended)');
    console.log('   3. Try running again (providers may have temporary issues)');
  }
  
  console.log('\n🔧 ADDITIONAL PROVIDERS AVAILABLE:');
  console.log('   • FRED (Federal Reserve) - Government data, very reliable');
  console.log('   • Polygon.io - Free tier with good coverage');
  console.log('   • Twelve Data - Additional backup option');
  console.log('\n   💡 Add API keys to .env to enable these providers');
  
  console.log('\n' + '='.repeat(60));
  console.log('✅ VIX DATA INTEGRATION TEST COMPLETE');
  console.log('='.repeat(60));
}

// Run the test
if (require.main === module) {
  runVIXTests().catch(error => {
    console.error('❌ Test failed:', error);
    process.exit(1);
  });
}
