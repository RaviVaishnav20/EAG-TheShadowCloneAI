// Configuration
const CONFIG = {
  GEMINI_API_KEY: 'your_gemini_api_key', // Replace with your API key
  SEARCH_ENGINE_ID: 'your_search_engine_id', // Replace with your Search Engine ID
  PLATFORMS: {
    netflix: "site:netflix.com new tv series OR new anime OR new shows",
    prime: "site:primevideo.com new tv series OR new shows",
    crunchyroll: "site:crunchyroll.com new anime OR new series"
  }
};

document.addEventListener('DOMContentLoaded', function() {
  const platformSelect = document.getElementById('platformSelect');
  const seriesList = document.getElementById('seriesList');
  
  async function fetchLatestSeries(platform) {
    try {
      seriesList.innerHTML = '<div class="loading">Loading...</div>';
      
      let searchQuery = '';
      if (platform === 'all') {
        searchQuery = "new tv series OR new anime (site:netflix.com OR site:primevideo.com OR site:crunchyroll.com)";
      } else {
        searchQuery = CONFIG.PLATFORMS[platform];
      }

      const url = `https://www.googleapis.com/customsearch/v1?key=${CONFIG.GEMINI_API_KEY}&cx=${CONFIG.SEARCH_ENGINE_ID}&q=${encodeURIComponent(searchQuery)}&num=10&sort=date`;
      
      const response = await fetch(url);
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error?.message || 'Failed to fetch data');
      }

      return data.items.map(item => ({
        title: item.title,
        description: item.snippet,
        platform: detectPlatform(item.link),
        link: item.link,
        image: item.pagemap?.cse_image?.[0]?.src || null
      }));
    } catch (error) {
      console.error('Error fetching data:', error);
      return [];
    }
  }

  function detectPlatform(url) {
    if (url.includes('netflix.com')) return 'Netflix';
    if (url.includes('primevideo.com')) return 'Prime Video';
    if (url.includes('crunchyroll.com')) return 'Crunchyroll';
    return 'Unknown Platform';
  }

  function displaySeries(series) {
    seriesList.innerHTML = '';
    
    if (series.length === 0) {
      seriesList.innerHTML = '<div class="error">No series found or error occurred</div>';
      return;
    }
    
    series.forEach(show => {
      const seriesCard = document.createElement('div');
      seriesCard.className = 'series-card';
      
      const imageHtml = show.image ? 
        `<img src="${show.image}" alt="${show.title}" class="series-image">` : 
        `<div class="series-image" style="background: #edf2f7"></div>`;
      
      seriesCard.innerHTML = `
        ${imageHtml}
        <div class="series-content">
          <div class="series-title">
            <a href="${show.link}" target="_blank">${show.title}</a>
          </div>
          <div class="series-platform" data-platform="${show.platform}">${show.platform}</div>
          <div class="series-description">${show.description}</div>
        </div>
      `;
      
      seriesList.appendChild(seriesCard);
    });
  }

  // Event listener for platform selection
  platformSelect.addEventListener('change', async (e) => {
    const selectedPlatform = e.target.value;
    const series = await fetchLatestSeries(selectedPlatform);
    displaySeries(series);
  });

  // Initial load
  fetchLatestSeries('all').then(displaySeries);
}); 