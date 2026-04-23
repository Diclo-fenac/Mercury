import { create } from 'zustand'

interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  conversationId?: string
}

interface ChatState {
  messages: Message[]
  currentConversationId: string | null
  conversations: { id: string; title: string; lastMessage: string }[]
  addMessage: (message: Message) => void
  setMessages: (messages: Message[]) => void
  setCurrentConversation: (id: string | null) => void
  addConversation: (id: string, title: string, lastMessage: string) => void
  getMessagesByConversation: (id: string) => Message[]
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  currentConversationId: null,
  conversations: [],
  addMessage: (message) =>
    set((state) => ({
      messages: [...state.messages, message],
    })),
  setMessages: (messages) => set({ messages }),
  setCurrentConversation: (id) => set({ currentConversationId: id }),
  addConversation: (id, title, lastMessage) =>
    set((state) => ({
      conversations: [
        { id, title, lastMessage },
        ...state.conversations,
      ],
    })),
  getMessagesByConversation: (id) => {
    const state = get()
    return state.messages.filter((m) => m.conversationId === id)
  },
}))
