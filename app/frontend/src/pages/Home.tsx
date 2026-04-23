import { Link } from 'react-router-dom'
import { Button } from '../components/ui/Button'
import { Card, CardContent, CardHeader } from '../components/ui/Card'
import { useSearch } from '../hooks/useSearch'
import { productsApi, Product } from '../api/products'
import { useEffect, useState } from 'react'

interface TrendingProduct extends Product {
  trending_score?: number
}

export const Home = () => {
  const { search } = useSearch()
  const [trending, setTrending] = useState<TrendingProduct[]>([])
  const [deals, setDeals] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadData = async () => {
      try {
        const [trendingRes, dealsRes] = await Promise.all([
          productsApi.getTrending(undefined, 7, 1, 6),
          productsApi.getDeals(undefined, 20, 1, 6),
        ])
        setTrending(trendingRes.trending_products || [])
        setDeals(dealsRes.deals || [])
      } catch (err) {
        console.error('Failed to load home data:', err)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <section className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-primary-600 to-blue-700 py-16 px-6 text-white">
        <div className="container mx-auto text-center">
          <h1 className="text-4xl md:text-6xl font-bold mb-6">
            Discover Products with AI
          </h1>
          <p className="text-xl md:text-2xl text-blue-100 mb-8 max-w-2xl mx-auto">
            Get personalized recommendations, search by image, and chat with our AI assistant to find exactly what you're looking for.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/search">
              <Button size="lg" className="bg-white text-primary-600 hover:bg-gray-100">
                Start Searching
              </Button>
            </Link>
            <Link to="/chat">
              <Button size="lg" variant="outline" className="border-white text-white hover:bg-white/10">
                Chat with AI
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Trending Products */}
      <section>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Trending Now</h2>
          <Link to="/search" className="text-primary-600 hover:text-primary-700 font-medium">
            View All
          </Link>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {trending.map((product) => (
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
                <h3 className="font-semibold text-gray-900 mb-2 line-clamp-1">{product.title}</h3>
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
                  <div className="flex items-center gap-1 text-sm text-yellow-500">
                    <span>★</span>
                    <span className="text-gray-600">{product.rating}</span>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* Deals Section */}
      <section className="bg-gray-50 rounded-2xl p-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Special Deals</h2>
          <Link to="/search" className="text-primary-600 hover:text-primary-700 font-medium">
            View All Deals
          </Link>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {deals.map((product) => (
            <Card key={product.id} className="overflow-hidden">
              {product.images && product.images.length > 0 && (
                <div className="aspect-square overflow-hidden bg-gray-100">
                  <img
                    src={product.images[0]}
                    alt={product.title}
                    className="h-full w-full object-cover"
                  />
                </div>
              )}
              <CardContent className="p-4">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-semibold text-gray-900 line-clamp-1">{product.title}</h3>
                  {product.price && product.price.original && product.price.amount && (
                    <span className="bg-red-100 text-red-800 text-xs font-bold px-2 py-1 rounded-full">
                      {Math.round(((product.price.original - product.price.amount) / product.price.original) * 100)}% OFF
                    </span>
                  )}
                </div>
                {product.price && (
                  <div className="flex items-center gap-2">
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
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {[
          {
            title: 'AI Chat Assistant',
            description: 'Get personalized recommendations and answers from our AI assistant.',
            icon: (
              <svg className="h-8 w-8 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            ),
          },
          {
            title: 'Image Search',
            description: 'Upload an image and find similar products instantly.',
            icon: (
              <svg className="h-8 w-8 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            ),
          },
          {
            title: 'Personalized Recommendations',
            description: 'Get product suggestions based on your preferences and history.',
            icon: (
              <svg className="h-8 w-8 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            ),
          },
        ].map((feature, i) => (
          <Card key={i} className="p-6 hover:shadow-lg transition-shadow">
            <div className="mb-4">{feature.icon}</div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">{feature.title}</h3>
            <p className="text-gray-500">{feature.description}</p>
          </Card>
        ))}
      </section>
    </div>
  )
}
