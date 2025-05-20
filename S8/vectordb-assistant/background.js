// Background script for VectorDB Assistant extension

// Listen for installation
chrome.runtime.onInstalled.addListener(() => {
    console.log('VectorDB Assistant extension installed');
    
    // Set up context menu
    chrome.contextMenus.create({
      id: 'save-selection',
      title: 'Save selection to VectorDB',
      contexts: ['selection']
    });
  });
  
  // Handle context menu clicks
  chrome.contextMenus.onClicked.addListener((info, tab) => {
    if (info.menuItemId === 'save-selection' && info.selectionText) {
      // Send selected text to content script
      chrome.tabs.sendMessage(tab.id, {
        action: 'saveSelection',
        text: info.selectionText,
        url: tab.url,
        title: tab.title
      });
    }
  });
  
  // Listen for messages from content script or popup
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    // Handle any messages if needed
    if (message.action === 'checkApiStatus') {
      checkApiStatus()
        .then(status => {
          sendResponse(status);
        })
        .catch(error => {
          sendResponse({ available: false, error: error.message });
        });
      return true; // Indicates async response
    }
  });
  
  // Function to check if the API servers are running
  async function checkApiStatus() {
    try {
      // Try to check ingestion API
      let ingestStatus = { status: 'unknown' };
      let searchStatus = { status: 'unknown' };
      
      try {
        const ingestResponse = await fetch('http://localhost:8000/health', {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' }
        });
        ingestStatus = await ingestResponse.json();
      } catch (e) {
        console.error('Ingest API check failed:', e);
        ingestStatus = { status: 'error', message: e.message };
      }
      
      
      
      return {
        available: (ingestStatus.status !== 'error' || searchStatus.status !== 'error'),
        ingest: ingestStatus,
        search: searchStatus
      };
    } catch (error) {
      console.error('API check failed:', error);
      return {
        available: false,
        error: 'Could not connect to API servers. Make sure they are running.'
      };
    }
  }