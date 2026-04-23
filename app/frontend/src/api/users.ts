import apiClient from './client'

export interface UserProfile {
  user_id: string
  preferences?: Record<string, any>
  activity_summary?: Record<string, any>
  created_at?: string
  last_active?: string
}

export interface UserResponse {
  success: boolean
  profile: UserProfile
}

export interface RecommendationsResponse {
  user_id: string
  recommendations: Array<{
    id: string
    title: string
    description?: string
    price?: { amount: number; currency: string }
    rating?: number
    images?: string[]
  }>
  personalized: boolean
  category?: string
  personalization_type?: string
  strategies_used?: string[]
}

export const usersApi = {
  getProfile: (userId: string) =>
    apiClient.get(`/users/${userId}/profile`).then((res) => res.data),
  
  getRecommendations: (userId: string, category?: string, page = 1, limit = 20) =>
    apiClient.get(`/users/${userId}/recommendations`, { params: { category, page, limit } }).then((res) => res.data),
  
  getPreferences: (userId: string) =>
    apiClient.get(`/users/${userId}/preferences`).then((res) => res.data),
  
  updatePreferences: (userId: string, preferences: Record<string, any>) =>
    apiClient.put(`/users/${userId}/preferences`, { preferences }).then((res) => res.data),
}
