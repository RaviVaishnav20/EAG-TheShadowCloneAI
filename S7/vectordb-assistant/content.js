// Content script for VectorDB Assistant extension

// Listen for messages from background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'saveSelection') {
    saveSelectedText(message.text, message.url, message.title);
  } else if (message.action === 'saveCurrentPage') {
    saveCurrentPage(message.url, message.title);
  }
});

// Function to save selected text to VectorDB
function saveSelectedText(text, url, pageTitle) {
  if (!text || text.trim() === '') {
    showNotification('Error', 'No text selected.');
    return;
  }

  // Make a request to save the selected text
  fetch('http://localhost:8000/ingest/text', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      content: text,
      title: `Selection from: ${pageTitle}`,
      source_type: 'text'
    })
  })
  .then(response => {
    if (!response.ok) {
      throw new Error(`Server responded with ${response.status}`);
    }
    return response.json();
  })
  .then(data => {
    showNotification('Success', 'Selected text saved to VectorDB.');
  })
  .catch(error => {
    console.error('Error saving selection:', error);
    showNotification('Error', `Failed to save: ${error.message}`);
  });
}

// Function to save the current page to VectorDB
function saveCurrentPage(url, title) {
  if (!url) {
    showNotification('Error', 'No URL provided.');
    return;
  }

  showNotification('Processing', 'Saving current page...');

  // Make request to save the URL
  fetch('http://localhost:8000/ingest/url', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      url: url,
      title: title || document.title
    })
  })
  .then(response => {
    if (!response.ok) {
      throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
    }
    return response.json();
  })
  .then(data => {
    showNotification('Success', 'Current page saved to VectorDB.');
  })
  .catch(error => {
    console.error('Error saving page:', error);
    showNotification('Error', `Failed to save page: ${error.message}`);
  });
}

// Helper function to create and show a notification
function showNotification(title, message) {
  // Create notification element
  const notification = document.createElement('div');
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 15px 20px;
    background-color: ${title === 'Success' ? '#4CAF50' : title === 'Processing' ? '#2196F3' : '#F44336'};
    color: white;
    border-radius: 4px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    z-index: 9999;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    max-width: 300px;
    animation: slideIn 0.3s forwards;
  `;
  
  // Add content
  notification.innerHTML = `
    <div style="font-weight: bold; margin-bottom: 5px;">${title}</div>
    <div>${message}</div>
  `;
  
  // Add to page
  document.body.appendChild(notification);
  
  // Add animation style
  const style = document.createElement('style');
  style.textContent = `
    @keyframes slideIn {
      from { transform: translateX(100%); opacity: 0; }
      to { transform: translateX(0); opacity: 1; }
    }
    @keyframes fadeOut {
      from { opacity: 1; }
      to { opacity: 0; }
    }
  `;
  document.head.appendChild(style);
  
  // Remove after delay
  setTimeout(() => {
    notification.style.animation = 'fadeOut 0.5s forwards';
    setTimeout(() => {
      notification.remove();
    }, 500);
  }, 3000);
}

// Add a "Save Page" button to the top of the page
function addSavePageButton() {
  const button = document.createElement('button');
  button.textContent = 'Save to VectorDB';
  button.style.cssText = `
    position: fixed;
    top: 10px;
    right: 10px;
    padding: 8px 12px;
    background-color: #1a73e8;
    color: white;
    border: none;
    border-radius: 4px;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 14px;
    cursor: pointer;
    z-index: 9999;
    opacity: 0.8;
    transition: opacity 0.2s;
  `;
  
  button.addEventListener('mouseover', () => {
    button.style.opacity = '1';
  });
  
  button.addEventListener('mouseout', () => {
    button.style.opacity = '0.8';
  });
  
  button.addEventListener('click', () => {
    saveCurrentPage(window.location.href, document.title);
  });
  
  document.body.appendChild(button);
}