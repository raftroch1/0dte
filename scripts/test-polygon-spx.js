#!/usr/bin/env node

/**
 * Test Polygon.io SPX Options Data Access
 * 
 * Tests if we can access SPX options data using the provided API key
 */

const https = require('https');

const POLYGON_API_KEY = 'DX1NqXJ3L0Ru3vzeldlZ0hUeq1JJfdfP';

async function testPolygonSPXAccess() {
    console.log('🔍 Testing Polygon.io SPX Options Data Access...\n');
    
    // Test 1: SPX Options Snapshot
    console.log('📊 Test 1: SPX Options Snapshot');
    try {
        const snapshotUrl = `https://api.polygon.io/v3/snapshot/options/I:SPX?apikey=${POLYGON_API_KEY}`;
        console.log(`🌐 URL: ${snapshotUrl}`);
        
        const snapshotData = await makeRequest(snapshotUrl);
        console.log('✅ SPX Options Snapshot Response:');
        console.log(JSON.stringify(snapshotData, null, 2));
        
    } catch (error) {
        console.error('❌ SPX Options Snapshot Error:', error.message);
    }
    
    console.log('\n' + '='.repeat(60) + '\n');
    
    // Test 2: SPX Options Contracts List
    console.log('📊 Test 2: SPX Options Contracts');
    try {
        const contractsUrl = `https://api.polygon.io/v3/reference/options/contracts?underlying_ticker=I:SPX&limit=10&apikey=${POLYGON_API_KEY}`;
        console.log(`🌐 URL: ${contractsUrl}`);
        
        const contractsData = await makeRequest(contractsUrl);
        console.log('✅ SPX Options Contracts Response:');
        console.log(JSON.stringify(contractsData, null, 2));
        
    } catch (error) {
        console.error('❌ SPX Options Contracts Error:', error.message);
    }
    
    console.log('\n' + '='.repeat(60) + '\n');
    
    // Test 3: Historical SPX Options Data
    console.log('📊 Test 3: Historical SPX Options Data');
    try {
        // Try to get historical data for a recent date
        const yesterday = new Date();
        yesterday.setDate(yesterday.getDate() - 1);
        const dateStr = yesterday.toISOString().split('T')[0];
        
        const historicalUrl = `https://api.polygon.io/v2/aggs/ticker/O:SPX240216C04600000/${dateStr}/${dateStr}?apikey=${POLYGON_API_KEY}`;
        console.log(`🌐 URL: ${historicalUrl}`);
        
        const historicalData = await makeRequest(historicalUrl);
        console.log('✅ Historical SPX Options Response:');
        console.log(JSON.stringify(historicalData, null, 2));
        
    } catch (error) {
        console.error('❌ Historical SPX Options Error:', error.message);
    }
}

function makeRequest(url) {
    return new Promise((resolve, reject) => {
        https.get(url, (res) => {
            let data = '';
            
            res.on('data', (chunk) => {
                data += chunk;
            });
            
            res.on('end', () => {
                try {
                    const jsonData = JSON.parse(data);
                    resolve(jsonData);
                } catch (error) {
                    reject(new Error(`JSON Parse Error: ${error.message}`));
                }
            });
            
        }).on('error', (error) => {
            reject(error);
        });
    });
}

// Run the test
testPolygonSPXAccess().catch(console.error);
