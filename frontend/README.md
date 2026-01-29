# Walmart AI Assistant - Enhanced Frontend API Tester

A comprehensive web-based frontend for testing all API endpoints including the new **Intelligence Restoration** features of the Walmart AI Assistant.

## 🚀 New Intelligence Features

### 🧠 Phase 1: Image Intelligence
- **Enhanced Image Analysis** - Advanced product identification with Gemini Vision
- **Barcode Detection** - UPC/EAN/QR code detection with product lookup
- **Search Suggestion Cascade** - Exact → Similar → Category suggestions
- **Mobile-First Design** - Optimized for barcode scanning use cases

### 🔍 Phase 2: Variant Discovery  
- **Strict Variant Matching** - Tag-based filtering with priority order
- **Product Substitutes** - Alternative product recommendations
- **Availability Checking** - Real-time stock and availability status
- **Tag Priority Logic** - Brand → Product Type → Material → Pattern → Variants

### 🎯 Phase 3: Behavioral Personalization
- **Session Constraints** - Redis-based session-specific preferences
- **Behavioral Context** - Firestore + Redis merge logic
- **Constraint Override** - Session rules override long-term preferences
- **Cross-Session Handling** - Persistent preference management

### ⚡ Phase 4: Autonomous Workflows
- **Capability Chaining** - 7 configured autonomous workflows
- **Proactive Intelligence** - Context-aware action suggestions
- **Decision Flow Logic** - Confidence-based execution paths
- **Workflow Orchestration** - End-to-end intelligent automation

## 📊 Trending & Analytics Features

### 📈 Trending Analysis
- **Trending Products** - Algorithm: (Rating × 0.4) + (Discount × 0.3) + (Availability × 0.2) + (Recency × 0.1)
- **Configurable Time Periods** - 1-30 days analysis window (affects recency scoring)
- **Category Filtering** - Electronics, Clothing, Food, Home, etc.
- **Performance Caching** - 30-minute cache for optimal response times
- **Data Sources** - Uses actual database fields: rating, price.discount_percent, availability quantities, created_at

### 💰 Deals & Offers
- **Regular Deals** - Uses existing price.discount_percent or calculates: ((price.actual - price.selling) / price.actual) × 100
- **Flash Deals** - High discount (>40%) with urgency scoring based on stock levels
- **Minimum Discount Filtering** - Configurable threshold (default 20%)
- **Smart Caching** - Regular deals (15 min), Flash deals (5 min)
- **Data Sources** - Uses actual database fields: price.actual, price.selling, availability quantities

## Features

### 🔍 Core Search Testing
- **Autocomplete/Suggestions** - Test search suggestions with minimum 2 characters
- **Trending Searches** - Get trending search queries with optional category filtering
- **Popular Searches** - View most popular searches
- **Product Search** - Full-text search with user personalization

### 🖼️ Image Intelligence Testing
- **Enhanced Image Analysis** - Upload and analyze product images with AI
- **Barcode Detection** - Detect and decode barcodes from images
- **Cached Analysis** - Retrieve previously analyzed image results
- **Mobile-Optimized** - Touch-friendly interface for mobile barcode scanning

### 🔍 Variant Discovery Testing
- **Find Product Variants** - Discover same product in different sizes/colors
- **Product Substitutes** - Get alternative product recommendations
- **Availability Check** - Real-time stock and availability status
- **Tag-Based Matching** - Strict variant logic with priority ordering

### 🎯 Personalization Testing
- **Apply Behavioral Personalization** - Test product ranking with user preferences
- **Set Session Constraints** - Override long-term preferences (dietary, budget, size)
- **Get Behavioral Context** - View merged Firestore + Redis preferences
- **Constraint Logic Testing** - Validate session override behavior

### ⚡ Autonomous Workflow Testing
- **Execute Workflows** - Test capability chaining (image → barcode → search → personalization)
- **Suggest Next Actions** - Get proactive intelligence recommendations
- **Workflow Status** - Monitor performance metrics and execution history
- **Decision Flow Testing** - Validate confidence-based execution paths

### 📈 Analytics & Trending Testing
- **Trending Products** - Test trending algorithm with configurable parameters
- **Deals Discovery** - Find products with significant discounts
- **Flash Deals** - Time-limited offers with expiration tracking
- **Algorithm Insights** - Visual explanation of trending and deals logic

### 📦 Enhanced Product Testing
- **Product Details** - Get comprehensive product information
- **Product Recommendations** - Similar, complementary, substitute, variant products
- **Trending Analysis** - View trending scores and criteria
- **Deal Information** - Discount percentages and savings

### 👤 Enhanced User Testing
- **User Profile** - Get user profile information with behavioral data
- **User Preferences** - View and manage user preferences
- **Personalized Recommendations** - Hybrid recommendation engine with behavioral scoring
- **Session Management** - Test session-specific constraint handling

### 💬 Enhanced Chat Interface
- **AI Chat with Intelligence** - Chat with enhanced AI assistant
- **Image Upload Support** - Send images for analysis in chat
- **Intelligence Status Tracking** - Real-time status of intelligence features
- **Feature Usage Monitoring** - Track which intelligence features are active

### ⚡ Real-time Testing
- **WebSocket Connection** - Connect to WebSocket server
- **Send Messages** - Send real-time messages
- **Typing Indicators** - Send typing status
- **Message History** - View all WebSocket messages

### ❤️ Health & Settings
- **Health Check** - Monitor API health status
- **API Configuration** - Configure API and WebSocket URLs
- **Settings Management** - Save and load settings
- **Intelligence Overview** - Documentation of all 4 phases

## Getting Started

### Prerequisites
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Running Walmart AI Assistant backend server with Intelligence Restoration
- Backend server accessible at `http://localhost:8000`

### Installation

1. **Copy frontend files to your project:**
   ```bash
   cp -r frontend/ /path/to/your/project/
   ```

2. **Open in browser:**
   ```bash
   # Option 1: Direct file access
   open frontend/index.html
   
   # Option 2: Using Python HTTP server
   cd frontend
   python -m http.server 8080
   # Then visit http://localhost:8080
   
   # Option 3: Using Node.js HTTP server
   cd frontend
   npx http-server
   ```

3. **Configure API URLs (if needed):**
   - Go to Settings section
   - Update API Base URL (default: `http://localhost:8000/api/v1`)
   - Update WebSocket URL (default: `ws://localhost:8000/ws`)
   - Click "Save Settings"

## Usage Guide

### Testing Intelligence Features

#### 🖼️ Image Intelligence
1. **Navigate to Image Intelligence section**
2. **Test Enhanced Image Analysis:**
   - Select image file (product photo or barcode)
   - Enter user ID
   - Click "Analyze Image"
   - View comprehensive analysis results

3. **Test Barcode Detection:**
   - Select image with barcode
   - Enter user ID
   - Click "Detect Barcode"
   - View barcode data and product lookup

#### 🔍 Variant Discovery
1. **Navigate to Variant Discovery section**
2. **Test Find Variants:**
   - Enter reference product JSON
   - Click "Find Variants"
   - View strict variant matches

3. **Test Product Substitutes:**
   - Enter reference product JSON
   - Click "Get Substitutes"
   - View alternative recommendations

#### 🎯 Personalization
1. **Navigate to Personalization section**
2. **Set Session Constraints:**
   - Enter user ID and session ID
   - Define constraints (dietary, budget, size)
   - Click "Set Constraints"
   - Test constraint override logic

3. **Apply Personalization:**
   - Enter user ID and products JSON
   - Click "Apply Personalization"
   - View behavioral scoring results

#### ⚡ Autonomous Workflows
1. **Navigate to Workflow section**
2. **Execute Workflow:**
   - Select trigger type (image_upload, product_search, etc.)
   - Enter context JSON
   - Click "Execute Workflow"
   - View capability chaining results

3. **Get Suggestions:**
   - Enter current context
   - Add user intent
   - Click "Get Suggestions"
   - View proactive recommendations

### Testing Analytics Features

#### 📈 Trending Analysis
1. **Navigate to Trending section**
2. **Test Trending Products:**
   - Set limit and time period
   - Select category (optional)
   - Click "Get Trending Products"
   - View trending scores and algorithm explanation

#### 💰 Deals & Offers
1. **Navigate to Deals section**
2. **Test Regular Deals:**
   - Set minimum discount percentage
   - Select category (optional)
   - Click "Get Deals"
   - View discount calculations

3. **Test Flash Deals:**
   - Set limit
   - Click "Get Flash Deals"
   - View time-limited offers

### Testing Enhanced Chat

1. **Navigate to Enhanced Chat section**
2. **Setup Chat:**
   - Enter user ID and conversation ID
   - Start chatting with AI assistant

3. **Test Image Upload:**
   - Click camera button (📷)
   - Select image file
   - Send message with image
   - View AI analysis and response

4. **Monitor Intelligence Status:**
   - Watch intelligence features activate
   - View real-time status indicators
   - Track feature usage

## 🧠 Intelligence Algorithm Explanations

### Trending Products Algorithm (Based on Your Actual Database)
```
Trending Score = (Rating × 0.4) + (Discount × 0.3) + (Availability × 0.2) + (Recency × 0.1)

Components:
- Rating (40%): Product rating from your rating field (0-5 scale)
- Discount (30%): Discount percentage from price.discount_percent field
- Availability (20%): Total stock from availability array quantities
- Recency (10%): Newer products from created_at field get boost

Data Sources:
- Rating: product.rating
- Discount: product.price.discount_percent
- Stock: sum(product.availability[].quantity)
- Date: product.created_at

Caching: 30 minutes for performance
Time Period: Configurable 1-30 days (affects recency scoring)
```

### Deals Detection Logic (Based on Your Actual Database)
```
Discount % = Uses existing price.discount_percent OR calculates:
((price.actual - price.selling) / price.actual) × 100

Types:
- Regular Deals: Discount ≥ threshold (default 20%)
- Flash Deals: High discount (>40%) with urgency scoring
- Sorting: Highest discount percentage first

Data Sources:
- Original Price: product.price.actual
- Current Price: product.price.selling
- Stored Discount: product.price.discount_percent
- Stock: sum(product.availability[].quantity)

Caching: Regular (15 min), Flash (5 min)
```

### Personalization Scoring
```
Session Constraints Override Long-term Preferences

Example: User prefers "Amul" (Firestore) + Session requires "vegan" (Redis)
Result: Suggest soy alternatives, penalize dairy products

Scoring Weights:
- Session Constraints: 40% (highest priority)
- Long-term Preferences: 30%
- Behavioral Patterns: 20%
- Availability: 10%
```

### Capability Chaining Flows
```
7 Configured Autonomous Workflows:

1. Image Upload → Barcode Detection → Product Search → Personalization
2. Product Search → Variant Discovery → Availability Check
3. Barcode Scan → Product Lookup → Variant Discovery
4. Personalization → Substitute Suggestions (user confirmation)
5. Variant Discovery → Availability Check → Personalization
6. Image Analysis → Product Search → Variant Discovery
7. Context Analysis → Proactive Suggestions

Decision Logic: Confidence thresholds determine autonomous vs user-confirmation
```

## API Endpoints Tested

### Intelligence Endpoints
- `POST /images/analyze` - Enhanced image analysis
- `POST /images/barcode` - Barcode detection
- `GET /images/analysis/{key}` - Cached analysis
- `POST /products/variants` - Find product variants
- `POST /products/substitutes` - Product substitutes
- `GET /products/{id}/availability` - Availability check
- `POST /personalization/apply` - Apply personalization
- `POST /personalization/constraints` - Set session constraints
- `GET /personalization/context/{user_id}` - Behavioral context
- `POST /workflow/execute` - Execute autonomous workflow
- `POST /workflow/suggestions` - Suggest next actions
- `GET /workflow/status` - Workflow status

### Analytics Endpoints
- `GET /products/trending` - Trending products
- `GET /products/deals` - Regular deals
- `GET /products/flash-deals` - Flash deals

### Core Endpoints
- `GET /search/suggestions` - Autocomplete
- `GET /search/trending` - Trending searches
- `GET /search/popular` - Popular searches
- `GET /search/products` - Product search
- `GET /products/{id}` - Product details
- `GET /products/{id}/recommendations/{type}` - Recommendations
- `GET /users/{id}` - User profile
- `GET /users/{id}/preferences` - User preferences
- `GET /users/{id}/recommendations` - Personalized recommendations
- `GET /conversations` - List conversations
- `GET /conversations/{id}` - Conversation details
- `POST /conversations` - Create conversation
- `POST /chat` - Send chat message
- `POST /chat/image` - Send image message
- `GET /health` - Health check

### WebSocket Endpoints
- `WS /ws` - WebSocket connection

## Keyboard Shortcuts

- **Enter** in chat input: Send message
- **Ctrl+Enter** in textarea: Submit form

## Browser Compatibility

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

## Performance Features

- **Lazy Loading** - Sections load on demand
- **Response Caching** - Intelligent caching of API responses
- **Mobile Optimization** - Touch-friendly interface
- **Real-time Updates** - WebSocket for live data
- **Error Handling** - Comprehensive error management
- **Loading States** - Visual feedback for all operations

## Development Roadmap

### Phase 1 ✅ Completed
- [x] Core API testing interface
- [x] Intelligence features testing
- [x] Analytics and trending testing
- [x] Enhanced chat interface
- [x] Mobile-responsive design

### Phase 2
- [ ] Batch testing capabilities
- [ ] API response comparison
- [ ] Performance benchmarking
- [ ] Test automation scripts
- [ ] Export/import test configurations

### Phase 3
- [ ] GraphQL support
- [ ] Advanced filtering and search
- [ ] Custom test scenarios
- [ ] Analytics dashboard
- [ ] Team collaboration features

## Contributing

To contribute improvements:
1. Test thoroughly across different browsers
2. Follow existing code style and patterns
3. Update documentation for new features
4. Ensure mobile compatibility
5. Submit pull request with detailed description

## Changelog

### v2.0.0 (2024-01-24) - Intelligence Restoration
- ✨ Added Image Intelligence testing (Phase 1)
- ✨ Added Variant Discovery testing (Phase 2)  
- ✨ Added Behavioral Personalization testing (Phase 3)
- ✨ Added Autonomous Workflows testing (Phase 4)
- ✨ Added Trending Analysis with algorithm explanations
- ✨ Added Deals & Offers testing
- ✨ Enhanced chat interface with image upload
- ✨ Added intelligence status monitoring
- ✨ Improved mobile responsiveness
- ✨ Added comprehensive algorithm documentation

### v1.0.0 (2024-01-23)
- Initial release
- Basic API endpoints supported
- WebSocket testing
- Simple chat interface
- Settings management

---

**🚀 Enhanced Testing Experience with Full Intelligence Restoration Support!**
- **Typing Indicators** - Send typing status
- **Message History** - View all WebSocket messages

### 💭 Chat Interface
- **Interactive Chat** - Chat with AI assistant
- **Message History** - View conversation history
- **Real-time Responses** - Get instant AI responses

### ❤️ Health & Settings
- **Health Check** - Monitor API health status
- **API Configuration** - Configure API and WebSocket URLs
- **Settings Management** - Save and load settings

## Getting Started

### Prerequisites
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Running Walmart AI Assistant backend server
- Backend server accessible at `http://localhost:8000`

### Installation

1. **Copy frontend files to your project:**
   ```bash
   cp -r frontend/ /path/to/your/project/
   ```

2. **Open in browser:**
   ```bash
   # Option 1: Direct file access
   open frontend/index.html
   
   # Option 2: Using Python HTTP server
   cd frontend
   python -m http.server 8080
   # Then visit http://localhost:8080
   
   # Option 3: Using Node.js HTTP server
   cd frontend
   npx http-server
   ```

3. **Configure API URLs (if needed):**
   - Go to Settings section
   - Update API Base URL (default: `http://localhost:8000/api/v1`)
   - Update WebSocket URL (default: `ws://localhost:8000/ws`)
   - Click "Save Settings"

## Usage

### Testing Search Endpoints

1. **Navigate to Search section**
2. **Test Autocomplete:**
   - Enter search query (minimum 2 characters)
   - Click "Get Suggestions"
   - View results in the result box

3. **Test Trending Searches:**
   - Set limit (1-50)
   - Optionally select category
   - Click "Get Trending"

4. **Test Product Search:**
   - Enter search query
   - Set user ID for personalization
   - Click "Search"

### Testing Product Endpoints

1. **Navigate to Products section**
2. **Test Trending Products:**
   - Set limit and optional category
   - Set time period (days)
   - Click "Get Trending"

3. **Test Deals:**
   - Set minimum discount percentage
   - Optionally select category
   - Click "Get Deals"

4. **Test Product Recommendations:**
   - Enter product ID
   - Select recommendation type
   - Click "Get Recommendations"

### Testing User Endpoints

1. **Navigate to Users section**
2. **Test User Profile:**
   - Enter user ID
   - Click "Get Profile"

3. **Test Personalized Recommendations:**
   - Enter user ID
   - Set limit and optional category
   - Click "Get Recommendations"

### Testing Image Endpoints

1. **Navigate to Images section**
2. **Upload Image:**
   - Select image file
   - Enter user ID and message
   - Click "Upload Image"

3. **Image Search:**
   - Select image file
   - Enter search prompt
   - Select search type
   - Click "Search by Image"

### Testing WebSocket

1. **Navigate to WebSocket section**
2. **Connect:**
   - Enter user ID and name
   - Click "Connect"
   - Status indicator should show "Connected"

3. **Send Messages:**
   - Type message in input field
   - Click "Send" or press Enter
   - View messages in the messages box

4. **Typing Indicator:**
   - Click "Start Typing" to send typing indicator
   - Click "Stop Typing" to stop

### Using Chat Interface

1. **Navigate to Chat section**
2. **Enter user ID and conversation ID**
3. **Type message in chat input**
4. **Press Enter or click Send**
5. **View AI response in chat history**

## API Configuration

### Default URLs
- **API Base URL:** `http://localhost:8000/api/v1`
- **WebSocket URL:** `ws://localhost:8000/ws`

### Changing URLs
1. Go to Settings section
2. Update API Base URL
3. Update WebSocket URL
4. Click "Save Settings"

Settings are saved in browser's localStorage and persist across sessions.

## Features

### User-Friendly Interface
- Clean, modern design
- Intuitive navigation
- Responsive layout (works on mobile)
- Dark/light theme support

### Real-time Feedback
- Instant API responses
- Error handling with clear messages
- Loading indicators
- Status indicators

### Data Management
- JSON formatting for responses
- Copy-paste friendly results
- Clear all results option
- Settings persistence

### Testing Capabilities
- Test all 22 API endpoints
- WebSocket connection testing
- Real-time chat testing
- Batch testing support

## Keyboard Shortcuts

- **Enter** in chat input: Send message
- **Shift+Enter** in chat input: New line

## Troubleshooting

### Connection Issues

**Problem:** "Failed to connect to API"
- **Solution:** Check if backend server is running at configured URL
- **Solution:** Verify API Base URL in Settings

**Problem:** "WebSocket connection failed"
- **Solution:** Check if WebSocket server is running
- **Solution:** Verify WebSocket URL in Settings
- **Solution:** Check browser console for errors

### CORS Issues

**Problem:** "CORS error" in browser console
- **Solution:** Backend must have CORS enabled
- **Solution:** Check backend CORS configuration

### Image Upload Issues

**Problem:** "Image upload failed"
- **Solution:** Ensure image file is valid
- **Solution:** Check file size (should be < 5MB)
- **Solution:** Verify user ID is provided

## Browser Support

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## Performance Tips

1. **Use reasonable limits** - Don't request too many results at once
2. **Clear results** - Use "Clear All Results" to free memory
3. **Close WebSocket** - Disconnect when not testing
4. **Refresh page** - If experiencing slowness

## Development

### File Structure
```
frontend/
├── index.html          # Main HTML file
├── styles.css          # Styling
├── app.js              # JavaScript logic
└── README.md           # This file
```

### Customization

**Change Colors:**
Edit CSS variables in `styles.css`:
```css
:root {
    --primary-color: #0071e3;
    --secondary-color: #f1f3f5;
    /* ... */
}
```

**Add New Endpoints:**
1. Add HTML form in `index.html`
2. Add JavaScript function in `app.js`
3. Call `makeRequest()` function

**Example:**
```javascript
async function testNewEndpoint() {
    try {
        const data = await makeRequest('/new-endpoint');
        displayResult('resultElementId', data);
    } catch (error) {
        displayResult('resultElementId', `Error: ${error.message}`, true);
    }
}
```

## API Reference

For complete API documentation, see:
- `API_ENDPOINTS_COMPLETE.md` - Full API reference
- `CURL_EXAMPLES.md` - cURL examples

## Support

### Common Issues

1. **API not responding**
   - Check backend server is running
   - Check API URL configuration
   - Check network connectivity

2. **WebSocket not connecting**
   - Check WebSocket server is running
   - Check WebSocket URL configuration
   - Check firewall settings

3. **Image upload failing**
   - Check file size
   - Check file format
   - Check user ID

### Getting Help

1. Check browser console for errors (F12)
2. Review API documentation
3. Check backend logs
4. Verify configuration settings

## License

MIT License - Feel free to use and modify

## Version

- **Version:** 1.0.0
- **Last Updated:** 2024-01-23
- **Status:** Production Ready

## Features Roadmap

### Phase 2
- [ ] Dark mode toggle
- [ ] Request history
- [ ] Saved requests
- [ ] Export results
- [ ] API documentation sidebar

### Phase 3
- [ ] GraphQL support
- [ ] Advanced filtering
- [ ] Batch operations
- [ ] Performance monitoring
- [ ] Analytics dashboard

## Contributing

To contribute improvements:
1. Test thoroughly
2. Follow existing code style
3. Update documentation
4. Submit pull request

## Changelog

### v1.0.0 (2024-01-23)
- Initial release
- All 22 API endpoints supported
- WebSocket testing
- Chat interface
- Settings management
- Responsive design

---

**Happy Testing! 🚀**
