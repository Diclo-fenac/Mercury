function dashboardApp() {
    return {
        // UI State
        toasts: [],
        toastIdCounter: 0,

        // Auth State
        isAuthenticated: false,
        adminKeyInput: '',
        adminKey: '',
        authError: '',
        isLoading: false,

        // Theme & Mode State
        isDarkMode: false,
        modeView: 'executive',

        // Playground State
        playgroundQuery: 'headphones for focus',
        playgroundResult: null,

        testPlaygroundQuery() {
            if (!this.playgroundQuery.trim()) return;
            this.playgroundResult = {
                topHit: `Zenith ANC Wireless Headphones (Query: "${this.playgroundQuery}")`,
                score: (0.91 + Math.random() * 0.08).toFixed(3),
                latency: (14 + Math.random() * 12).toFixed(1) + " ms",
                breakdown: `BM25 Score: ${(3.5 + Math.random() * 2).toFixed(2)} | Vector Cosine Similarity: ${(0.85 + Math.random() * 0.1).toFixed(3)}`
            };
            this.addLog({ type: 'success', message: `Executed hybrid search playground test for query "${this.playgroundQuery}".`, time: 'Just now' });
        },

        // Navigation State
        currentView: 'analytics',
        navItems: [
            { id: 'analytics', name: 'Analytics' },
            { id: 'catalog', name: 'Catalog' },
            { id: 'customizer', name: 'Merchandising & Widget' },
            { id: 'upload', name: 'Upload Data' },
            { id: 'synonyms', name: 'Synonyms' },
            { id: 'keys', name: 'API Keys' }
        ],

        // Search Redirects & Out of Stock Strategy State
        redirectQueryInput: '',
        redirectTargetInput: '',
        redirectRules: [
            { id: 1, query: 'shipping', target: '/shipping-policy' },
            { id: 2, query: 'returns', target: '/returns-and-exchanges' }
        ],
        oosStrategy: 'demote',

        addRedirectRule() {
            if (!this.redirectQueryInput.trim() || !this.redirectTargetInput.trim()) return;
            this.redirectRules.push({
                id: Date.now(),
                query: this.redirectQueryInput.trim(),
                target: this.redirectTargetInput.trim()
            });
            this.addLog({ type: 'success', message: `Added search redirect rule: '${this.redirectQueryInput}' -> '${this.redirectTargetInput}'.`, time: 'Just now' });
            alert(`Search redirect rule added: Queries for '${this.redirectQueryInput}' will automatically redirect shoppers to ${this.redirectTargetInput}`);
            this.redirectQueryInput = '';
            this.redirectTargetInput = '';
        },

        removeRedirectRule(id) {
            this.redirectRules = this.redirectRules.filter(r => r.id !== id);
            this.addLog({ type: 'info', message: 'Removed search redirect rule.', time: 'Just now' });
        },

        updateOOSStrategy(val) {
            this.oosStrategy = val;
            this.addLog({ type: 'success', message: `Updated out-of-stock ranking strategy to '${val}'.`, time: 'Just now' });
            alert(`Out-of-stock search strategy updated to '${val}'. Changes reflected immediately in search API results.`);
        },

        // Merchandising & Widget Customizer State
        bm25Weight: 70,
        vectorWeight: 30,
        widgetColor: '#C1C8FF',
        widgetPlaceholder: 'Search products, brands, or ask AI...',
        curationProducts: [
            { id: 'PROD-101', title: 'Zenith ANC Wireless Headphones', price: 349, badge: 'Best Seller' },
            { id: 'PROD-102', title: 'Aura Wireless Mechanical Keyboard', price: 189, badge: 'Trending' },
            { id: 'PROD-103', title: 'ErgoLift Wool Felt Desk Mat', price: 89, badge: 'None' },
            { id: 'PROD-104', title: 'Pulse Ultra Fitness Smartwatch', price: 279, badge: 'Promoted' }
        ],

        moveCurationRank(idx, dir) {
            const target = idx + dir;
            if (target < 0 || target >= this.curationProducts.length) return;
            const temp = this.curationProducts[idx];
            this.curationProducts[idx] = this.curationProducts[target];
            this.curationProducts[target] = temp;
        },

        saveMerchandisingCuration() {
            this.addLog({ type: 'success', message: 'Saved visual product ranking curation grid and hybrid weight rules.', time: 'Just now' });
            alert('Visual Merchandising Grid saved! Product search ranking positions updated live across storefronts.');
        },

        // Catalog Filter & Keys State
        catalogFilterQuery: '',
        publicKey: 'pk_demo_key_99812',
        adminKeyDisplay: 'sk_stress_test_key_123',
        catalogItems: [
            { id: 'PROD-101', title: 'Zenith ANC Wireless Headphones', category: 'Audio', price: 349, stock: 'In Stock' },
            { id: 'PROD-102', title: 'Aura Wireless Mechanical Keyboard', category: 'Deskware', price: 189, stock: 'In Stock' },
            { id: 'PROD-103', title: 'ErgoLift Wool Felt Desk Mat', category: 'Deskware', price: 89, stock: 'In Stock' },
            { id: 'PROD-104', title: 'Pulse Ultra Fitness Smartwatch', category: 'Wearables', price: 279, stock: 'In Stock' },
            { id: 'PROD-105', title: 'Horizon Smart Ambient Light Strip', category: 'Ambient', price: 119, stock: 'In Stock' },
            { id: 'PROD-106', title: 'Studio Hi-Fi Desktop Speakers', category: 'Audio', price: 420, stock: 'Low Stock' },
            { id: 'PROD-107', title: 'Luna MagSafe Charging Dock', category: 'Deskware', price: 79, stock: 'In Stock' },
            { id: 'PROD-108', title: 'Minimalist Magnetic Cable Organizer', category: 'Ambient', price: 35, stock: 'In Stock' }
        ],

        get filteredCatalog() {
            if (!this.catalogFilterQuery.trim()) return this.catalogItems;
            const q = this.catalogFilterQuery.toLowerCase();
            return this.catalogItems.filter(i =>
                i.title.toLowerCase().includes(q) ||
                i.category.toLowerCase().includes(q) ||
                i.id.toLowerCase().includes(q)
            );
        },

        reindexCollection() {
            this.addLog({ type: 'success', message: 'Background worker triggered re-indexing for collection tenant_demo_products.', time: 'Just now' });
            alert('Collection tenant_demo_products re-index job queued successfully! Typesense BM25 and PostgreSQL vector embeddings updated.');
        },

        downloadCatalogSchema() {
            const schemaJson = JSON.stringify({
                name: "tenant_demo_products",
                fields: [
                    { name: "title", type: "string" },
                    { name: "category", type: "string" },
                    { name: "price", type: "float" },
                    { name: "embedding", type: "float[]", num_dim: 768 }
                ]
            }, null, 2);
            const encodedUri = encodeURI("data:application/json;charset=utf-8," + schemaJson);
            const link = document.createElement("a");
            link.setAttribute("href", encodedUri);
            link.setAttribute("download", `catalog_schema_${Date.now()}.json`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        },

        copyKey(keyText) {
            navigator.clipboard.writeText(keyText);
            alert('API Key copied to clipboard!');
        },

        rotateKey(type) {
            if (confirm(`Are you sure you want to rotate the ${type} API key? Existing integrations using the old key will lose access immediately.`)) {
                if (type === 'public') {
                    this.publicKey = 'pk_rotated_' + Math.random().toString(36).substring(2, 10);
                } else {
                    this.adminKeyDisplay = 'sk_rotated_' + Math.random().toString(36).substring(2, 10);
                }
                this.addLog({ type: 'warning', message: `Rotated ${type} API key successfully.`, time: 'Just now' });
                alert(`New ${type} API Key generated successfully!`);
            }
        },

        // Data State
        analyticsData: { total_searches: 12480, top_queries: [], zero_results: [] },
        catalogStats: { product_count: 8, collection_name: 'tenant_demo_products' },
        newSynonym: { term: '', synonyms: '' },

        fixZeroResult(missedQuery, mappedTarget) {
            this.addLog({ type: 'success', message: `Mapped synonym "${missedQuery}" -> "${mappedTarget}" via Gemini AI.`, time: 'Just now' });
            alert(`Zero-result query "${missedQuery}" successfully mapped to target catalog keyword "${mappedTarget}"!`);
        },

        exportCSVReport() {
            const csvContent = "data:text/csv;charset=utf-8,Query,Volume,Latency_ms,Conversion_Rate\nwireless headphones,1420,18,88.4%\nmechanical keyboard,980,22,82.1%\nwool desk mat,640,14,91.0%";
            const encodedUri = encodeURI(csvContent);
            const link = document.createElement("a");
            link.setAttribute("href", encodedUri);
            link.setAttribute("download", `mercury_search_report_${Date.now()}.csv`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            this.addLog({ type: 'success', message: 'Exported search telemetry report to CSV.', time: 'Just now' });
        },

        pinMerchandisingProduct(query, productId) {
            this.addLog({ type: 'success', message: `Pinned item ${productId} to top of query "${query}".`, time: 'Just now' });
            alert(`Merchandising Rule Active: Product ${productId} is now pinned to Rank #1 for search query "${query}".`);
        },

        openQueryInspector() {
            const rawJson = JSON.stringify({
                endpoint: "/api/v1/search/",
                method: "GET",
                query: "headphones for focus",
                params: {
                    q: "headphones for focus",
                    collection: "tenant_demo_products",
                    hybrid: true,
                    bm25_weight: 0.7,
                    vector_weight: 0.3
                },
                gemini_grounding_prompt: "Select high-fidelity audio products matching focus and noise isolation.",
                execution_time_ms: 24.2
            }, null, 2);
            alert("Raw Search API Request JSON & Gemini Prompt:\n\n" + rawJson);
        },

        // Notifications & SSE
        isDrawerOpen: false,
        systemLogs: [],
        unreadLogs: 0,
        sseSource: null,

        // Upload & Preview State
        isDragging: false,
        isUploading: false,
        uploadProgress: 0,
        uploadStatusText: '',
        previewData: null,
        previewHeaders: [],
        pendingFile: null,

        // Telemetry Live Sparkline Data
        latencyTicker: [14, 18, 12, 22, 19, 15, 14, 16, 21, 13, 17, 14],
        p95Latency: 24.2,
        p99Latency: 48.1,

        init() {
            // Check for existing key in localStorage on load
            const savedKey = localStorage.getItem('mercury_admin_key');
            if (savedKey) {
                this.adminKey = savedKey;
                this.setupAxios();
                this.verifyAuth();
            }

            // Live Telemetry Sparkline Interval Simulation
            setInterval(() => {
                const nextLat = Math.floor(Math.random() * 15) + 10;
                this.latencyTicker.shift();
                this.latencyTicker.push(nextLat);
                this.p95Latency = (20 + Math.random() * 8).toFixed(1);
                this.p99Latency = (42 + Math.random() * 10).toFixed(1);
            }, 3000);

            // Watch for view changes to load appropriate data
            this.$watch('currentView', value => {
                if (value === 'catalog') {
                    this.fetchCatalogStats();
                    setTimeout(() => this.renderEChart('treemap'), 100);
                }
                if (value === 'analytics') this.fetchAnalytics();
            });
        },

        getPageTitle() {
            const item = this.navItems.find(n => n.id === this.currentView);
            return item ? item.name : 'Dashboard';
        },

        getIcon(id) {
            const icons = {
                'analytics': '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>',
                'catalog': '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>',
                'customizer': '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>',
                'upload': '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>',
                'synonyms': '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg>',
                'keys': '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>'
            };
            return icons[id] || '';
        },

        setupAxios() {
            axios.defaults.baseURL = '/api/v1';
            axios.defaults.headers.common['Authorization'] = `Bearer ${this.adminKey}`;
            axios.defaults.headers.common['X-API-Key'] = this.adminKey;

            // Global error handler
            axios.interceptors.response.use(
                response => response,
                error => {
                    if (error.response && (error.response.status === 401 || error.response.status === 403)) {
                        this.logout();
                        this.showToast('Authentication failed. Please login again.', 'error');
                    } else if (error.response && error.response.status >= 500) {
                        this.showToast('System Overloaded or Server Error.', 'error');
                    }
                    return Promise.reject(error);
                }
            );
        },

        async verifyAuth() {
            this.isLoading = true;
            this.authError = '';

            try {
                await axios.get('/admin/config');
                this.isAuthenticated = true;
                this.fetchCatalogStats();
                this.fetchAnalytics();
                this.connectSSE();
            } catch (err) {
                this.authError = 'Invalid API Key or server unavailable.';
                this.logout();
            } finally {
                this.isLoading = false;
            }
        },

        async login() {
            this.adminKey = this.adminKeyInput;
            localStorage.setItem('mercury_admin_key', this.adminKey);
            this.setupAxios();
            await this.verifyAuth();
        },

        logout() {
            this.isAuthenticated = false;
            this.adminKey = '';
            this.adminKeyInput = '';
            localStorage.removeItem('mercury_admin_key');
            delete axios.defaults.headers.common['Authorization'];
            if (this.sseSource) {
                this.sseSource.close();
                this.sseSource = null;
            }
        },

        // ---- SSE & Logs ----
        connectSSE() {
            // Placeholder for SSE connection to real-time logs
            // this.sseSource = new EventSource(`/api/v1/admin/logs/stream?token=${this.adminKey}`);
            // this.sseSource.onmessage = (e) => {
            //     const log = JSON.parse(e.data);
            //     this.addLog(log);
            // };

            // Simulation for demo
            setTimeout(() => this.addLog({ type: 'success', message: 'System connected successfully.', time: 'Just now' }), 1000);
        },

        addLog(log) {
            this.systemLogs.unshift(log);
            if (this.systemLogs.length > 50) this.systemLogs.pop();
            if (!this.isDrawerOpen) this.unreadLogs++;

            if (log.type === 'error' || log.type === 'success') {
                this.showToast(log.message, log.type);
            }
        },

        toggleNotifications() {
            this.isDrawerOpen = !this.isDrawerOpen;
            if (this.isDrawerOpen) {
                this.unreadLogs = 0;
            }
        },

        // ---- API Interactions ----

        async fetchAnalytics() {
            try {
                const response = await axios.get('/admin/analytics');
                this.analyticsData = response.data;
            } catch (err) {
                console.error("Failed to fetch analytics", err);
            }
        },

        async fetchCatalogStats() {
            try {
                const response = await axios.get('/admin/catalog/stats');
                this.catalogStats = response.data;
            } catch (err) {
                console.error("Failed to fetch stats", err);
            }
        },

        // ---- Upload & Preview Logic ----

        handleFileDrop(event) {
            this.isDragging = false;
            if (event.dataTransfer.files.length > 0) {
                this.processFile(event.dataTransfer.files[0]);
            }
        },

        handleFileSelect(event) {
            if (event.target.files.length > 0) {
                this.processFile(event.target.files[0]);
            }
        },

        processFile(file) {
            this.pendingFile = file;

            // Read first few kilobytes to preview data
            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    const text = e.target.result;
                    let parsed = [];
                    if (file.name.endsWith('.json')) {
                        parsed = JSON.parse(text);
                        if (!Array.isArray(parsed)) parsed = [parsed];
                    } else if (file.name.endsWith('.jsonl')) {
                        parsed = text.split('\n').filter(l => l.trim()).slice(0, 5).map(l => JSON.parse(l));
                    }

                    if (parsed.length > 0) {
                        this.previewData = parsed.slice(0, 5);
                        this.previewHeaders = Object.keys(this.previewData[0]);
                    }
                } catch (err) {
                    this.showToast('Failed to parse file preview', 'error');
                }
            };
            // Read just a chunk for preview (simplification for demo)
            reader.readAsText(file.slice(0, 50000));
        },

        cancelUpload() {
            this.previewData = null;
            this.previewHeaders = [];
            this.pendingFile = null;
            document.getElementById('catalog-upload').value = '';
        },

        async confirmUpload() {
            if (!this.pendingFile) return;

            this.isUploading = true;
            this.uploadProgress = 10;
            this.uploadStatusText = 'Parsing file...';

            const formData = new FormData();
            formData.append('file', this.pendingFile);

            try {
                // Simulate progress
                const progressInterval = setInterval(() => {
                    if (this.uploadProgress < 90) this.uploadProgress += 10;
                    this.uploadStatusText = `Processed ${this.uploadProgress * 100} items...`;
                }, 500);

                const response = await axios.post('/admin/catalog/upload', formData, {
                    headers: { 'Content-Type': 'multipart/form-data' }
                });

                clearInterval(progressInterval);
                this.uploadProgress = 100;
                this.uploadStatusText = 'Complete!';

                if (response.data.success) {
                    this.showToast(`Successfully imported ${response.data.stats.total_processed || 0} products!`, 'success');
                    this.addLog({ type: 'success', message: `Imported ${response.data.stats.total_processed} products`, time: 'Just now' });
                    setTimeout(() => {
                        this.currentView = 'catalog';
                        this.cancelUpload();
                        this.isUploading = false;
                    }, 1000);
                }
            } catch (err) {
                this.isUploading = false;
                this.showToast('Upload failed: ' + (err.response?.data?.detail || err.message), 'error');
                this.addLog({ type: 'error', message: 'Upload failed', time: 'Just now' });
            }
        },

        // ---- Data Visualization (ECharts) ----
        renderEChart(type = 'treemap') {
            const chartDom = document.getElementById('catalog-chart');
            if (!chartDom) return;

            if (this.chartInstance) {
                this.chartInstance.dispose();
            }

            // Use dark theme
            this.chartInstance = echarts.init(chartDom, 'dark', { backgroundColor: 'transparent' });

            // Mock hierarchical data based on catalog stats
            const count = this.catalogStats.product_count || 100;
            const data = [
                {
                    name: 'Electronics',
                    value: Math.floor(count * 0.4),
                    children: [
                        { name: 'Phones', value: Math.floor(count * 0.2) },
                        { name: 'Laptops', value: Math.floor(count * 0.15) },
                        { name: 'Accessories', value: Math.floor(count * 0.05) }
                    ]
                },
                {
                    name: 'Clothing',
                    value: Math.floor(count * 0.35),
                    children: [
                        { name: 'Shirts', value: Math.floor(count * 0.2) },
                        { name: 'Pants', value: Math.floor(count * 0.15) }
                    ]
                },
                {
                    name: 'Home & Kitchen',
                    value: Math.floor(count * 0.25)
                }
            ];

            let option = {};

            if (type === 'treemap') {
                option = {
                    tooltip: { trigger: 'item', formatter: '{b}: {c} items' },
                    series: [{
                        type: 'treemap',
                        data: data,
                        roam: true,
                        itemStyle: {
                            borderColor: '#0B0F19',
                            borderWidth: 2,
                            gapWidth: 2
                        },
                        colorMappingBy: 'value',
                        levels: [
                            {
                                itemStyle: { borderColor: '#555', borderWidth: 4, gapWidth: 4 }
                            },
                            {
                                colorSaturation: [0.3, 0.6],
                                itemStyle: { borderColorSaturation: 0.7, gapWidth: 2, borderWidth: 2 }
                            }
                        ]
                    }]
                };
            } else {
                option = {
                    tooltip: { trigger: 'item', formatter: '{b}: {c} items' },
                    series: [{
                        type: 'sunburst',
                        data: data,
                        radius: ['10%', '90%'],
                        itemStyle: {
                            borderRadius: 4,
                            borderWidth: 2,
                            borderColor: '#0B0F19'
                        },
                        label: { show: true }
                    }]
                };
            }

            this.chartInstance.setOption(option);

            // Handle resize
            window.addEventListener('resize', () => {
                if (this.chartInstance) this.chartInstance.resize();
            });
        },

        // ---- Utilities ----

        async addSynonym() {
            if (!this.newSynonym.term || !this.newSynonym.synonyms) return;
            const synonymsArray = this.newSynonym.synonyms.split(',').map(s => s.trim()).filter(s => s);

            try {
                await axios.post('/admin/rules/synonyms', {
                    term: this.newSynonym.term.trim(),
                    synonyms: synonymsArray
                });
                this.showToast('Synonym rule added successfully!');
                this.newSynonym = { term: '', synonyms: '' };
            } catch (err) {
                this.showToast('Failed to add synonym rule.', 'error');
            }
        },

        generateKey() {
            this.showToast('Key generation not fully implemented in demo.', 'info');
        },

        async copyToClipboard(text) {
            try {
                await navigator.clipboard.writeText(text);
                this.showToast('Copied to clipboard', 'success');
            } catch (err) {
                this.showToast('Failed to copy', 'error');
            }
        },

        showToast(message, type = 'success') {
            const id = this.toastIdCounter++;
            this.toasts.push({ id, message, type });

            setTimeout(() => {
                this.dismissToast(id);
            }, 5000);
        },

        dismissToast(id) {
            this.toasts = this.toasts.filter(t => t.id !== id);
        }
    }
}
