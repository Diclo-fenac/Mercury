import { useState, useCallback, useRef } from 'react'
import { chatApi, ChatRequest, ChatResponse, Message } from '../api/chat'
import { useChatStore } from '../context/ChatContext'

export const useChat = () => {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { messages, addMessage, currentConversationId, addConversation } = useChatStore()
  const eventSourceRef = useRef<EventSource | null>(null)

  const sendMessage = useCallback(async (content: string, userId: string) => {
    setLoading(true)
    setError(null)

    const userMessage: Message = {
      role: 'user',
      content,
    }

    addMessage({
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date(),
      conversationId: currentConversationId || undefined,
    })

    const request: ChatRequest = {
      messages: [userMessage],
      conversation_id: currentConversationId || undefined,
      user_id: userId,
    }

    try {
      const response = await chatApi.complete(request)
      
      addMessage({
        id: response.message_id,
        role: 'assistant',
        content: response.response,
        timestamp: new Date(),
        conversationId: response.conversation_id,
      })

      if (!currentConversationId) {
        addConversation(
          response.conversation_id,
          content.slice(0, 30) + (content.length > 30 ? '...' : ''),
          response.response
        )
      }

      return response
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Chat failed')
      return null
    } finally {
      setLoading(false)
    }
  }, [currentConversationId, addMessage, addConversation])

  const streamMessage = useCallback(async (content: string, userId: string, onChunk: (text: string) => void) => {
    setLoading(true)
    setError(null)

    const userMessage: Message = {
      role: 'user',
      content,
    }

    addMessage({
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date(),
      conversationId: currentConversationId || undefined,
    })

    const request: ChatRequest = {
      messages: [userMessage],
      conversation_id: currentConversationId || undefined,
      user_id: userId,
      stream: true,
    }

    try {
      const eventSource = await chatApi.stream(request)
      eventSourceRef.current = eventSource

      let fullResponse = ''
      let messageBuffer = ''

      eventSource.onmessage = (event) => {
        if (event.data === '[DONE]') {
          eventSource.close()
          eventSourceRef.current = null
          setLoading(false)

          if (fullResponse) {
            addMessage({
              id: Date.now().toString(),
              role: 'assistant',
              content: fullResponse,
              timestamp: new Date(),
              conversationId: currentConversationId || undefined,
            })
          }
        } else {
          try {
            const data = JSON.parse(event.data)
            const chunk = data.response || ''
            fullResponse += chunk
            messageBuffer += chunk
            onChunk(chunk)
          } catch (e) {
            // Ignore non-JSON messages
          }
        }
      }

      eventSource.onerror = (error) => {
        eventSource.close()
        eventSourceRef.current = null
        setLoading(false)
        setError('Stream failed')
      }
    } catch (err) {
      setLoading(false)
      setError(err instanceof Error ? err.message : 'Stream failed')
    }
  }, [currentConversationId, addMessage])

  const stopStreaming = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
      setLoading(false)
    }
  }, [])

  const reset = useCallback(() => {
    setLoading(false)
    setError(null)
    stopStreaming()
  }, [stopStreaming])

  return { loading, error, sendMessage, streamMessage, stopStreaming, reset }
}
