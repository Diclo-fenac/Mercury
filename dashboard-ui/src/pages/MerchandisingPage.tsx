import { useState, useEffect } from 'react';
import { getPinnedProducts, pinProduct } from '../lib/merchandising-api';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { toast } from 'sonner';

export const MerchandisingPage = () => {
  const [pins, setPins] = useState<any[]>([]);
  const [query, setQuery] = useState('');
  const [productId, setProductId] = useState('');
  const [position, setPosition] = useState(1);
  const [loading, setLoading] = useState(true);

  const fetchPins = async () => {
    try {
      const data = await getPinnedProducts();
      setPins(data);
    } catch (err) {
      toast.error('Failed to load rules');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPins();
  }, []);

  const handleAddPin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query || !productId) return;
    try {
      await pinProduct(query, productId, position);
      toast.success('Product pinned successfully', { duration: 5000 });
      setQuery('');
      setProductId('');
      setPosition(1);
      fetchPins();
    } catch (err) {
      toast.error('Failed to pin product', { duration: 5000 });
    }
  };

  return (
    <div className="p-8 space-y-6 max-w-5xl">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Merchandising</h2>
        <p className="text-muted-foreground mt-2">
          Customize search results by pinning products to specific query patterns.
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Create Rule</CardTitle>
            <CardDescription>Pin a specific product to always appear at the top for a query.</CardDescription>
          </CardHeader>
          <form onSubmit={handleAddPin}>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Query Pattern</label>
                <Input 
                  placeholder="e.g. running shoes" 
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Product ID</label>
                <Input 
                  placeholder="e.g. prod_12345" 
                  value={productId}
                  onChange={(e) => setProductId(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Position (1-indexed)</label>
                <Input 
                  type="number"
                  min="1"
                  value={position}
                  onChange={(e) => setPosition(parseInt(e.target.value))}
                  required
                />
              </div>
              <Button type="submit" className="w-full">Pin Product</Button>
            </CardContent>
          </form>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Active Rules</CardTitle>
            <CardDescription>Your current pinning overrides.</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? <p>Loading...</p> : (
              pins.length === 0 ? <p className="text-sm text-muted-foreground">No active rules.</p> :
              <div className="space-y-2">
                {pins.map(pin => (
                  <div key={pin.id} className="p-3 border rounded-md flex justify-between items-center">
                    <div>
                      <div className="font-semibold text-sm">Query: "{pin.query_pattern}"</div>
                      <div className="text-xs text-muted-foreground">Product ID: {pin.product_id}</div>
                    </div>
                    <div className="text-xs font-mono bg-muted px-2 py-1 rounded">Pos: {pin.position}</div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
