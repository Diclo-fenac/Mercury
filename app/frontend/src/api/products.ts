import apiClient from './client'

export interface Product {
  id: string
  title: string
  description?: string
  brand?: string
  category?: string
  sub_category?: string
  price?: { amount: number; currency: string; original?: number }
  rating?: number
  stock?: string
  images?: string[]
  tags?: Record<string, any>
  availability?: Array<{ store_id: string; in_stock: boolean }>
  score?: number
  breakdown?: {
    keyword_score: number
    semantic_score: number
    rrf_score: number
    personalization_boost: number
  }
}

export interface SearchResult {
  query: string
  results: Product[]
  total_results: number
  facets?: Record<string, Record<string, number>>
  meta?: {
    latency_ms: number
    cache_hit: boolean
    search_mode: string
  }
  search_metadata?: {
    search_type: string
    suggestions?: string[]
  }
}

export interface SearchRequest {
  query: string
  filters?: {
    price?: { min?: number; max?: number }
    category?: string[]
    brand?: string[]
    rating?: number
    sub_category?: string[]
    stock_only?: boolean
    online_available?: boolean
  }
  sort?: { by: 'relevance' | 'price' | 'rating' | 'discount' | 'newest'; order: 'asc' | 'desc' }
  pagination?: { page: number; limit: number }
  user_id?: string
  search_type?: 'hybrid' | 'keyword' | 'semantic'
  include_suggestions?: boolean
}

export const productsApi = {
  search: (request: SearchRequest): Promise<SearchResult> =>
    apiClient.post('/products/search', request).then((res) => res.data),
  
  getTrending: (category?: string, days = 7, page = 1, limit = 20) =>
    apiClient.get('/products/trending', { params: { category, days, page, limit } }).then((res) => res.data),
  
  getDeals: (category?: string, minDiscount = 20, page = 1, limit = 20) =>
    apiClient.get('/products/deals', { params: { category, minDiscount, page, limit } }).then((res) => res.data),
  
  getFlashDeals: (page = 1, limit = 20) =>
    apiClient.get('/products/flash-deals', { params: { page, limit } }).then((res) => res.data),
  
  getById: (id: string, user_id?: string) =>
    apiClient.get(`/products/${id}`, { params: { user_id } }).then((res) => res.data),
  
  getRecommendations: (id: string, type: 'similar' | 'complementary' | 'substitute' | 'variant' = 'similar', page = 1, limit = 10) =>
    apiClient.get(`/products/${id}/recommendations`, { params: { recommendation_type: type, page, limit } }).then((res) => res.data),
  
  getSuggestions: (query: string, limit = 10) =>
    apiClient.get('/products/search/suggestions', { params: { q: query, limit } }).then((res) => res.data),
}
