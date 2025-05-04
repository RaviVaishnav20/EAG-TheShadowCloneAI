document.addEventListener('DOMContentLoaded', function() {
    // API endpoints
    const API_ENDPOINTS = {
      ingestText: 'http://localhost:8000/ingest/text',
      ingestPdf: 'http://localhost:8000/ingest/pdf',
      ingestUrl: 'http://localhost:8000/ingest/url',
      search: 'http://localhost:8000/search',
      askNimo: 'http://localhost:8002/agent'
    };
  
    // Tab elements
    const saveTabBtn = document.getElementById('saveTabBtn');
    const searchTabBtn = document.getElementById('searchTabBtn');
    const askNimoTabBtn = document.getElementById('askNimoTabBtn');
    const saveTab = document.getElementById('saveTab');
    const searchTab = document.getElementById('searchTab');
    const askNimoTab = document.getElementById('askNimoTab');
  
    // Save tab elements
    const optionText = document.getElementById('optionText');
    const optionPdf = document.getElementById('optionPdf');
    const optionUrl = document.getElementById('optionUrl');
    const textInputSection = document.getElementById('textInputSection');
    const pdfInputSection = document.getElementById('pdfInputSection');
    const urlInputSection = document.getElementById('urlInputSection');
    const saveBtn = document.getElementById('saveBtn');
    const saveStatus = document.getElementById('saveStatus');
    const currentUrl = document.getElementById('currentUrl');
  
    // Search tab elements
    const searchBtn = document.getElementById('searchBtn');
    const searchQuery = document.getElementById('searchQuery');
    const resultCount = document.getElementById('resultCount');
    const searchStatus = document.getElementById('searchStatus');
    const searchResults = document.getElementById('searchResults');
    
    // Ask Nimo tab elements
    const askNimoBtn = document.getElementById('askNimoBtn');
    const nimoQuery = document.getElementById('nimoQuery');
    const nimoStatus = document.getElementById('nimoStatus');
    const nimoResults = document.getElementById('nimoResults');
  
    // Tab switching
    saveTabBtn.addEventListener('click', function() {
      setActiveTab(saveTabBtn, saveTab);
    });
  
    searchTabBtn.addEventListener('click', function() {
      setActiveTab(searchTabBtn, searchTab);
    });
    
    askNimoTabBtn.addEventListener('click', function() {
      setActiveTab(askNimoTabBtn, askNimoTab);
    });
  
    function setActiveTab(tabBtn, tabContent) {
      // Remove active class from all tabs
      document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
      
      // Add active class to selected tab
      tabBtn.classList.add('active');
      tabContent.classList.add('active');
    }
  
    // Get current tab URL
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
      if (tabs[0]) {
        currentUrl.textContent = tabs[0].url;
      }
    });
  
    // Toggle between save options
    optionText.addEventListener('change', updateSaveOption);
    optionPdf.addEventListener('change', updateSaveOption);
    optionUrl.addEventListener('change', updateSaveOption);
  
    function updateSaveOption() {
      textInputSection.classList.add('hidden');
      pdfInputSection.classList.add('hidden');
      urlInputSection.classList.add('hidden');
  
      if (optionText.checked) {
        textInputSection.classList.remove('hidden');
      } else if (optionPdf.checked) {
        pdfInputSection.classList.remove('hidden');
      } else if (optionUrl.checked) {
        urlInputSection.classList.remove('hidden');
      }
    }
  
    // Save button handler
    saveBtn.addEventListener('click', function() {
      clearStatus(saveStatus);
      
      if (optionText.checked) {
        saveText();
      } else if (optionPdf.checked) {
        savePdf();
      } else if (optionUrl.checked) {
        saveUrl();
      }
    });
  
    // Search button handler
    searchBtn.addEventListener('click', function() {
      performSearch();
    });
    
    // Ask Nimo button handler
    askNimoBtn.addEventListener('click', function() {
      askNimo();
    });
  
    // Enter key for search
    searchQuery.addEventListener('keypress', function(e) {
      if (e.key === 'Enter') {
        performSearch();
      }
    });
    
    // Enter key for Ask Nimo
    nimoQuery.addEventListener('keypress', function(e) {
      if (e.key === 'Enter') {
        askNimo();
      }
    });
  
    // Save text function
    function saveText() {
      const title = document.getElementById('textTitle').value;
      const content = document.getElementById('textContent').value;
  
      if (!content.trim()) {
        showStatus(saveStatus, 'Please enter some text content.', 'error');
        return;
      }
  
      showStatus(saveStatus, 'Saving text...', 'loading');
  
      fetch(API_ENDPOINTS.ingestText, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          content: content,
          title: title || 'Untitled Text Document',
          source_type: 'text'
        })
      })
      .then(response => response.json())
      .then(data => {
        showStatus(saveStatus, 'Text saved successfully!', 'success');
      })
      .catch(error => {
        showStatus(saveStatus, 'Error saving text: ' + error.message, 'error');
      });
    }
  
    // Save PDF function
    function savePdf() {
      const title = document.getElementById('pdfTitle').value;
      const pdfFile = document.getElementById('pdfFile').files[0];
  
      if (!pdfFile) {
        showStatus(saveStatus, 'Please select a PDF file.', 'error');
        return;
      }
  
      showStatus(saveStatus, 'Uploading PDF...', 'loading');
  
      const formData = new FormData();
      formData.append('pdf_file', pdfFile);
      
      if (title) {
        formData.append('title', title);
      }
  
      fetch(API_ENDPOINTS.ingestPdf, {
        method: 'POST',
        body: formData
      })
      .then(response => response.json())
      .then(data => {
        showStatus(saveStatus, 'PDF uploaded successfully!', 'success');
      })
      .catch(error => {
        showStatus(saveStatus, 'Error uploading PDF: ' + error.message, 'error');
      });
    }
  
    // Save URL function
    function saveUrl() {
      const title = document.getElementById('urlTitle').value;
      const url = currentUrl.textContent;
  
      if (!url || url === 'https://...') {
        showStatus(saveStatus, 'No URL available.', 'error');
        return;
      }
  
      showStatus(saveStatus, 'Saving current page...', 'loading');
  
      fetch(API_ENDPOINTS.ingestUrl, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          url: url,
          title: title || null
        })
      })
      .then(response => response.json())
      .then(data => {
        showStatus(saveStatus, 'Page saved successfully!', 'success');
      })
      .catch(error => {
        showStatus(saveStatus, 'Error saving page: ' + error.message, 'error');
      });
    }
  
    // Search function
    function performSearch() {
      const query = searchQuery.value;
      const top_k = parseInt(resultCount.value) || 5;
  
      if (!query.trim()) {
        showStatus(searchStatus, 'Please enter a search query.', 'error');
        return;
      }
  
      showStatus(searchStatus, 'Searching...', 'loading');
      searchResults.innerHTML = '';
  
      fetch(API_ENDPOINTS.search, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          query: query,
          top_k: top_k,
          include_context: true,
          min_score: 0.1
        })
      })
      .then(response => response.json())
      .then(data => {
        clearStatus(searchStatus);
        
        if (data.results.length === 0) {
          showStatus(searchStatus, 'No results found.', 'error');
          return;
        }
  
        // Display results
        data.results.forEach(result => {
          const resultElement = document.createElement('div');
          resultElement.className = 'result-item';
          
          const scorePercentage = Math.round(result.score * 100);
          
          resultElement.innerHTML = `
            <h3 class="result-title">${escapeHtml(result.title)}</h3>
            <div class="result-score">Relevance: ${scorePercentage}%</div>
            <div class="result-chunk">${escapeHtml(result.chunk)}</div>
            ${result.url ? `<div class="result-url"><a href="${result.url}" target="_blank">${result.url}</a></div>` : ''}
          `;
          
          searchResults.appendChild(resultElement);
        });
      })
      .catch(error => {
        showStatus(searchStatus, 'Error searching: ' + error.message, 'error');
      });
    }
    
    // Update only the askNimo function in popup.js

    function askNimo() {
      const query = nimoQuery.value;

      if (!query.trim()) {
        showStatus(nimoStatus, 'Please enter a question.', 'error');
        return;
      }

      showStatus(nimoStatus, 'Thinking...', 'loading');
      nimoResults.innerHTML = '';

      fetch(API_ENDPOINTS.askNimo, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          query: query,
          session_id: "user_1"  // Match the expected parameter in agent_api.py
        })
      })
      .then(response => {
        if (!response.ok) {
          throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
        }
        return response.json();
      })
      .then(data => {
        clearStatus(nimoStatus);
        
        // Check if we have a results string
        if (!data.results) {
          showStatus(nimoStatus, 'No response received.', 'error');
          return;
        }

        // Create response element with the string result
        const resultElement = document.createElement('div');
        resultElement.className = 'result-item';
        
        // Extract URLs if present in the response
        const urlMatch = data.results.match(/https?:\/\/[^\s"')<>]+/g);
        const urlHtml = urlMatch ? 
          `<div class="result-url"><strong>Source:</strong> <a href="${urlMatch[0]}" target="_blank">${escapeHtml(urlMatch[0])}</a></div>` : 
          '';
        
        resultElement.innerHTML = `
          <h3 class="result-title">Nimo's Response</h3>
          <div class="result-chunk">${formatNimoResponse(data.results)}</div>
          ${urlHtml}
        `;
        
        nimoResults.appendChild(resultElement);
      })
      .catch(error => {
        showStatus(nimoStatus, 'Error asking Nimo: ' + error.message, 'error');
        console.error('Nimo API error:', error);
      });
    }
            
        // Format Nimo response (converts newlines to <br> tags and preserves formatting)
        function formatNimoResponse(text) {
          if (!text) return '';
          
          // Replace newlines with <br> tags and preserve formatting
          return escapeHtml(text)
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Bold
            .replace(/\*(.*?)\*/g, '<em>$1</em>'); // Italic
    }
  
    // Helper functions
    function showStatus(element, message, type) {
      element.textContent = message;
      element.className = 'status ' + type;
    }
  
    function clearStatus(element) {
      element.textContent = '';
      element.className = 'status';
    }
  
    function escapeHtml(unsafe) {
      return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
    }
  });