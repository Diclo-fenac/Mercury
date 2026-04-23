import apiClient from './client'

export interface Message {
  role: 'system' | 'user' | 'assistant' | 'tool'
  content?: string
  name?: string
  tool_calls?: Array<Record<string, any>>
  tool_call_id?: string
}

export interface ChatRequest {
  model_version?: string
  messages: Message[]
  conversation_id?: string
  stream?: boolean
  temperature?: number
  max_tokens?: number
  context_config?: {
    max_history_messages?: number
    enable_memory?: boolean
    summarize_threshold?: number
  }
  tools?: Array<Record<string, any>>
  image_data?: string
  user_id: string
}

export interface ChatResponse {
  success: boolean
  response: string
  conversation_id: string
  message_id: string
  user_message_id?: string
  personalization_reason?: string
  language_info?: Record<string, string>
  cache_stats?: Record<string, any>
  features_used?: Record<string, boolean>
}

export interface ToolRequest {
  operation: 'discover' | 'execute'
  tool_name?: string
  parameters?: Record<string, any>
  user_id?: string
}

export interface ToolResponse {
  success: boolean
  tools?: Array<{ name: string; description: string; parameters: Record<string, any> }>
  result?: any
}

export const chatApi = {
  complete: (request: ChatRequest): Promise<ChatResponse> =>
    apiClient.post('/chat/completions', request).then((res) => res.data),
  
  stream: (request: ChatRequest): Promise<EventSource> => {
    return new Promise((resolve, reject) => {
      const token = localStorage.getItem('auth_token')
      const headers: Record<string, string> = {}
      if (token) headers['Authorization'] = `Bearer ${token}`
      
      const eventSource = new EventSource(
        `${import.meta.env.VITE_API_URL || '/api'}/chat/stream`,
        { headers }
      )
      
      let responseText = ''
      
      eventSource.onmessage = (event) => {
        if (event.data === '[DONE]') {
          eventSource.close()
          resolve(eventSource)
        } else {
          try {
            const data = JSON.parse(event.data)
            responseText += data.response || ''
          } catch (e) {
            // Ignore non-JSON messages
          }
        }
      }
      
      eventSource.onerror = (error) => {
        eventSource.close()
        reject(error)
      }
    })
  },
  
  getTools: (operation: 'discover' | 'execute', toolName?: string, parameters?: Record<string, any>) =>
    apiClient.post('/chat/tools', { operation, tool_name: toolName, parameters }).then((res) => res.data),
  
  getHistory: (conversationId: string, page = 1, limit = 50) =>
    apiClient.get(`/chat/history/${conversationId}`, { params: { page, limit } }).then((res) => res.data),
}
