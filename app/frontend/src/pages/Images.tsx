import { useState, useRef } from 'react'
import { Button } from '../components/ui/Button'
import { Card, CardContent } from '../components/ui/Card'
import { EmptyState } from '../components/ui/EmptyState'
import { LoadingSpinner } from '../components/ui/LoadingSpinner'
import { imagesApi, ImageAnalysis, ImageSearchResponse } from '../api/images'
import { useAuth } from '../hooks/useAuth'

export const Images = () => {
  const { isAuthenticated } = useAuth()
  const [image, setImage] = useState<string | null>(null)
  const [analysis, setAnalysis] = useState<ImageAnalysis | null>(null)
  const [searchResults, setSearchResults] = useState<ImageSearchResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    if (!file.type.startsWith('image/')) {
      setError('Please upload an image file (JPEG, PNG, WEBP)')
      return
    }

    if (file.size > 5 * 1024 * 1024) {
      setError('Image size must be less than 5MB')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const reader = new FileReader()
      reader.onload = async (event) => {
        const imageData = event.target?.result as string
        setImage(imageData)

        const userId = localStorage.getItem('user_id') || 'user_' + Date.now()
        localStorage.setItem('user_id', userId)

        const response = await imagesApi.upload(imageData, 'Uploaded image')
        setAnalysis(response.analysis)
        setSearchResults(null)
      }
      reader.readAsDataURL(file)
    } catch (err) {
      setError('Failed to upload image')
    } finally {
      setLoading(false)
    }
  }

  const handleImageSearch = async () => {
    if (!image) return

    setLoading(true)
    setError(null)

    try {
      const userId = localStorage.getItem('user_id') || 'user_' + Date.now()
      localStorage.setItem('user_id', userId)

      const response = await imagesApi.search({
        image_data: image,
        prompt: searchQuery || 'Find similar products',
        search_type: 'exact_and_similar',
        limit: 10,
      })

      setSearchResults(response)
    } catch (err) {
      setError('Failed to search by image')
    } finally {
      setLoading(false)
    }
  }

  if (!isAuthenticated()) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Please login to use image features</h2>
          <Button onClick={() => window.location.href = '/login'}>Login</Button>
        </div>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      {/* Upload Section */}
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Image Search</h1>
          <p className="text-gray-500 mt-1">Upload an image to search for similar products</p>
        </div>

        <Card className="border-2 border-dashed border-gray-300 hover:border-primary-500 transition-colors">
          <CardContent className="p-8 text-center">
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleImageUpload}
              className="hidden"
            />
            <div
              onClick={() => fileInputRef.current?.click()}
              className="cursor-pointer"
            >
              <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-primary-100 text-primary-600 mb-4">
                <svg className="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900">Click to upload image</h3>
              <p className="text-sm text-gray-500 mt-1">JPEG, PNG, or WEBP (max 5MB)</p>
            </div>
          </CardContent>
        </Card>

        {image && (
          <div className="relative rounded-xl overflow-hidden bg-gray-100">
            <img src={image} alt="Uploaded" className="max-h-96 w-full object-contain" />
            <Button
              variant="danger"
              size="sm"
              className="absolute top-2 right-2"
              onClick={() => { setImage(null); setAnalysis(null); setSearchResults(null); }}
            >
              Remove
            </Button>
          </div>
        )}

        {analysis && (
          <Card>
            <CardContent className="p-6">
              <h3 className="font-semibold text-gray-900 mb-4">Image Analysis</h3>
              <div className="space-y-3">
                <div>
                  <p className="text-sm text-gray-500">Description</p>
                  <p className="text-gray-900">{analysis.description}</p>
                </div>
                {analysis.is_barcode && (
                  <div className="bg-green-50 p-3 rounded-lg">
                    <p className="text-sm text-green-800 font-medium">Barcode Detected!</p>
                    <p className="text-green-700">{analysis.barcode_data}</p>
                    <p className="text-xs text-green-600 mt-1">Type: {analysis.barcode_type}</p>
                  </div>
                )}
                {analysis.confidence_score && (
                  <div>
                    <p className="text-sm text-gray-500">Confidence</p>
                    <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                      <div
                        className="bg-green-500 h-2 rounded-full"
                        style={{ width: `${analysis.confidence_score * 100}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {image && (
          <div className="space-y-4">
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search prompt (optional)"
            />
            <Button
              className="w-full"
              onClick={handleImageSearch}
              isLoading={loading}
            >
              Search Products
            </Button>
          </div>
        )}
      </div>

      {/* Results Section */}
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-gray-900">Search Results</h2>
        
        {loading && (
          <div className="flex items-center justify-center py-20">
            <LoadingSpinner size="lg" />
          </div>
        )}

        {error && (
          <div className="bg-red-50 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {searchResults?.results && searchResults.results.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {searchResults.results.map((product, i) => (
              <Card key={i} className="overflow-hidden">
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
                  <h3 className="font-semibold text-gray-900 line-clamp-1 mb-2">{product.title}</h3>
                  {product.price && (
                    <div className="flex items-center gap-2">
                      <span className="text-lg font-bold text-gray-900">
                        {product.price.currency}{product.price.amount}
                      </span>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        ) : !loading && searchResults ? (
          <EmptyState
            title="No products found"
            description="Try adjusting your search or uploading a different image."
          />
        ) : (
          <EmptyState
            title="Upload an image to search"
            description="Select an image to find similar products or detect barcodes."
          />
        )}
      </div>
    </div>
  )
}

// Simple input component for Images page
const Input = ({ value, onChange, placeholder }: { value: string; onChange: (e: React.ChangeEvent<HTMLInputElement>) => void; placeholder: string }) => (
  <input
    type="text"
    value={value}
    onChange={onChange}
    placeholder={placeholder}
    className="block w-full rounded-lg border-gray-300 bg-white py-2.5 px-3 text-gray-900 placeholder-gray-400 focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
  />
)
