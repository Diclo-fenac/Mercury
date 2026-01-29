// API Configuration
let API_BASE_URL = 'http://localhost:8000/api/v1';
let WS_BASE_URL = 'ws://localhost:8000/ws';
let ws = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadSettings();
    setupNavigation();
    showSection('search');
});

// Navigation Setup
function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const section = item.getAttribute('data-section');
            showSection(section);
            
            // Update active state
            navItems.forEach(i => i.classList.remove('active'));
            item.classList.add('active');
        });
    });
}

// Show Section
function showSection(sectionId) {
    const sections = document.querySelectorAll('.section');
    sections.forEach(section => {
        section.classList.remove('active');
        section.classList.add('hidden');
    });
    
    const section = document.getElementById(sectionId);
    if (section) {
        section.classList.remove('hidden');
        section.classList.add('active');
    }
}

// Utility Functions
function formatJSON(obj) {
    return JSON.stringify(obj, null, 2);
}

function displayResult(elementId, data, isError = false) {
    const element = document.getElementById(elementId);
    if (!element) return;

    element.innerHTML = '';
    
    if (isError) {
        element.innerHTML = `<div class="error">${data}</div>`;
        return;
    }
    
    const pre = document.createElement('pre');
    pre.textContent = typeof data === 'string' ? data : formatJSON(data);
    element.appendChild(pre);
}

// API Request Helper
async function makeRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        },
    };
    
    const finalOptions = { ...defaultOptions, ...options };
    
    try {
        const response = await fetch(url, finalOptions);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || `HTTP ${response.status}`);
        }
        
        return data;
    } catch (error) {
        throw new Error(`Request failed: ${error.message}`);
    }
}

// Search Functions
async function testAutocomplete() {
    const query = document.getElementById('autocompleteQuery').value;
    
    try {
        const data = await makeRequest(`/search/suggestions?q=${encodeURIComponent(query)}`);
        displayResult('autocompleteResult', data);
    } catch (error) {
        displayResult('autocompleteResult', `Error: ${error.message}`, true);
    }
}

async function testTrendingSearches() {
    const limit = document.getElementById('trendingLimit').value;
    const category = document.getElementById('trendingCategory').value;
    
    try {
        let endpoint = `/search/trending?limit=${limit}`;
        if (category) endpoint += `&category=${encodeURIComponent(category)}`;
        
        const data = await makeRequest(endpoint);
        displayResult('trendingSearchesResult', data);
    } catch (error) {
        displayResult('trendingSearchesResult', `Error: ${error.message}`, true);
    }
}

async function testPopularSearches() {
    const limit = document.getElementById('popularLimit').value;
    
    try {
        const data = await makeRequest(`/search/popular?limit=${limit}`);
        displayResult('popularSearchesResult', data);
    } catch (error) {
        displayResult('popularSearchesResult', `Error: ${error.message}`, true);
    }
}

async function testProductSearch() {
    const query = document.getElementById('productSearchQuery').value;
    const userId = document.getElementById('productSearchUserId').value;
    
    try {
        let endpoint = `/search/products?q=${encodeURIComponent(query)}`;
        if (userId) endpoint += `&user_id=${encodeURIComponent(userId)}`;
        
        const data = await makeRequest(endpoint);
        displayResult('productSearchResult', data);
    } catch (error) {
        displayResult('productSearchResult', `Error: ${error.message}`, true);
    }
}

// Image Intelligence Functions
async function testImageAnalysis() {
    const fileInput = document.getElementById('imageAnalysisFile');
    const userId = document.getElementById('imageAnalysisUserId').value;
    
    if (!fileInput.files[0]) {
        displayResult('imageAnalysisResult', 'Please select an image file', true);
        return;
    }
    
    try {
        const formData = new FormData();
        formData.append('image', fileInput.files[0]);
        formData.append('user_id', userId);
        formData.append('message', 'Analyze this image');
        
        const response = await fetch(`${API_BASE_URL}/images/analyze`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || `HTTP ${response.status}`);
        }
        
        displayResult('imageAnalysisResult', data);
        updateIntelligenceStatus('imageIntelligenceStatus', 'Active ✅');
    } catch (error) {
        displayResult('imageAnalysisResult', `Error: ${error.message}`, true);
        updateIntelligenceStatus('imageIntelligenceStatus', 'Error ❌');
    }
}

async function testBarcodeDetection() {
    const fileInput = document.getElementById('barcodeFile');
    const userId = document.getElementById('barcodeUserId').value;
    
    if (!fileInput.files[0]) {
        displayResult('barcodeResult', 'Please select an image file', true);
        return;
    }
    
    try {
        const formData = new FormData();
        formData.append('image', fileInput.files[0]);
        formData.append('user_id', userId);
        
        const response = await fetch(`${API_BASE_URL}/images/barcode`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || `HTTP ${response.status}`);
        }
        
        displayResult('barcodeResult', data);
        updateIntelligenceStatus('imageIntelligenceStatus', 'Active ✅');
    } catch (error) {
        displayResult('barcodeResult', `Error: ${error.message}`, true);
    }
}

async function testCachedAnalysis() {
    const cacheKey = document.getElementById('cachedAnalysisKey').value;
    const userId = document.getElementById('cachedAnalysisUserId').value;
    
    try {
        const data = await makeRequest(`/images/analysis/${encodeURIComponent(cacheKey)}?user_id=${userId}`);
        displayResult('cachedAnalysisResult', data);
    } catch (error) {
        displayResult('cachedAnalysisResult', `Error: ${error.message}`, true);
    }
}

// Variant Discovery Functions
async function testFindVariants() {
    const referenceProduct = document.getElementById('variantReferenceProduct').value;
    
    try {
        const productData = JSON.parse(referenceProduct);
        const data = await makeRequest('/products/variants', {
            method: 'POST',
            body: JSON.stringify({ reference_product: productData })
        });
        displayResult('findVariantsResult', data);
        updateIntelligenceStatus('variantDiscoveryStatus', 'Active ✅');
    } catch (error) {
        displayResult('findVariantsResult', `Error: ${error.message}`, true);
        updateIntelligenceStatus('variantDiscoveryStatus', 'Error ❌');
    }
}

async function testProductSubstitutes() {
    const referenceProduct = document.getElementById('substituteReferenceProduct').value;
    
    try {
        const productData = JSON.parse(referenceProduct);
        const data = await makeRequest('/products/substitutes', {
            method: 'POST',
            body: JSON.stringify({ reference_product: productData })
        });
        displayResult('productSubstitutesResult', data);
        updateIntelligenceStatus('variantDiscoveryStatus', 'Active ✅');
    } catch (error) {
        displayResult('productSubstitutesResult', `Error: ${error.message}`, true);
    }
}

async function testProductAvailability() {
    const productId = document.getElementById('availabilityProductId').value;
    
    try {
        const data = await makeRequest(`/products/${productId}/availability`);
        displayResult('productAvailabilityResult', data);
    } catch (error) {
        displayResult('productAvailabilityResult', `Error: ${error.message}`, true);
    }
}

// Personalization Functions
async function testApplyPersonalization() {
    const userId = document.getElementById('personalizationUserId').value;
    const sessionId = document.getElementById('personalizationSessionId').value;
    const products = document.getElementById('personalizationProducts').value;
    
    try {
        const productsData = JSON.parse(products);
        const data = await makeRequest('/personalization/apply', {
            method: 'POST',
            body: JSON.stringify({
                user_id: userId,
                session_id: sessionId,
                products: productsData
            })
        });
        displayResult('applyPersonalizationResult', data);
        updateIntelligenceStatus('personalizationStatus', 'Active ✅');
    } catch (error) {
        displayResult('applyPersonalizationResult', `Error: ${error.message}`, true);
        updateIntelligenceStatus('personalizationStatus', 'Error ❌');
    }
}

async function testSetSessionConstraints() {
    const userId = document.getElementById('constraintsUserId').value;
    const sessionId = document.getElementById('constraintsSessionId').value;
    const constraints = document.getElementById('sessionConstraints').value;
    const ttl = document.getElementById('constraintsTTL').value;
    
    try {
        const constraintsData = JSON.parse(constraints);
        const data = await makeRequest('/personalization/constraints', {
            method: 'POST',
            body: JSON.stringify({
                user_id: userId,
                session_id: sessionId,
                constraints: constraintsData,
                ttl: parseInt(ttl)
            })
        });
        displayResult('setSessionConstraintsResult', data);
        updateIntelligenceStatus('personalizationStatus', 'Active ✅');
    } catch (error) {
        displayResult('setSessionConstraintsResult', `Error: ${error.message}`, true);
    }
}

async function testGetBehavioralContext() {
    const userId = document.getElementById('contextUserId').value;
    const sessionId = document.getElementById('contextSessionId').value;
    
    try {
        let endpoint = `/personalization/context/${userId}`;
        if (sessionId) endpoint += `?session_id=${sessionId}`;
        
        const data = await makeRequest(endpoint);
        displayResult('getBehavioralContextResult', data);
    } catch (error) {
        displayResult('getBehavioralContextResult', `Error: ${error.message}`, true);
    }
}

// Workflow Functions
async function testExecuteWorkflow() {
    const triggerType = document.getElementById('workflowTriggerType').value;
    const context = document.getElementById('workflowContext').value;
    const maxChainLength = document.getElementById('maxChainLength').value;
    
    try {
        const contextData = JSON.parse(context);
        const data = await makeRequest('/workflow/execute', {
            method: 'POST',
            body: JSON.stringify({
                trigger_type: triggerType,
                context: contextData,
                max_chain_length: parseInt(maxChainLength)
            })
        });
        displayResult('executeWorkflowResult', data);
        updateIntelligenceStatus('workflowStatus', 'Active ✅');
    } catch (error) {
        displayResult('executeWorkflowResult', `Error: ${error.message}`, true);
        updateIntelligenceStatus('workflowStatus', 'Error ❌');
    }
}

async function testSuggestNextActions() {
    const currentContext = document.getElementById('currentContext').value;
    const userIntent = document.getElementById('userIntent').value;
    
    try {
        const contextData = JSON.parse(currentContext);
        const requestBody = { current_context: contextData };
        if (userIntent) requestBody.user_intent = userIntent;
        
        const data = await makeRequest('/workflow/suggestions', {
            method: 'POST',
            body: JSON.stringify(requestBody)
        });
        displayResult('suggestNextActionsResult', data);
        updateIntelligenceStatus('workflowStatus', 'Active ✅');
    } catch (error) {
        displayResult('suggestNextActionsResult', `Error: ${error.message}`, true);
    }
}

async function testGetWorkflowStatus() {
    const workflowId = document.getElementById('workflowId').value;
    
    try {
        let endpoint = '/workflow/status';
        if (workflowId) endpoint += `?workflow_id=${workflowId}`;
        
        const data = await makeRequest(endpoint);
        displayResult('getWorkflowStatusResult', data);
    } catch (error) {
        displayResult('getWorkflowStatusResult', `Error: ${error.message}`, true);
    }
}

// Trending Functions
async function testTrendingProducts() {
    const limit = document.getElementById('trendingProdLimit').value;
    const category = document.getElementById('trendingProdCategory').value;
    const days = document.getElementById('trendingDays').value;
    
    try {
        let endpoint = `/products/trending?limit=${limit}&days=${days}`;
        if (category) endpoint += `&category=${encodeURIComponent(category)}`;
        
        const data = await makeRequest(endpoint);
        displayResult('trendingProductsResult', data);
    } catch (error) {
        displayResult('trendingProductsResult', `Error: ${error.message}`, true);
    }
}

// Deals Functions
async function testDeals() {
    const limit = document.getElementById('dealsLimit').value;
    const minDiscount = document.getElementById('minDiscount').value;
    const category = document.getElementById('dealsCategory').value;
    
    try {
        let endpoint = `/products/deals?limit=${limit}&min_discount=${minDiscount}`;
        if (category) endpoint += `&category=${encodeURIComponent(category)}`;
        
        const data = await makeRequest(endpoint);
        displayResult('dealsResult', data);
    } catch (error) {
        displayResult('dealsResult', `Error: ${error.message}`, true);
    }
}

async function testFlashDeals() {
    const limit = document.getElementById('flashDealsLimit').value;
    
    try {
        const data = await makeRequest(`/products/flash-deals?limit=${limit}`);
        displayResult('flashDealsResult', data);
    } catch (error) {
        displayResult('flashDealsResult', `Error: ${error.message}`, true);
    }
}

// Product Functions
async function testProductDetails() {
    const productId = document.getElementById('productId').value;
    
    try {
        const data = await makeRequest(`/products/${productId}`);
        displayResult('productDetailsResult', data);
    } catch (error) {
        displayResult('productDetailsResult', `Error: ${error.message}`, true);
    }
}

async function testProductRecommendations() {
    const productId = document.getElementById('recProductId').value;
    const recType = document.getElementById('recType').value;
    const limit = document.getElementById('recLimit').value;
    
    try {
        const data = await makeRequest(`/products/${productId}/recommendations/${recType}?limit=${limit}`);
        displayResult('productRecommendationsResult', data);
    } catch (error) {
        displayResult('productRecommendationsResult', `Error: ${error.message}`, true);
    }
}

// User Functions
async function testUserProfile() {
    const userId = document.getElementById('userId').value;
    
    try {
        const data = await makeRequest(`/users/${userId}`);
        displayResult('userProfileResult', data);
    } catch (error) {
        displayResult('userProfileResult', `Error: ${error.message}`, true);
    }
}

async function testUserPreferences() {
    const userId = document.getElementById('userPrefId').value;
    
    try {
        const data = await makeRequest(`/users/${userId}/preferences`);
        displayResult('userPreferencesResult', data);
    } catch (error) {
        displayResult('userPreferencesResult', `Error: ${error.message}`, true);
    }
}

async function testPersonalizedRecommendations() {
    const userId = document.getElementById('personalizedUserId').value;
    const limit = document.getElementById('personalizedLimit').value;
    const category = document.getElementById('personalizedCategory').value;
    
    try {
        let endpoint = `/users/${userId}/recommendations?limit=${limit}`;
        if (category) endpoint += `&category=${encodeURIComponent(category)}`;
        
        const data = await makeRequest(endpoint);
        displayResult('personalizedRecommendationsResult', data);
    } catch (error) {
        displayResult('personalizedRecommendationsResult', `Error: ${error.message}`, true);
    }
}

// Conversation Functions
async function testListConversations() {
    const userId = document.getElementById('convUserId').value;
    const limit = document.getElementById('convLimit').value;
    
    try {
        const data = await makeRequest(`/conversations?user_id=${userId}&limit=${limit}`);
        displayResult('listConversationsResult', data);
    } catch (error) {
        displayResult('listConversationsResult', `Error: ${error.message}`, true);
    }
}

async function testGetConversation() {
    const conversationId = document.getElementById('getConvId').value;
    
    try {
        const data = await makeRequest(`/conversations/${conversationId}`);
        displayResult('getConversationResult', data);
    } catch (error) {
        displayResult('getConversationResult', `Error: ${error.message}`, true);
    }
}

async function testCreateConversation() {
    const userId = document.getElementById('createConvUserId').value;
    const title = document.getElementById('createConvTitle').value;
    
    try {
        const data = await makeRequest('/conversations', {
            method: 'POST',
            body: JSON.stringify({
                user_id: userId,
                title: title
            })
        });
        displayResult('createConversationResult', data);
    } catch (error) {
        displayResult('createConversationResult', `Error: ${error.message}`, true);
    }
}

// Enhanced Chat Functions
function handleChatKeyPress(event) {
    if (event.key === 'Enter') {
        sendChatMessage();
    }
}

function handleImageUpload(event) {
    const file = event.target.files[0];
    if (file) {
        // Show image preview
        const reader = new FileReader();
        reader.onload = function(e) {
            addChatMessage('user', `📷 Image uploaded: ${file.name}`, true);
        };
        reader.readAsDataURL(file);
    }
}

async function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const imageInput = document.getElementById('chatImageInput');
    const userId = document.getElementById('chatUserId').value;
    const conversationId = document.getElementById('chatConversationId').value;
    
    const message = input.value.trim();
    const hasImage = imageInput.files.length > 0;
    
    if (!message && !hasImage) return;
    
    // Add user message to chat
    addChatMessage('user', message || '📷 Image message');
    
    // Clear input
    input.value = '';
    
    try {
        let response;
        
        if (hasImage) {
            // Send image message
            const formData = new FormData();
            formData.append('image', imageInput.files[0]);
            formData.append('user_id', userId);
            formData.append('conversation_id', conversationId);
            formData.append('message', message || 'Analyze this image');
            
            response = await fetch(`${API_BASE_URL}/chat/image`, {
                method: 'POST',
                body: formData
            });
            
            // Clear image input
            imageInput.value = '';
        } else {
            // Send text message
            response = await fetch(`${API_BASE_URL}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    user_id: userId,
                    conversation_id: conversationId
                })
            });
        }
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || `HTTP ${response.status}`);
        }
        
        // Add AI response to chat
        addChatMessage('assistant', data.response || 'No response');
        
        // Update intelligence status based on features used
        if (data.features_used) {
            if (data.features_used.enhanced_image_analysis) {
                updateIntelligenceStatus('imageIntelligenceStatus', 'Active ✅');
            }
            if (data.features_used.function_calling) {
                updateIntelligenceStatus('workflowStatus', 'Active ✅');
            }
            if (data.features_used.personalization) {
                updateIntelligenceStatus('personalizationStatus', 'Active ✅');
            }
        }
        
        displayResult('chatResult', data);
        
    } catch (error) {
        addChatMessage('system', `Error: ${error.message}`, false, true);
        displayResult('chatResult', `Error: ${error.message}`, true);
    }
}

function addChatMessage(role, message, isImage = false, isError = false) {
    const messagesContainer = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role}`;
    
    if (isError) {
        messageDiv.className += ' error';
    }
    
    const roleIcon = role === 'user' ? '👤' : role === 'assistant' ? '🤖' : '⚠️';
    messageDiv.innerHTML = `
        <div class="message-header">
            <span class="role-icon">${roleIcon}</span>
            <span class="role-name">${role.charAt(0).toUpperCase() + role.slice(1)}</span>
            <span class="timestamp">${new Date().toLocaleTimeString()}</span>
        </div>
        <div class="message-content">${message}</div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function updateIntelligenceStatus(elementId, status) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = status;
        element.className = 'status-value ' + (status.includes('✅') ? 'active' : status.includes('❌') ? 'error' : '');
    }
}

// WebSocket Functions
function connectWebSocket() {
    const userId = document.getElementById('wsUserId').value;
    const userName = document.getElementById('wsUserName').value;
    
    if (ws) {
        ws.close();
    }
    
    try {
        ws = new WebSocket(`${WS_BASE_URL}?user_id=${userId}&user_name=${encodeURIComponent(userName)}`);
        
        ws.onopen = function(event) {
            updateWSStatus('Connected', true);
            addWSMessage('system', 'Connected to WebSocket');
            displayResult('wsConnectionResult', 'WebSocket connected successfully');
        };
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            addWSMessage('received', formatJSON(data));
        };
        
        ws.onclose = function(event) {
            updateWSStatus('Disconnected', false);
            addWSMessage('system', 'Disconnected from WebSocket');
        };
        
        ws.onerror = function(error) {
            updateWSStatus('Error', false);
            addWSMessage('system', `WebSocket error: ${error}`);
            displayResult('wsConnectionResult', `WebSocket error: ${error}`, true);
        };
        
    } catch (error) {
        displayResult('wsConnectionResult', `Connection failed: ${error.message}`, true);
    }
}

function disconnectWebSocket() {
    if (ws) {
        ws.close();
        ws = null;
    }
}

function sendWebSocketMessage() {
    const message = document.getElementById('wsMessage').value;
    
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        addWSMessage('system', 'WebSocket not connected');
        return;
    }
    
    const messageData = {
        type: 'message',
        content: message,
        timestamp: new Date().toISOString()
    };
    
    ws.send(JSON.stringify(messageData));
    addWSMessage('sent', message);
    
    document.getElementById('wsMessage').value = '';
}

function sendTypingIndicator(isTyping) {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        addWSMessage('system', 'WebSocket not connected');
        return;
    }
    
    const messageData = {
        type: 'typing',
        is_typing: isTyping,
        timestamp: new Date().toISOString()
    };
    
    ws.send(JSON.stringify(messageData));
    addWSMessage('system', `Typing indicator: ${isTyping ? 'started' : 'stopped'}`);
}

function addWSMessage(type, message) {
    const messagesContainer = document.getElementById('wsMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `ws-message ${type}`;
    
    const timestamp = new Date().toLocaleTimeString();
    messageDiv.innerHTML = `
        <span class="ws-timestamp">[${timestamp}]</span>
        <span class="ws-type">${type.toUpperCase()}:</span>
        <span class="ws-content">${typeof message === 'string' ? message : formatJSON(message)}</span>
    `;
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function updateWSStatus(status, connected) {
    const indicator = document.querySelector('.status-dot');
    const text = document.querySelector('.status-text');
    
    text.textContent = status;
    if (connected) {
        indicator.classList.add('connected');
    } else {
        indicator.classList.remove('connected');
    }
}

// Health Check Function
async function testHealthCheck() {
    try {
        const data = await makeRequest('/health');
        displayResult('healthCheckResult', data);
    } catch (error) {
        displayResult('healthCheckResult', `Error: ${error.message}`, true);
    }
}

// Settings Functions
function loadSettings() {
    const savedApiUrl = localStorage.getItem('apiBaseUrl');
    const savedWsUrl = localStorage.getItem('wsBaseUrl');
    
    if (savedApiUrl) {
        API_BASE_URL = savedApiUrl;
        document.getElementById('apiBaseUrl').value = savedApiUrl;
    }
    
    if (savedWsUrl) {
        WS_BASE_URL = savedWsUrl;
        document.getElementById('wsBaseUrl').value = savedWsUrl;
    }
}

function saveSettings() {
    const apiUrl = document.getElementById('apiBaseUrl').value;
    const wsUrl = document.getElementById('wsBaseUrl').value;
    
    API_BASE_URL = apiUrl;
    WS_BASE_URL = wsUrl;
    
    localStorage.setItem('apiBaseUrl', apiUrl);
    localStorage.setItem('wsBaseUrl', wsUrl);
    
    displayResult('settingsResult', 'Settings saved successfully');
}

function resetSettings() {
    API_BASE_URL = 'http://localhost:8000/api/v1';
    WS_BASE_URL = 'ws://localhost:8000/ws';
    
    document.getElementById('apiBaseUrl').value = API_BASE_URL;
    document.getElementById('wsBaseUrl').value = WS_BASE_URL;
    
    localStorage.removeItem('apiBaseUrl');
    localStorage.removeItem('wsBaseUrl');
    
    displayResult('settingsResult', 'Settings reset to default');
}
    
    element.classList.remove('empty', 'error', 'success');
    
    if (data === null || data === undefined) {
        element.textContent = 'No data';
        element.classList.add('empty');
    } else if (typeof data === 'string') {
        element.textContent = data;
        if (isError) element.classList.add('error');
        else element.classList.add('success');
    } else {
        element.textContent = formatJSON(data);
        if (isError) element.classList.add('error');
        else element.classList.add('success');
    }
}

async function makeRequest(endpoint, method = 'GET', body = null) {
    try {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            }
        };
        
        if (body) {
            options.body = JSON.stringify(body);
        }
        
        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || `HTTP ${response.status}`);
        }
        
        return data;
    } catch (error) {
        throw error;
    }
}

// Search Endpoints
async function testSearchSuggestions() {
    const query = document.getElementById('searchQuery').value;
    const limit = document.getElementById('searchLimit').value;
    
    if (query.length < 2) {
        displayResult('searchSuggestionsResult', 'Query must be at least 2 characters', true);
        return;
    }
    
    try {
        const data = await makeRequest(`/search/autocomplete?q=${encodeURIComponent(query)}&limit=${limit}`);
        displayResult('searchSuggestionsResult', data);
    } catch (error) {
        displayResult('searchSuggestionsResult', `Error: ${error.message}`, true);
    }
}

async function testTrendingSearches() {
    const limit = document.getElementById('trendingLimit').value;
    const category = document.getElementById('trendingCategory').value;
    
    try {
        let endpoint = `/search/trending?limit=${limit}`;
        if (category) endpoint += `&category=${encodeURIComponent(category)}`;
        
        const data = await makeRequest(endpoint);
        displayResult('trendingSearchesResult', data);
    } catch (error) {
        displayResult('trendingSearchesResult', `Error: ${error.message}`, true);
    }
}

async function testPopularSearches() {
    const limit = document.getElementById('popularLimit').value;
    
    try {
        const data = await makeRequest(`/search/popular?limit=${limit}`);
        displayResult('popularSearchesResult', data);
    } catch (error) {
        displayResult('popularSearchesResult', `Error: ${error.message}`, true);
    }
}

async function testSearchProducts() {
    const query = document.getElementById('productQuery').value;
    const userId = document.getElementById('userId').value;
    const limit = document.getElementById('searchProductLimit').value;
    
    try {
        const data = await makeRequest('/search/', 'POST', {
            query,
            user_id: userId,
            limit: parseInt(limit)
        });
        displayResult('searchProductsResult', data);
    } catch (error) {
        displayResult('searchProductsResult', `Error: ${error.message}`, true);
    }
}

// Product Endpoints
async function testTrendingProducts() {
    const limit = document.getElementById('trendingProdLimit').value;
    const category = document.getElementById('trendingProdCategory').value;
    const days = document.getElementById('trendingDays').value;
    
    try {
        let endpoint = `/products/trending?limit=${limit}&days=${days}`;
        if (category) endpoint += `&category=${encodeURIComponent(category)}`;
        
        const data = await makeRequest(endpoint);
        displayResult('trendingProductsResult', data);
    } catch (error) {
        displayResult('trendingProductsResult', `Error: ${error.message}`, true);
    }
}

async function testDeals() {
    const minDiscount = document.getElementById('minDiscount').value;
    const category = document.getElementById('dealsCategory').value;
    const limit = document.getElementById('dealsLimit').value;
    
    try {
        let endpoint = `/products/deals?min_discount=${minDiscount}&limit=${limit}`;
        if (category) endpoint += `&category=${encodeURIComponent(category)}`;
        
        const data = await makeRequest(endpoint);
        displayResult('dealsResult', data);
    } catch (error) {
        displayResult('dealsResult', `Error: ${error.message}`, true);
    }
}

async function testFlashDeals() {
    const limit = document.getElementById('flashDealsLimit').value;
    
    try {
        const data = await makeRequest(`/products/flash-deals?limit=${limit}`);
        displayResult('flashDealsResult', data);
    } catch (error) {
        displayResult('flashDealsResult', `Error: ${error.message}`, true);
    }
}

async function testBrandDeals() {
    const brand = document.getElementById('brandName').value;
    const limit = document.getElementById('brandDealsLimit').value;
    
    try {
        const data = await makeRequest(`/products/deals/brand/${encodeURIComponent(brand)}?limit=${limit}`);
        displayResult('brandDealsResult', data);
    } catch (error) {
        displayResult('brandDealsResult', `Error: ${error.message}`, true);
    }
}

async function testProductRecommendations() {
    const productId = document.getElementById('productId').value;
    const limit = document.getElementById('recLimit').value;
    const type = document.getElementById('recType').value;
    
    try {
        const data = await makeRequest(`/products/${productId}/recommendations?limit=${limit}&recommendation_type=${type}`);
        displayResult('productRecommendationsResult', data);
    } catch (error) {
        displayResult('productRecommendationsResult', `Error: ${error.message}`, true);
    }
}

// User Endpoints
async function testUserProfile() {
    const userId = document.getElementById('userIdProfile').value;
    
    try {
        const data = await makeRequest(`/users/${userId}/profile`);
        displayResult('userProfileResult', data);
    } catch (error) {
        displayResult('userProfileResult', `Error: ${error.message}`, true);
    }
}

async function testUserPreferences() {
    const userId = document.getElementById('userIdPrefs').value;
    
    try {
        const data = await makeRequest(`/users/${userId}/preferences`);
        displayResult('userPreferencesResult', data);
    } catch (error) {
        displayResult('userPreferencesResult', `Error: ${error.message}`, true);
    }
}

async function testUserActivity() {
    const userId = document.getElementById('userIdActivity').value;
    const limit = document.getElementById('activityLimit').value;
    const activityType = document.getElementById('activityType').value;
    
    try {
        let endpoint = `/users/${userId}/activity?limit=${limit}`;
        if (activityType) endpoint += `&activity_type=${encodeURIComponent(activityType)}`;
        
        const data = await makeRequest(endpoint);
        displayResult('userActivityResult', data);
    } catch (error) {
        displayResult('userActivityResult', `Error: ${error.message}`, true);
    }
}

async function testPersonalizedRecommendations() {
    const userId = document.getElementById('userIdRec').value;
    const limit = document.getElementById('userRecLimit').value;
    const category = document.getElementById('userRecCategory').value;
    
    try {
        let endpoint = `/users/${userId}/recommendations?limit=${limit}`;
        if (category) endpoint += `&category=${encodeURIComponent(category)}`;
        
        const data = await makeRequest(endpoint);
        displayResult('personalizedRecommendationsResult', data);
    } catch (error) {
        displayResult('personalizedRecommendationsResult', `Error: ${error.message}`, true);
    }
}

async function testSimilarUsersRecommendations() {
    const userId = document.getElementById('userIdSimilar').value;
    const limit = document.getElementById('similarUserLimit').value;
    
    try {
        const data = await makeRequest(`/users/${userId}/recommendations/similar-users?limit=${limit}`);
        displayResult('similarUsersRecommendationsResult', data);
    } catch (error) {
        displayResult('similarUsersRecommendationsResult', `Error: ${error.message}`, true);
    }
}

async function testFrequentlyBoughtTogether() {
    const userId = document.getElementById('userIdFBT').value;
    const productId = document.getElementById('productIdFBT').value;
    const limit = document.getElementById('fbtLimit').value;
    
    try {
        const data = await makeRequest(`/users/${userId}/recommendations/frequently-bought-together/${productId}?limit=${limit}`);
        displayResult('frequentlyBoughtTogetherResult', data);
    } catch (error) {
        displayResult('frequentlyBoughtTogetherResult', `Error: ${error.message}`, true);
    }
}

// Image Endpoints
async function testImageUpload() {
    const fileInput = document.getElementById('imageFile');
    const userId = document.getElementById('imageUserId').value;
    const message = document.getElementById('imageMessage').value;
    
    if (!fileInput.files.length) {
        displayResult('imageUploadResult', 'Please select an image file', true);
        return;
    }
    
    try {
        const file = fileInput.files[0];
        const reader = new FileReader();
        
        reader.onload = async (e) => {
            const imageData = e.target.result;
            const data = await makeRequest('/images/upload', 'POST', {
                image_data: imageData,
                user_id: userId,
                message: message,
                create_chat_message: false
            });
            displayResult('imageUploadResult', data);
        };
        
        reader.readAsDataURL(file);
    } catch (error) {
        displayResult('imageUploadResult', `Error: ${error.message}`, true);
    }
}

async function testImageSearch() {
    const fileInput = document.getElementById('imageSearchFile');
    const userId = document.getElementById('imageSearchUserId').value;
    const prompt = document.getElementById('imageSearchPrompt').value;
    const searchType = document.getElementById('imageSearchType').value;
    
    if (!fileInput.files.length) {
        displayResult('imageSearchResult', 'Please select an image file', true);
        return;
    }
    
    try {
        const file = fileInput.files[0];
        const reader = new FileReader();
        
        reader.onload = async (e) => {
            const imageData = e.target.result;
            const data = await makeRequest('/images/search', 'POST', {
                image_data: imageData,
                prompt: prompt,
                search_type: searchType,
                limit: 10,
                user_id: userId
            });
            displayResult('imageSearchResult', data);
        };
        
        reader.readAsDataURL(file);
    } catch (error) {
        displayResult('imageSearchResult', `Error: ${error.message}`, true);
    }
}

// Conversation Endpoints
async function testGetConversations() {
    const userId = document.getElementById('convUserId').value;
    const limit = document.getElementById('convLimit').value;
    
    try {
        const data = await makeRequest(`/conversations/${userId}?limit=${limit}`);
        displayResult('getConversationsResult', data);
    } catch (error) {
        displayResult('getConversationsResult', `Error: ${error.message}`, true);
    }
}

async function testGetConversationDetail() {
    const userId = document.getElementById('convUserIdDetail').value;
    const conversationId = document.getElementById('conversationId').value;
    
    try {
        const data = await makeRequest(`/conversations/${userId}/${conversationId}`);
        displayResult('getConversationDetailResult', data);
    } catch (error) {
        displayResult('getConversationDetailResult', `Error: ${error.message}`, true);
    }
}

async function testCreateConversation() {
    const userId = document.getElementById('convUserIdCreate').value;
    const title = document.getElementById('convTitle').value;
    
    try {
        const data = await makeRequest(`/conversations/${userId}`, 'POST', {
            title: title,
            metadata: { source: 'api' }
        });
        displayResult('createConversationResult', data);
    } catch (error) {
        displayResult('createConversationResult', `Error: ${error.message}`, true);
    }
}

// WebSocket Functions
function connectWebSocket() {
    const userId = document.getElementById('wsUserId').value;
    const userName = document.getElementById('wsUserName').value;
    
    try {
        ws = new WebSocket(WS_BASE_URL);
        
        ws.onopen = () => {
            updateWSStatus('Connected', true);
            addWSMessage('System', 'Connected to WebSocket', 'system');
            
            // Send authentication
            ws.send(JSON.stringify({
                event: 'user_auth',
                data: {
                    user_id: userId,
                    user_name: userName
                }
            }));
        };
        
        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            addWSMessage('Server', formatJSON(message), 'assistant');
        };
        
        ws.onerror = (error) => {
            updateWSStatus('Error', false);
            addWSMessage('System', `Error: ${error.message}`, 'system');
        };
        
        ws.onclose = () => {
            updateWSStatus('Disconnected', false);
            addWSMessage('System', 'Disconnected from WebSocket', 'system');
        };
    } catch (error) {
        displayResult('wsStatusResult', `Error: ${error.message}`, true);
    }
}

function disconnectWebSocket() {
    if (ws) {
        ws.close();
        updateWSStatus('Disconnected', false);
    }
}

function sendWebSocketMessage() {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        addWSMessage('System', 'WebSocket not connected', 'system');
        return;
    }
    
    const message = document.getElementById('wsMessage').value;
    if (!message) return;
    
    ws.send(JSON.stringify({
        event: 'chat_message',
        data: {
            message: message,
            user_id: document.getElementById('wsUserId').value,
            conversation_id: document.getElementById('wsConvId').value
        }
    }));
    
    addWSMessage('You', message, 'user');
    document.getElementById('wsMessage').value = '';
}

function sendTypingIndicator(typing) {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        addWSMessage('System', 'WebSocket not connected', 'system');
        return;
    }
    
    ws.send(JSON.stringify({
        event: 'typing',
        data: {
            user_id: document.getElementById('wsUserId').value,
            conversation_id: document.getElementById('wsConvId').value,
            typing: typing
        }
    }));
    
    addWSMessage('System', typing ? 'Started typing...' : 'Stopped typing', 'system');
}

function updateWSStatus(status, connected) {
    const indicator = document.querySelector('.status-dot');
    const text = document.querySelector('.status-text');
    
    text.textContent = status;
    if (connected) {
        indicator.classList.add('connected');
    } else {
        indicator.classList.remove('connected');
    }
}

function addWSMessage(sender, message, type = 'assistant') {
    const messagesBox = document.getElementById('wsMessages');
    const messageEl = document.createElement('div');
    messageEl.className = `message ${type}`;
    
    const time = new Date().toLocaleTimeString();
    messageEl.innerHTML = `
        <strong>${sender}</strong>
        <div>${message}</div>
        <div class="message-time">${time}</div>
    `;
    
    messagesBox.appendChild(messageEl);
    messagesBox.scrollTop = messagesBox.scrollHeight;
}

// Chat Functions
async function sendChatMessage() {
    const message = document.getElementById('chatInput').value;
    const userId = document.getElementById('chatUserId').value;
    const conversationId = document.getElementById('chatConvId').value;
    
    if (!message) return;
    
    try {
        addChatMessage('You', message, 'user');
        document.getElementById('chatInput').value = '';
        
        const data = await makeRequest('/chat/', 'POST', {
            message: message,
            user_id: userId,
            conversation_id: conversationId,
            message_type: 'text'
        });
        
        if (data.response) {
            addChatMessage('Assistant', data.response, 'assistant');
        }
        
        displayResult('chatResult', data);
    } catch (error) {
        addChatMessage('System', `Error: ${error.message}`, 'system');
        displayResult('chatResult', `Error: ${error.message}`, true);
    }
}

function handleChatKeypress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendChatMessage();
    }
}

function addChatMessage(sender, message, type = 'assistant') {
    const messagesBox = document.getElementById('chatMessages');
    const messageEl = document.createElement('div');
    messageEl.className = `message ${type}`;
    
    const time = new Date().toLocaleTimeString();
    messageEl.innerHTML = `
        <strong>${sender}</strong>
        <div>${message}</div>
        <div class="message-time">${time}</div>
    `;
    
    messagesBox.appendChild(messageEl);
    messagesBox.scrollTop = messagesBox.scrollHeight;
}

// Health Check
async function testHealthCheck() {
    try {
        const response = await fetch(`${API_BASE_URL.replace('/api/v1', '')}/health`);
        const data = await response.json();
        displayResult('healthResult', data);
    } catch (error) {
        displayResult('healthResult', `Error: ${error.message}`, true);
    }
}

// Settings
function saveSettings() {
    const apiUrl = document.getElementById('apiBaseUrl').value;
    const wsUrl = document.getElementById('wsBaseUrl').value;
    
    API_BASE_URL = apiUrl;
    WS_BASE_URL = wsUrl;
    
    localStorage.setItem('apiBaseUrl', apiUrl);
    localStorage.setItem('wsBaseUrl', wsUrl);
    
    alert('Settings saved!');
}

function loadSettings() {
    const apiUrl = localStorage.getItem('apiBaseUrl') || 'http://localhost:8000/api/v1';
    const wsUrl = localStorage.getItem('wsBaseUrl') || 'ws://localhost:8000/ws';
    
    API_BASE_URL = apiUrl;
    WS_BASE_URL = wsUrl;
    
    document.getElementById('apiBaseUrl').value = apiUrl;
    document.getElementById('wsBaseUrl').value = wsUrl;
}

function clearAllData() {
    if (confirm('Are you sure you want to clear all results?')) {
        const resultBoxes = document.querySelectorAll('.result-box');
        resultBoxes.forEach(box => {
            box.textContent = '';
            box.classList.add('empty');
        });
        alert('All results cleared!');
    }
}
