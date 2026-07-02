function dashboardApp() {
    return {
        // Auth State
        isAuthenticated: false,
        adminKeyInput: '',
        adminKey: '',
        authError: '',
        isLoading: false,
        isUploading: false,
        
        // Navigation State
        currentView: 'analytics',
        navItems: [
            { id: 'analytics', name: 'Analytics' },
            { id: 'catalog', name: 'Catalog' },
            { id: 'synonyms', name: 'Synonyms' },
            { id: 'keys', name: 'API Keys' }
        ],
        
        // Data State
        analyticsData: { total_searches: 0, top_queries: [], zero_results: [] },
        catalogStats: { product_count: 0, collection_name: null },
        newSynonym: { term: '', synonyms: '' },
        
        // Toast Notification State
        toast: { visible: false, message: '', type: 'success' },

        init() {
            // Check for existing key in localStorage on load
            const savedKey = localStorage.getItem('mercury_admin_key');
            if (savedKey) {
                this.adminKey = savedKey;
                this.setupAxios();
                this.verifyAuth();
            }
            
            // Watch for view changes to load appropriate data
            this.$watch('currentView', value => {
                if (value === 'catalog') this.fetchCatalogStats();
                if (value === 'analytics') this.fetchAnalytics();
            });
        },

        setupAxios() {
            axios.defaults.baseURL = '/api/v1';
            axios.defaults.headers.common['Authorization'] = `Bearer ${this.adminKey}`;
            
            // Global error handler
            axios.interceptors.response.use(
                response => response,
                error => {
                    if (error.response && (error.response.status === 401 || error.response.status === 403)) {
                        this.logout();
                        this.showToast('Authentication failed. Please login again.', 'error');
                    }
                    return Promise.reject(error);
                }
            );
        },

        async verifyAuth() {
            this.isLoading = true;
            this.authError = '';
            
            try {
                // Try hitting a protected endpoint to verify the key
                await axios.get('/admin/config');
                this.isAuthenticated = true;
                this.fetchCatalogStats();
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
        
        async uploadCatalog(event) {
            const file = event.target.files[0];
            if (!file) return;
            
            this.isUploading = true;
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                const response = await axios.post('/admin/catalog/upload', formData, {
                    headers: { 'Content-Type': 'multipart/form-data' }
                });
                
                if (response.data.success) {
                    this.showToast(`Successfully imported ${response.data.stats.total_processed || 0} products!`);
                    this.fetchCatalogStats();
                } else {
                    this.showToast('Upload failed to process completely.', 'error');
                }
            } catch (err) {
                this.showToast('Upload failed: ' + (err.response?.data?.detail || err.message), 'error');
            } finally {
                this.isUploading = false;
                event.target.value = ''; // reset input
            }
        },
        
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

        // ---- Utilities ----
        
        async copyToClipboard(text) {
            try {
                await navigator.clipboard.writeText(text);
                this.showToast('Copied to clipboard');
            } catch (err) {
                this.showToast('Failed to copy', 'error');
            }
        },
        
        showToast(message, type = 'success') {
            this.toast.message = message;
            this.toast.type = type;
            this.toast.visible = true;
            
            setTimeout(() => {
                this.toast.visible = false;
            }, 3000);
        }
    }
}
