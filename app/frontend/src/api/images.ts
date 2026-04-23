import apiClient from './client'

export interface ImageAnalysis {
  description: string
  is_barcode: boolean
  barcode_data?: string
  barcode_type?: string
  confidence_score?: number
}

export interface ImageUploadResponse {
  success: boolean
  image_id: string
  image_url: string
  analysis: ImageAnalysis
  product_data?: {
    id: string
    title: string
    description?: string
    price?: { amount: number; currency: string }
    images?: string[]
  }
}

export interface ImageSearchRequest {
  image_id?: string
  image_data?: string
  prompt: string
  search_type?: 'exact_match' | 'similar_style' | 'exact_and_similar'
  limit?: number
}

export interface ImageSearchResponse {
  success: boolean
  results: Array<{
    id: string
    title: string
    description?: string
    price?: { amount: number; currency: string }
    images?: string[]
    score?: number
  }>
  search_type: string
  total: number
  image_analysis?: {
    description: string
    confidence: number
  }
}

export const imagesApi = {
  upload: (imageData: string, message?: string, conversationId?: string) => {
    const request = { image_data: imageData, message, conversation_id: conversationId }
    return apiClient.post('/images/', request).then((res) => res.data)
  },
  
  getById: (id: string) =>
    apiClient.get(`/images/${id}`).then((res) => res.data),
  
  search: (request: ImageSearchRequest) =>
    apiClient.post('/images/search', request).then((res) => res.data),
}
