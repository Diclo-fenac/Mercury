import apiClient from './client'

export interface ConversationSummary {
  conversation_id: string
  title?: string
  last_message?: string
  message_count: number
  created_at: string
  updated_at: string
  archived: boolean
}

export interface ConversationDetail {
  conversation_id: string
  title?: string
  messages: Array<{
    message_id: string
    user_id: string
    message: string
    message_type: string
    timestamp: string
    metadata?: Record<string, any>
  }>
  created_at: string
  updated_at: string
  archived: boolean
  metadata?: Record<string, any>
}

export interface CreateConversationRequest {
  title?: string
  metadata?: Record<string, any>
  user_id?: string
}

export interface ConversationListResponse {
  conversations: ConversationSummary[]
  total: number
  pagination: {
    page: number
    per_page: number
    total: number
    pages: number
  }
}

export const conversationsApi = {
  list: (userId?: string, page = 1, limit = 20) =>
    apiClient.get('/conversations/', { params: { user_id: userId, page, limit } }).then((res) => res.data),
  
  getById: (id: string) =>
    apiClient.get(`/conversations/${id}`).then((res) => res.data),
  
  create: (request: CreateConversationRequest) =>
    apiClient.post('/conversations/', request).then((res) => res.data),
  
  delete: (id: string) =>
    apiClient.delete(`/conversations/${id}`).then((res) => res.data),
}
