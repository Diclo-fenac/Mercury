import { SearchAPI } from './api.js';
import { SearchUI } from './ui.js';

class MercurySearch {
  static init() {
    const scripts = document.getElementsByTagName('script');
    let config = null;
    let targetScript = null;

    // Find the script tag that loaded us to extract data attributes
    for (let i = 0; i < scripts.length; i++) {
      if (scripts[i].src.includes('mercury-search.min.js')) {
        targetScript = scripts[i];
        config = {
          apiKey: scripts[i].getAttribute('data-api-key'),
          endpoint: scripts[i].getAttribute('data-endpoint') || 'http://localhost:8000'
        };
        break;
      }
    }

    if (!config || !config.apiKey) {
      console.error('[Mercury] Initialization failed. Missing data-api-key on script tag.');
      return;
    }

    // Create mount point right after the script tag
    const mountNode = document.createElement('div');
    targetScript.parentNode.insertBefore(mountNode, targetScript.nextSibling);

    const api = new SearchAPI(config.endpoint, config.apiKey);
    const ui = new SearchUI(mountNode, api);
    
    // Fetch and apply theme config
    api.getConfig().then(cfg => {
      if (cfg) ui.applyTheme(cfg);
    });
    
    console.log('[Mercury] Search widget initialized.');
  }
}

// Auto-initialize when loaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', MercurySearch.init);
} else {
  MercurySearch.init();
}
