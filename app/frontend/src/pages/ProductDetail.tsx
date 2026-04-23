import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Card, CardContent, CardHeader } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { LoadingSpinner } from '../components/ui/LoadingSpinner'
import { productsApi, Product } from '../api/products'

export const ProductDetail = () => {
  const { id } = useParams<{ id: string }>()
  const [product, setProduct] = useState<Product | null>(null)
  const [recommendations, setRecommendations] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [activeImage, setActiveImage] = useState(0)

  useEffect(() => {
    const loadData = async () => {
      if (!id) return
      try {
        const [productData, recommendationsData] = await Promise.all([
          productsApi.getById(id),
          productsApi.getRecommendations(id),
        ])
        setProduct(productData)
        setRecommendations(recommendationsData.recommendations || [])
      } catch (err) {
        console.error('Failed to load product:', err)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [id])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!product) {
    return (
      <div className="text-center py-20">
        <h2 className="text-2xl font-bold text-gray-900">Product not found</h2>
        <Link to="/search" className="text-primary-600 mt-4 inline-block">
          Back to Search
        </Link>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      {/* Product Images */}
      <div className="space-y-4">
        <div className="aspect-square rounded-2xl overflow-hidden bg-gray-100">
          {product.images && product.images.length > 0 ? (
            <img
              src={product.images[activeImage]}
              alt={product.title}
              className="h-full w-full object-cover"
            />
          ) : (
            <div className="h-full flex items-center justify-center text-gray-400">
              No image available
            </div>
          )}
        </div>
        {product.images && product.images.length > 1 && (
          <div className="grid grid-cols-4 gap-2">
            {product.images.map((img, i) => (
              <button
                key={i}
                onClick={() => setActiveImage(i)}
                className={`aspect-square rounded-lg overflow-hidden ${activeImage === i ? 'ring-2 ring-primary-600' : ''}`}
              >
                <img src={img} alt={`View ${i + 1}`} className="h-full w-full object-cover" />
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Product Info */}
      <div className="space-y-6">
        <div>
          {product.brand && <p className="text-sm text-primary-600 font-medium mb-2">{product.brand}</p>}
          <h1 className="text-3xl font-bold text-gray-900 mb-4">{product.title}</h1>
          
          {product.price && (
            <div className="flex items-center gap-4 mb-6">
              <span className="text-4xl font-bold text-gray-900">
                {product.price.currency}{product.price.amount}
              </span>
              {product.price.original && (
                <span className="text-xl text-gray-500 line-through">
                  {product.price.currency}{product.price.original}
                </span>
              )}
              {product.price.original && product.price.amount && (
                <span className="bg-red-100 text-red-800 px-3 py-1 rounded-full text-sm font-bold">
                  {Math.round(((product.price.original - product.price.amount) / product.price.original) * 100)}% OFF
                </span>
              )}
            </div>
          )}

          {product.rating && (
            <div className="flex items-center gap-2 mb-6">
              <div className="flex items-center text-yellow-500">
                {[...Array(5)].map((_, i) => (
                  <svg key={i} className={`h-5 w-5 ${i < Math.round(product.rating!) ? 'fill-current' : 'text-gray-300'}`} fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                ))}
              </div>
              <span className="text-gray-600">{product.rating} / 5</span>
            </div>
          )}
        </div>

        {product.description && (
          <div className="prose max-w-none">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Description</h3>
            <p className="text-gray-600">{product.description}</p>
          </div>
        )}

        <div className="space-y-4">
          <Button className="w-full h-12 text-lg">Add to Cart</Button>
          <Button variant="outline" className="w-full h-12">
            Add to Wishlist
          </Button>
        </div>

        {product.availability && (
          <div className="border-t border-gray-200 pt-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Availability</h3>
            <div className="space-y-2">
              {product.availability.map((store, i) => (
                <div key={i} className="flex items-center justify-between text-sm">
                  <span className="text-gray-700">Store {store.store_id}</span>
                  <span className={store.in_stock ? 'text-green-600' : 'text-red-600'}>
                    {store.in_stock ? 'In Stock' : 'Out of Stock'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <div className="lg:col-span-2">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">You Might Also Like</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {recommendations.map((rec) => (
              <Card key={rec.id} className="overflow-hidden group">
                {rec.images && rec.images.length > 0 && (
                  <div className="aspect-square overflow-hidden bg-gray-100">
                    <img
                      src={rec.images[0]}
                      alt={rec.title}
                      className="h-full w-full object-cover transition-transform group-hover:scale-105"
                    />
                  </div>
                )}
                <CardContent className="p-4">
                  <h3 className="font-semibold text-gray-900 line-clamp-1 mb-2">{rec.title}</h3>
                  {rec.price && (
                    <div className="flex items-center gap-2">
                      <span className="text-lg font-bold text-gray-900">
                        {rec.price.currency}{rec.price.amount}
                      </span>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
