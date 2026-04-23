import { useState, useCallback } from 'react'
import { productsApi, SearchRequest, SearchResult, Product } from '../api/products'

export const useSearch = () => {
  const [results, setResults] = useState<SearchResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [suggestions, setSuggestions] = useState<string[]>([])

  const search = useCallback(async (request: SearchRequest) => {
    setLoading(true)
    setError(null)
    try {
      const data = await productsApi.search(request)
      setResults(data)
      return data
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed')
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  const getSuggestions = useCallback(async (query: string, limit = 10) => {
    try {
      const data = await productsApi.getSuggestions(query, limit)
      setSuggestions(data.suggestions || [])
      return data.suggestions
    } catch (err) {
      return []
    }
  }, [])

  const reset = useCallback(() => {
    setResults(null)
    setSuggestions([])
    setError(null)
  }, [])

  return { results, loading, error, suggestions, search, getSuggestions, reset }
}
