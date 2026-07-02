import css from './styles.css';

export class SearchUI {
  constructor(container, api) {
    this.api = api;
    this.shadowRoot = container.attachShadow({ mode: 'open' });
    this.elements = {};
    this.state = {
      query: '',
      results: [],
      selectedIndex: -1,
      isLoading: false
    };
    
    this.sessionId = Math.random().toString(36).substring(7);
    this.chatHistoryEl = null;
    
    this.initDOM();
    this.bindEvents();
  }

  initDOM() {
    // Inject Styles
    const style = document.createElement('style');
    style.textContent = css;
    this.shadowRoot.appendChild(style);

    // Create Container
    const wrapper = document.createElement('div');
    wrapper.className = 'mercury-search-container';
    
    // Create Input
    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'mercury-input';
    input.placeholder = 'Search products...';
    input.setAttribute('autocomplete', 'off');
    
    // Create AI Toggle Button
    const aiToggle = document.createElement('button');
    aiToggle.className = 'mercury-ai-toggle';
    aiToggle.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
      </svg>
    `;
    aiToggle.title = "Ask AI Assistant";
    aiToggle.style.display = 'none'; // Hidden by default
    
    // Create Dropdown
    const dropdown = document.createElement('div');
    dropdown.className = 'mercury-dropdown';
    
    // Create Modal Overlay
    const overlay = document.createElement('div');
    overlay.className = 'mercury-modal-overlay';
    overlay.innerHTML = `
      <div class="mercury-modal">
        <div class="mercury-modal-header">
          <h2 class="mercury-modal-title">Search Results</h2>
          <button class="mercury-modal-close">&times;</button>
        </div>
        <div class="mercury-modal-body">
          <div class="mercury-grid"></div>
        </div>
      </div>
    `;
    
    wrapper.appendChild(input);
    wrapper.appendChild(aiToggle);
    wrapper.appendChild(dropdown);
    this.shadowRoot.appendChild(wrapper);
    this.shadowRoot.appendChild(overlay);
    
    this.elements = { input, dropdown, overlay, aiToggle };
  }

  applyTheme(config) {
    if (!config) return;
    const overrides = [];
    
    if (config.primary_color) {
      overrides.push(`--mercury-primary: ${config.primary_color};`);
    }
    if (config.font_family) {
      overrides.push(`--mercury-font: ${config.font_family};`);
    }
    
    if (config.mode === 'full') {
      this.elements.aiToggle.style.display = 'flex';
    }
    
    if (overrides.length > 0) {
      const customStyle = document.createElement('style');
      customStyle.textContent = `:host { ${overrides.join(' ')} }`;
      this.shadowRoot.appendChild(customStyle);
    }
  }

  debounce(func, wait) {
    let timeout;
    return (...args) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => func.apply(this, args), wait);
    };
  }

  bindEvents() {
    const { input, overlay } = this.elements;
    
    const debouncedSearch = this.debounce((q) => this.performSearch(q), 150);
    
    input.addEventListener('input', (e) => {
      const val = e.target.value.trim();
      if (val !== this.state.query) {
        this.state.query = val;
        this.state.selectedIndex = -1;
        debouncedSearch(val);
      }
    });

    input.addEventListener('keydown', (e) => this.handleKeydown(e));
    
    // Close on click outside
    document.addEventListener('click', (e) => {
      if (!this.shadowRoot.host.contains(e.target)) {
        this.closeDropdown();
      }
    });
    
    input.addEventListener('focus', () => {
      if (this.state.query.length > 0) this.openDropdown();
    });
    
    // Modal events
    const closeBtn = overlay.querySelector('.mercury-modal-close');
    closeBtn.addEventListener('click', () => this.closeModal());
    
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) this.closeModal();
    });
    
    // AI Toggle Event
    this.elements.aiToggle.addEventListener('click', (e) => {
      e.preventDefault();
      this.openChatModal();
    });
  }
  
  async performSearch(query) {
    if (!query) {
      this.closeDropdown();
      return;
    }
    
    this.state.isLoading = true;
    this.renderDropdown();
    this.openDropdown();
    
    const res = await this.api.search(query);
    this.state.isLoading = false;
    this.state.results = res.results || [];
    this.state.selectedIndex = -1;
    
    this.renderDropdown();
  }

  handleKeydown(e) {
    const { results, selectedIndex } = this.state;
    const max = results.length > 0 ? results.length : -1;
    
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        if (max >= 0) {
          this.state.selectedIndex = selectedIndex < max ? selectedIndex + 1 : 0;
          this.updateSelection();
        }
        break;
      case 'ArrowUp':
        e.preventDefault();
        if (max >= 0) {
          this.state.selectedIndex = selectedIndex > 0 ? selectedIndex - 1 : max;
          this.updateSelection();
        }
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && selectedIndex < results.length) {
          this.selectResult(results[selectedIndex]);
        } else if (selectedIndex === results.length) {
          this.openModal();
        }
        break;
      case 'Escape':
        e.preventDefault();
        this.closeDropdown();
        this.elements.input.blur();
        break;
    }
  }

  updateSelection() {
    const items = this.elements.dropdown.querySelectorAll('.mercury-result-item, .mercury-view-all');
    items.forEach((el, i) => {
      if (i === this.state.selectedIndex) {
        el.classList.add('selected');
        el.scrollIntoView({ block: 'nearest' });
      } else {
        el.classList.remove('selected');
      }
    });
  }

  selectResult(result) {
    // In a real app, this would navigate to the product URL or trigger a callback.
    console.log('[Mercury] Selected:', result);
    this.elements.input.value = result.title || result.name;
    this.closeDropdown();
  }

  openDropdown() {
    this.elements.dropdown.classList.add('active');
  }

  closeDropdown() {
    this.elements.dropdown.classList.remove('active');
  }
  
  async openModal() {
    this.closeDropdown();
    const { overlay } = this.elements;
    const grid = overlay.querySelector('.mercury-grid');
    const title = overlay.querySelector('.mercury-modal-title');
    
    title.textContent = `Results for "${this.state.query}"`;
    grid.innerHTML = '<div class="mercury-loading">Loading all results...</div>';
    overlay.classList.add('active');
    
    // Fetch larger result set
    const res = await this.api.search(this.state.query, 20);
    
    if (!res.results || res.results.length === 0) {
      grid.innerHTML = '<div class="mercury-empty">No results found.</div>';
      return;
    }
    
    grid.innerHTML = '';
    res.results.forEach(item => {
      const card = document.createElement('div');
      card.className = 'mercury-card';
      
      const titleText = item.title || item.name || 'Unknown Product';
      const priceText = item.selling_price ? '$' + item.selling_price.toFixed(2) : '';
      
      card.innerHTML = `
        <img class="mercury-card-image" src="${item.image_url || 'data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs='}" alt="">
        <div class="mercury-card-content">
          <h4 class="mercury-card-title">${titleText}</h4>
          ${priceText ? `<p class="mercury-card-price">${priceText}</p>` : ''}
        </div>
      `;
      
      card.addEventListener('click', () => {
        this.selectResult(item);
        this.closeModal();
      });
      
      grid.appendChild(card);
    });
  }
  
  closeModal() {
    this.elements.overlay.classList.remove('active');
  }

  openChatModal() {
    this.closeDropdown();
    const { overlay } = this.elements;
    const title = overlay.querySelector('.mercury-modal-title');
    const body = overlay.querySelector('.mercury-modal-body');
    
    title.textContent = `Mercury AI Assistant`;
    
    body.innerHTML = `
      <div class="mercury-chat-container">
        <div class="mercury-chat-history"></div>
        <div class="mercury-chat-input-wrapper">
          <input type="text" class="mercury-chat-input" placeholder="Type your message...">
          <button class="mercury-chat-send">Send</button>
        </div>
      </div>
    `;
    
    overlay.classList.add('active');
    
    const history = body.querySelector('.mercury-chat-history');
    this.chatHistoryEl = history;
    
    this.appendChatMessage('ai', "Hi! I'm your AI shopping assistant. What are you looking for today?");
    
    const chatInput = body.querySelector('.mercury-chat-input');
    const sendBtn = body.querySelector('.mercury-chat-send');
    
    // Small timeout ensures modal display transition completes before focus
    setTimeout(() => chatInput.focus(), 100);
    
    const handleSend = async () => {
      const text = chatInput.value.trim();
      if (!text) return;
      this.appendChatMessage('user', text);
      chatInput.value = '';
      
      this.appendChatMessage('ai', 'Thinking...', true);
      const res = await this.api.chat(text, this.sessionId);
      
      const msgs = history.querySelectorAll('.mercury-chat-message');
      const lastMsg = msgs[msgs.length - 1];
      if (lastMsg && lastMsg.textContent === 'Thinking...') {
        lastMsg.remove();
      }
      
      this.appendChatMessage('ai', res.answer || "I'm sorry, I couldn't process that request.");
    };
    
    sendBtn.addEventListener('click', handleSend);
    chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') handleSend();
    });
  }
  
  appendChatMessage(role, text, isLoading = false) {
    if (!this.chatHistoryEl) return;
    const msg = document.createElement('div');
    msg.className = `mercury-chat-message ${role}`;
    msg.textContent = text;
    if (isLoading) msg.style.opacity = '0.7';
    this.chatHistoryEl.appendChild(msg);
    this.chatHistoryEl.scrollTop = this.chatHistoryEl.scrollHeight;
  }

  renderDropdown() {
    const { dropdown } = this.elements;
    const { results, isLoading } = this.state;
    
    if (isLoading) {
      dropdown.innerHTML = `<div class="mercury-loading">Searching...</div>`;
      return;
    }
    
    if (results.length === 0) {
      dropdown.innerHTML = `<div class="mercury-empty">No results found</div>`;
      return;
    }
    
    dropdown.innerHTML = '';
    
    results.forEach((item, i) => {
      const el = document.createElement('div');
      el.className = `mercury-result-item ${i === this.state.selectedIndex ? 'selected' : ''}`;
      
      const title = item.title || item.name || 'Unknown Product';
      const price = item.selling_price ? '$' + item.selling_price.toFixed(2) : '';
      const category = item.category || item.brand || '';
      
      el.innerHTML = `
        <img class="mercury-result-image" src="${item.image_url || 'data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs='}" alt="">
        <div class="mercury-result-content">
          <h4 class="mercury-result-title">${title}</h4>
          ${category ? `<p class="mercury-result-category">${category}</p>` : ''}
        </div>
        ${price ? `<div class="mercury-result-price">${price}</div>` : ''}
      `;
      
      el.addEventListener('mouseenter', () => {
        this.state.selectedIndex = i;
        this.updateSelection();
      });
      
      el.addEventListener('click', () => {
        this.selectResult(item);
      });
      
      dropdown.appendChild(el);
    });
    
    if (results.length > 0) {
      const viewAll = document.createElement('div');
      viewAll.className = `mercury-view-all ${results.length === this.state.selectedIndex ? 'selected' : ''}`;
      viewAll.textContent = `View all results for "${this.state.query}"`;
      
      viewAll.addEventListener('mouseenter', () => {
        this.state.selectedIndex = results.length;
        this.updateSelection();
      });
      
      viewAll.addEventListener('click', () => {
        this.openModal();
      });
      
      dropdown.appendChild(viewAll);
    }
  }
}
