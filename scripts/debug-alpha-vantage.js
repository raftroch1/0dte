#!/usr/bin/env node

/**
 * 🔍 Alpha Vantage VIX Debug Script
 * =================================
 * 
 * Debug script to see exactly what Alpha Vantage returns for VIX data
 * and fix the parsing logic accordingly.
 */

const axios = require('axios');

async function debugAlphaVantageVIX() {
  console.log('🔍 Alpha Vantage VIX Debug Test');
  console.log('===============================\n');
  
  const apiKey = process.env.ALPHA_VANTAGE_API_KEY || 'XAZF4K40D1HMUEJK';
  console.log(`🔑 Using API Key: ${apiKey.substring(0, 8)}...`);
  
  try {
    const url = `https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=VIX&apikey=${apiKey}`;
    console.log(`📡 URL: ${url}`);
    
    const response = await axios.get(url, { 
      timeout: 15000,
      headers: {
        'User-Agent': 'Trading-System/1.0',
        'Accept': 'application/json'
      }
    });
    
    console.log('\n📄 Full Response:');
    console.log(JSON.stringify(response.data, null, 2));
    
    const data = response.data;
    
    // Check different possible structures
    console.log('\n🔍 Response Analysis:');
    console.log('Response keys:', Object.keys(data));
    
    if (data['Global Quote']) {
      console.log('\n📊 Global Quote structure:');
      console.log(JSON.stringify(data['Global Quote'], null, 2));
      
      const quote = data['Global Quote'];
      console.log('\n🔍 Global Quote keys:', Object.keys(quote));
      
      // Try different field names
      const possiblePriceFields = [
        '05. price',
        'price',
        'close',
        'latest_price',
        'current_price'
      ];
      
      console.log('\n💰 Looking for price fields:');
      possiblePriceFields.forEach(field => {
        if (quote[field]) {
          console.log(`   ✅ Found ${field}: ${quote[field]}`);
        } else {
          console.log(`   ❌ Missing ${field}`);
        }
      });
    }
    
    // Try alternative VIX symbols
    console.log('\n🔄 Trying alternative VIX symbol...');
    const altUrl = `https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=^VIX&apikey=${apiKey}`;
    
    const altResponse = await axios.get(altUrl, { 
      timeout: 15000,
      headers: {
        'User-Agent': 'Trading-System/1.0',
        'Accept': 'application/json'
      }
    });
    
    console.log('\n📄 Alternative Symbol (^VIX) Response:');
    console.log(JSON.stringify(altResponse.data, null, 2));
    
  } catch (error) {
    console.error('❌ Error:', error.message);
    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response data:', error.response.data);
    }
  }
}

// Run the debug
debugAlphaVantageVIX().catch(console.error);
