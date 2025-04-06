require('dotenv').config();
// API endpoints
const GOLD_API_URL = 'https://www.goldapi.io/api/XAU/USD';
const EXCHANGE_API_URL = 'https://api.exchangerate-api.com/v4/latest/USD';

// Store your API keys securely
const GOLD_API_KEY = 'your_gold_api_key_here';
const EXCHANGE_API_KEY = 'your_exchange_api_key_here';

let previousData = {};

// Gold purity constants
const PURITY = {
    '24K': 1,
    '22K': 0.9167,
    '18K': 0.75
};

// Currency symbols
const CURRENCY_SYMBOLS = {
    INR: '₹',
    USD: '$',
    AED: 'AED'
};

// Format number with commas and decimals
function formatNumber(number, decimals = 2) {
    return new Intl.NumberFormat('en-IN', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(number);
}

// Format currency with symbol
function formatCurrency(amount, currency) {
    const formattedNumber = formatNumber(amount);
    const symbol = CURRENCY_SYMBOLS[currency] || '';
    return `${symbol}${formattedNumber}`;
}

// Get today's date in YYYY-MM-DD format
function getTodayDate() {
    return new Date().toISOString().split('T')[0];
}

// Get yesterday's date in YYYY-MM-DD format
function getYesterdayDate() {
    const date = new Date();
    date.setDate(date.getDate() - 1);
    return date.toISOString().split('T')[0];
}

async function fetchGoldPrice() {
    try {
        const response = await fetch(GOLD_API_URL, {
            headers: {
                'x-access-token': GOLD_API_KEY,
                'Content-Type': 'application/json'
            }
        });
        const data = await response.json();
        return data.price;
    } catch (error) {
        console.error('Error fetching gold price:', error);
        return null;
    }
}

async function fetchExchangeRates() {
    try {
        const response = await fetch(EXCHANGE_API_URL);
        const data = await response.json();
        return {
            usdToInr: data.rates.INR,
            aedToInr: data.rates.INR / data.rates.AED,
            usdToAed: data.rates.AED
        };
    } catch (error) {
        console.error('Error fetching exchange rates:', error);
        return null;
    }
}

function calculateChange(current, previous) {
    if (!previous) return { value: 0, isIncrease: true };
    const change = ((current - previous) / previous) * 100;
    return {
        value: Math.abs(change).toFixed(2),
        isIncrease: change >= 0
    };
}

function updateUI(elementId, value, change, absoluteChange = null) {
    const element = document.getElementById(elementId);
    if (!element) return;

    let changeHtml = '';
    if (change) {
        const changeClass = change.isIncrease ? 'increase' : 'decrease';
        const arrow = change.isIncrease ? '↑' : '↓';
        const absoluteChangeText = absoluteChange ? 
            ` (${change.isIncrease ? '+' : '-'}${formatCurrency(Math.abs(absoluteChange), value.split(' ')[0].replace(/[0-9,.]/g, ''))})` : '';
        changeHtml = `<span class="change ${changeClass}">${arrow} ${change.value}%${absoluteChangeText}</span>`;
    }

    element.innerHTML = `${value}${changeHtml}`;
}

function calculateGoldPrices(basePrice, exchangeRates) {
    const prices = {};
    Object.entries(PURITY).forEach(([karat, purity]) => {
        const pricePerGram = basePrice * purity / 31.1035; // Convert from troy ounce to gram
        prices[karat] = {
            inr: pricePerGram * exchangeRates.usdToInr,
            aed: pricePerGram * exchangeRates.usdToAed
        };
    });
    return prices;
}

async function updatePrices() {
    // Load previous data from storage
    chrome.storage.local.get(['dailyData'], async (result) => {
        const today = getTodayDate();
        const yesterday = getYesterdayDate();
        
        const dailyData = result.dailyData || {};
        const yesterdayData = dailyData[yesterday] || {};
        
        const [goldPrice, exchangeRates] = await Promise.all([
            fetchGoldPrice(),
            fetchExchangeRates()
        ]);

        if (goldPrice && exchangeRates) {
            // Calculate prices for different karats
            const goldPrices = calculateGoldPrices(goldPrice, exchangeRates);
            
            // Update UI for each karat
            Object.entries(goldPrices).forEach(([karat, prices]) => {
                const inrPrice = formatCurrency(prices.inr, 'INR') + '/g';
                const aedPrice = formatCurrency(prices.aed, 'AED') + '/g';
                
                // Calculate changes from yesterday
                const yesterdayInrPrice = yesterdayData[`${karat}_inr`];
                const yesterdayAedPrice = yesterdayData[`${karat}_aed`];
                
                const inrChange = calculateChange(prices.inr, yesterdayInrPrice);
                const aedChange = calculateChange(prices.aed, yesterdayAedPrice);
                
                // Calculate absolute price changes
                const inrAbsoluteChange = yesterdayInrPrice ? prices.inr - yesterdayInrPrice : null;
                const aedAbsoluteChange = yesterdayAedPrice ? prices.aed - yesterdayAedPrice : null;

                updateUI(`${karat.toLowerCase()}_inr`, inrPrice, inrChange, inrAbsoluteChange);
                updateUI(`${karat.toLowerCase()}_aed`, aedPrice, aedChange, aedAbsoluteChange);
            });

            // Update exchange rates
            updateUI('usdToInr', formatCurrency(exchangeRates.usdToInr, 'INR'), 
                calculateChange(exchangeRates.usdToInr, yesterdayData.usdToInr));
            updateUI('aedToInr', formatCurrency(exchangeRates.aedToInr, 'INR'), 
                calculateChange(exchangeRates.aedToInr, yesterdayData.aedToInr));

            // Update last updated time
            document.getElementById('lastUpdated').textContent = 
                `Last updated: ${new Date().toLocaleTimeString('en-US', { hour12: true })}`;

            // Store today's data
            const todayData = {
                usdToInr: exchangeRates.usdToInr,
                aedToInr: exchangeRates.aedToInr,
                timestamp: new Date().getTime()
            };

            // Store prices for each karat
            Object.entries(goldPrices).forEach(([karat, prices]) => {
                todayData[`${karat}_inr`] = prices.inr;
                todayData[`${karat}_aed`] = prices.aed;
            });

            // Update storage with daily data
            dailyData[today] = todayData;
            
            // Keep only last 7 days of data
            const dates = Object.keys(dailyData).sort();
            while (dates.length > 7) {
                delete dailyData[dates.shift()];
            }

            chrome.storage.local.set({ dailyData });
        }
    });
}

// Update prices when popup opens
document.addEventListener('DOMContentLoaded', updatePrices);

// Add auto-refresh every 5 minutes
setInterval(updatePrices, 300000); 