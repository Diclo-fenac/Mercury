import { useState, useEffect } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { Input } from '../components/ui/Input'
import { Button } from '../components/ui/Button'
import { Card, CardContent, CardHeader } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { EmptyState } from '../components/ui/EmptyState'
import { LoadingSpinner } from '../components/ui/LoadingSpinner'
import { useSearch } from '../hooks/useSearch'
import { productsApi, Product, SearchRequest } from '../api/products'

export const Search = () => {
  const [searchParams, setSearchParams] = useSearchParams()
  const query = searchParams.get('q') || ''
  const [searchQuery, setSearchQuery] = useState(query)
  const { results, loading, error, suggestions, search, getSuggestions, reset } = useSearch()
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [showSuggestions, setShowSuggestions] = useState(false)

  useEffect(() => {
    if (query) {
      search({
        query,
        pagination: { page: 1, limit: 20 },
      })
    }
  }, [query])

  useEffect(() => {
    if (query.length > 2) {
      const timer = setTimeout(() => {
        getSuggestions(query)
      }, 300)
      return () => clearTimeout(timer)
    }
    setShowSuggestions(false)
  }, [query, getSuggestions])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      setSearchParams({ q: searchQuery })
      search({
        query: searchQuery,
        pagination: { page: 1, limit: 20 },
      })
      setShowSuggestions(false)
    }
  }

  const handleSuggestionClick = (suggestion: string) => {
    setSearchQuery(suggestion)
    setSearchParams({ q: suggestion })
    search({
      query: suggestion,
      pagination: { page: 1, limit: 20 },
    })
    setShowSuggestions(false)
  }

  const categories = results?.facets?.category || {}
  const brands = results?.facets?.brand || {}

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
      {/* Search Input */}
      <div className="lg:col-span-4">
        <form onSubmit={handleSearch} className="relative">
          <Input
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value)
              setShowSuggestions(true)
            }}
            onFocus={() => setShowSuggestions(true)}
            placeholder="Search for products..."
            className="h-14 text-lg"
          />
          {showSuggestions && suggestions.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-lg shadow-xl border border-gray-200 z-50">
              {suggestions.map((suggestion, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="w-full px-4 py-3 text-left hover:bg-gray-50 text-gray-700"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          )}
        </form>
      </div>

      {/* Filters */}
      <div className="lg:col-span-1 space-y-6">
        <Card>
          <CardHeader className="border-b border-gray-100">
            <h3 className="font-semibold text-gray-900">Categories</h3>
          </CardHeader>
          <CardContent className="p-4">
            <div className="space-y-2">
              {Object.entries(categories).slice(0, 10).map(([category, count]) => (
                <label key={category} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedCategory === category}
                    onChange={() => setSelectedCategory(selectedCategory === category ? null : category)}
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="text-sm text-gray-700">{category}</span>
                  <span className="text-xs text-gray-500 ml-auto">({count})</span>
                </label>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="border-b border-gray-100">
            <h3 className="font-semibold text-gray-900">Brands</h3>
          </CardHeader>
          <CardContent className="p-4">
            <div className="space-y-2">
              {Object.entries(brands).slice(0, 10).map(([brand, count]) => (
                <label key={brand} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="text-sm text-gray-700">{brand}</span>
                  <span className="text-xs text-gray-500 ml-auto">({count})</span>
                </label>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Results */}
      <div className="lg:col-span-3">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <LoadingSpinner size="lg" />
          </div>
        ) : error ? (
          <EmptyState title="Search failed" description={error} />
        ) : results?.results.length === 0 ? (
          <EmptyState
            title="No products found"
            description={`We couldn't find any products matching "${query}". Try different keywords.`}
            action={
              <Button onClick={() => { reset(); setSearchParams({}) }}>
                Clear Search
              </Button>
            }
          />
        ) : (
          <>
            <div className="mb-6 flex items-center justify-between">
              <p className="text-gray-600">
                Showing {results?.results.length || 0} of {results?.total_results || 0} results
              </p>
              <select className="rounded-lg border-gray-300 text-sm focus:ring-primary-500">
                <option>Relevance</option>
                <option>Price: Low to High</option>
                <option>Price: High to Low</option>
                <option>Rating</option>
              </select>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              {results?.results.map((product) => (
                <Card key={product.id} className="overflow-hidden group">
                  {product.images && product.images.length > 0 && (
                    <div className="aspect-square overflow-hidden bg-gray-100">
                      <img
                        src={product.images[0]}
                        alt={product.title}
                        className="h-full w-full object-cover transition-transform group-hover:scale-105"
                      />
                    </div>
                  )}
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="font-semibold text-gray-900 line-clamp-1">{product.title}</h3>
                      {product.price?.original && product.price.amount && (
                        <Badge variant="danger">
                          {Math.round(((product.price.original - product.price.amount) / product.price.original) * 100)}% OFF
                        </Badge>
                      )}
                    </div>
                    {product.brand && <p className="text-sm text-gray-500 mb-1">{product.brand}</p>}
                    {product.price && (
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-lg font-bold text-gray-900">
                          {product.price.currency}{product.price.amount}
                        </span>
                        {product.price.original && (
                          <span className="text-sm text-gray-500 line-through">
                            {product.price.currency}{product.price.original}
                          </span>
                        )}
                      </div>
                    )}
                    {product.rating && (
                      <div className="flex items-center gap-1 text-sm text-yellow-500 mb-2">
                        <span>★</span>
                        <span className="text-gray-600">{product.rating}</span>
                      </div>
                    )}
                    {product.stock && (
                      <Badge variant={product.stock === 'In Stock' ? 'success' : 'warning'}>
                        {product.stock}
                      </Badge>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
