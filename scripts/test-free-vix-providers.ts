#!/usr/bin/env ts-node

/**
 * 🧪 Free VIX Providers Test Script
 * =================================
 * 
 * Tests all free VIX data providers to ensure they work correctly.
 * Helps verify which providers are available and working.
 * 
 * @fileoverview Test script for free VIX data providers
 * @author Trading System QA
 * @version 1.0.0
 * @created 2025-08-30
 */

import { FreeVIXDataProvider, VIXProviderSetup } from '../src/data/free-vix-providers';

/**
 * Main test function
 */
async function testFreeVIXProviders(): Promise<void> {
  console.log('🧪 Testing Free VIX Data Providers...\n');

  try {
    // Test 1: Show provider status
    console.log('📋 Provider Status:');
    const providerStatus = FreeVIXDataProvider.getProviderStatus();
    
    providerStatus.forEach(provider => {
      const status = provider.enabled ? '✅ Enabled' : '❌ Disabled';
      const apiKey = provider.requiresApiKey ? '🔑 Requires API Key' : '🆓 No API Key';
      const rateLimit = provider.rateLimit ? 
        `📊 ${provider.rateLimit.callsPerMinute}/min, ${provider.rateLimit.callsPerDay}/day` : 
        '📊 No limits';
      
      console.log(`   ${provider.provider}: ${status} | ${apiKey} | ${rateLimit}`);
    });

    // Test 2: Test all providers
    console.log('\n🔍 Testing All Providers:');
    const testResults = await FreeVIXDataProvider.testAllProviders();
    
    let workingProviders = 0;
    testResults.forEach(result => {
      const status = result.working ? '✅ Working' : '❌ Failed';
      const latency = result.latency ? `⏱️ ${result.latency}ms` : '';
      const error = result.error ? `❌ ${result.error}` : '';
      
      console.log(`   ${result.provider}: ${status} ${latency} ${error}`);
      
      if (result.working) workingProviders++;
    });

    console.log(`\n📊 Summary: ${workingProviders}/${testResults.length} providers working`);

    // Test 3: Get current VIX
    console.log('\n📈 Testing Current VIX Fetch:');
    try {
      const currentVIX = await FreeVIXDataProvider.getCurrentVIX();
      
      if (currentVIX) {
        console.log(`   ✅ Current VIX: ${currentVIX.value.toFixed(2)}`);
        console.log(`   📊 Source: ${currentVIX.source}`);
        console.log(`   📅 Date: ${currentVIX.date.toDateString()}`);
        console.log(`   ⏰ Fetched: ${currentVIX.timestamp.toLocaleTimeString()}`);
      } else {
        console.log('   ❌ No current VIX data available');
      }
    } catch (error) {
      console.log(`   ❌ Current VIX fetch failed: ${error.message}`);
    }

    // Test 4: Get historical VIX (last 5 days)
    console.log('\n📊 Testing Historical VIX Fetch (Last 5 Days):');
    try {
      const endDate = new Date();
      const startDate = new Date(endDate.getTime() - 5 * 24 * 60 * 60 * 1000); // 5 days ago
      
      const historicalVIX = await FreeVIXDataProvider.getHistoricalVIX(startDate, endDate);
      
      if (historicalVIX.length > 0) {
        console.log(`   ✅ Retrieved ${historicalVIX.length} historical VIX data points:`);
        
        // Show last 3 data points
        const recentData = historicalVIX.slice(-3);
        recentData.forEach(point => {
          console.log(`      ${point.date.toDateString()}: ${point.value.toFixed(2)} (${point.source})`);
        });
        
        // Calculate some basic stats
        const values = historicalVIX.map(p => p.value);
        const avgVIX = values.reduce((sum, val) => sum + val, 0) / values.length;
        const minVIX = Math.min(...values);
        const maxVIX = Math.max(...values);
        
        console.log(`   📊 Stats: Avg=${avgVIX.toFixed(2)}, Min=${minVIX.toFixed(2)}, Max=${maxVIX.toFixed(2)}`);
      } else {
        console.log('   ❌ No historical VIX data available');
      }
    } catch (error) {
      console.log(`   ❌ Historical VIX fetch failed: ${error.message}`);
    }

    // Test 5: Performance test
    console.log('\n⚡ Performance Test (3 consecutive calls):');
    const performanceResults = [];
    
    for (let i = 1; i <= 3; i++) {
      const startTime = Date.now();
      try {
        const vixData = await FreeVIXDataProvider.getCurrentVIX();
        const latency = Date.now() - startTime;
        
        if (vixData) {
          performanceResults.push(latency);
          console.log(`   Call ${i}: ✅ ${vixData.value.toFixed(2)} in ${latency}ms (${vixData.source})`);
        } else {
          console.log(`   Call ${i}: ❌ No data in ${latency}ms`);
        }
      } catch (error) {
        const latency = Date.now() - startTime;
        console.log(`   Call ${i}: ❌ Error in ${latency}ms - ${error.message}`);
      }
      
      // Small delay between calls to respect rate limits
      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    if (performanceResults.length > 0) {
      const avgLatency = performanceResults.reduce((sum, lat) => sum + lat, 0) / performanceResults.length;
      console.log(`   📊 Average latency: ${avgLatency.toFixed(0)}ms`);
    }

    // Show setup instructions if no providers are working
    if (workingProviders === 0) {
      console.log('\n⚠️ No VIX providers are working. Setup instructions:');
      console.log(VIXProviderSetup.getSetupInstructions());
      
      console.log('\n📝 .env Template:');
      console.log(VIXProviderSetup.generateEnvTemplate());
    } else {
      console.log('\n✅ VIX data integration is working!');
      
      if (workingProviders < testResults.length) {
        console.log('\n💡 To enable more providers, add API keys to .env:');
        const disabledProviders = providerStatus.filter(p => !p.enabled && p.requiresApiKey);
        disabledProviders.forEach(provider => {
          console.log(`   ${provider.provider.toUpperCase()}_API_KEY=your_key_here`);
        });
      }
    }

    console.log('\n🎯 Test Complete!');

  } catch (error) {
    console.error('❌ Test failed:', error);
    process.exit(1);
  }
}

/**
 * Run test with command line options
 */
async function main(): Promise<void> {
  const args = process.argv.slice(2);
  
  if (args.includes('--help') || args.includes('-h')) {
    console.log(`
🧪 Free VIX Providers Test Script
=================================

Usage: npm run test:vix [options]

Options:
  --help, -h     Show this help message
  --setup        Show setup instructions only
  --env          Generate .env template

Examples:
  npm run test:vix                    # Run full test
  npm run test:vix --setup           # Show setup instructions
  npm run test:vix --env             # Generate .env template
`);
    return;
  }

  if (args.includes('--setup')) {
    console.log(VIXProviderSetup.getSetupInstructions());
    return;
  }

  if (args.includes('--env')) {
    console.log(VIXProviderSetup.generateEnvTemplate());
    return;
  }

  await testFreeVIXProviders();
}

// Run if called directly
if (require.main === module) {
  main().catch(error => {
    console.error('❌ Test script failed:', error);
    process.exit(1);
  });
}

export { testFreeVIXProviders };
