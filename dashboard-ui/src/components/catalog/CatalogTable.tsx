import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Search, MoreHorizontal, ArrowUpDown, ChevronLeft, ChevronRight, Edit, Trash2, Loader2, AlertCircle } from 'lucide-react';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { searchProducts, deleteProduct, updateProduct } from '@/lib/api';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';

import { useDebounce } from '@/hooks/use-debounce';
import { useNavigate } from 'react-router-dom';

export function CatalogTable() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const debouncedSearchTerm = useDebounce(searchTerm, 300);
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;
  const queryClient = useQueryClient();

  const [editingProduct, setEditingProduct] = useState<any>(null);
  const [editFormData, setEditFormData] = useState({ title: '', price: 0, stock: 0 });

  // Fetch live catalog data
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['products', debouncedSearchTerm, currentPage],
    queryFn: () => searchProducts({
      query: debouncedSearchTerm || "*",
      pagination: { page: currentPage, limit: itemsPerPage }
    })
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteProduct(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string, data: any }) => updateProduct(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
      setEditingProduct(null);
      toast.success('Product updated successfully');
    },
    onError: () => {
      toast.error('Failed to update product');
    }
  });

  const handleEditClick = (product: any) => {
    setEditingProduct(product);
    setEditFormData({
      title: product.name || product.title || '',
      price: product.price || 0,
      stock: product.stock || product.inventory || 0,
    });
  };

  const handleSaveEdit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingProduct) return;
    
    // In a real app we'd map this back to the exact schema the backend expects
    // For V1 MVP, we are patching the fields we know about.
    updateMutation.mutate({
      id: editingProduct.id,
      data: {
        title: editFormData.title,
        price: editFormData.price,
        stock: editFormData.stock
      }
    });
  };

  const products = data?.results || [];
  const totalResults = data?.total_results || 0;
  const totalPages = Math.ceil(totalResults / itemsPerPage);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900">Product Catalog</h1>
          <p className="text-zinc-500">Manage your inventory and search indexes.</p>
        </div>
        <Button className="bg-zinc-900 text-white hover:bg-zinc-800">
          Add Product
        </Button>
      </div>

      <Card className="rounded-xl shadow-sm border-border">
        <CardHeader className="pb-4">
          <div className="flex items-center gap-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
              <Input 
                placeholder="Search products..." 
                className="pl-9"
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  setCurrentPage(1);
                }}
              />
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" className="text-zinc-600">Filter</Button>
              <Button variant="outline" size="sm" className="text-zinc-600">Export</Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="border border-border rounded-xl overflow-x-auto overflow-y-hidden">
            <Table>
              <TableHeader className="bg-zinc-50">
                <TableRow>
                  <TableHead className="w-[100px]">Image</TableHead>
                  <TableHead>
                    <Button variant="ghost" className="-ml-4 h-8 data-[state=open]:bg-accent font-semibold text-zinc-900">
                      Product Details
                      <ArrowUpDown className="ml-2 h-4 w-4" />
                    </Button>
                  </TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead className="text-right">Price</TableHead>
                  <TableHead className="text-right">Stock</TableHead>
                  <TableHead className="text-center">Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <TableRow>
                    <TableCell colSpan={7} className="h-48 text-center">
                      <div className="flex flex-col items-center justify-center space-y-3 text-zinc-500">
                        <Loader2 className="h-6 w-6 animate-spin text-zinc-400" />
                        <p>Loading catalog data...</p>
                      </div>
                    </TableCell>
                  </TableRow>
                ) : isError ? (
                  <TableRow>
                    <TableCell colSpan={7} className="h-48 text-center">
                      <div className="flex flex-col items-center justify-center space-y-3 text-red-500">
                        <AlertCircle className="h-8 w-8 text-red-400" />
                        <p>Failed to load catalog.</p>
                        <p className="text-xs text-red-400">{error instanceof Error ? error.message : 'Unknown error'}</p>
                      </div>
                    </TableCell>
                  </TableRow>
                ) : isLoading ? (
                  Array.from({ length: 5 }).map((_, i) => (
                    <TableRow key={`skeleton-${i}`}>
                      <TableCell><div className="w-12 h-12 bg-zinc-100 animate-pulse rounded-md"></div></TableCell>
                      <TableCell>
                        <div className="h-4 bg-zinc-100 animate-pulse rounded w-3/4 mb-2"></div>
                        <div className="h-3 bg-zinc-100 animate-pulse rounded w-1/2"></div>
                      </TableCell>
                      <TableCell><div className="h-5 bg-zinc-100 animate-pulse rounded-full w-24"></div></TableCell>
                      <TableCell><div className="h-4 bg-zinc-100 animate-pulse rounded w-16 ml-auto"></div></TableCell>
                      <TableCell><div className="h-4 bg-zinc-100 animate-pulse rounded w-12 ml-auto"></div></TableCell>
                      <TableCell><div className="h-6 bg-zinc-100 animate-pulse rounded-full w-16 mx-auto"></div></TableCell>
                      <TableCell><div className="h-8 bg-zinc-100 animate-pulse rounded w-8 ml-auto"></div></TableCell>
                    </TableRow>
                  ))
                ) : products.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="h-48 text-center text-zinc-500">
                      <div className="flex flex-col items-center justify-center space-y-3">
                        <div className="h-12 w-12 rounded-full bg-zinc-100 flex items-center justify-center">
                          <Search className="h-6 w-6 text-zinc-400" />
                        </div>
                        <p className="font-medium text-zinc-900">No products found</p>
                        <p className="text-sm">Get started by ingesting your catalog.</p>
                        <Button 
                          variant="outline" 
                          className="mt-2"
                          onClick={() => navigate('/ingest')}
                        >
                          Upload CSV
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ) : (
                  products.map((item: any) => (
                    <TableRow key={item.id} className="group hover:bg-zinc-50/50">
                      <TableCell>
                        <div className="w-12 h-12 rounded-md bg-zinc-100 border border-zinc-200 flex items-center justify-center overflow-hidden">
                          {item.image_url ? (
                             <img src={item.image_url} alt={item.name} className="w-full h-full object-cover" />
                          ) : (
                             <span className="text-xl">📦</span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="font-medium text-zinc-900">{item.name || item.title || 'Unknown Product'}</div>
                        <div className="text-xs text-zinc-500 font-mono mt-0.5">{item.id}</div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary" className="bg-zinc-100 text-zinc-600 font-normal hover:bg-zinc-200">
                          {item.category || item.categories?.[0] || 'Uncategorized'}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        ${item.price?.toFixed(2) || '0.00'}
                      </TableCell>
                      <TableCell className="text-right text-zinc-600">
                        {item.stock || item.inventory || 0}
                      </TableCell>
                      <TableCell className="text-center">
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          (item.status || 'active') === 'active' ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-zinc-100 text-zinc-700 border border-zinc-200'
                        }`}>
                          {(item.status || 'active').charAt(0).toUpperCase() + (item.status || 'active').slice(1)}
                        </span>
                      </TableCell>
                      <TableCell className="text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity">
                              <span className="sr-only">Open menu</span>
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end" className="w-40">
                            <DropdownMenuLabel>Actions</DropdownMenuLabel>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem 
                              className="text-zinc-600 cursor-pointer"
                              onClick={() => handleEditClick(item)}
                            >
                              <Edit className="mr-2 h-4 w-4" /> Edit Product
                            </DropdownMenuItem>
                            <DropdownMenuItem 
                              className="text-red-600 focus:text-red-600 cursor-pointer"
                              onClick={() => deleteMutation.mutate(item.id)}
                            >
                              <Trash2 className="mr-2 h-4 w-4" /> Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4 text-sm text-zinc-500">
              <div>
                Showing {(currentPage - 1) * itemsPerPage + 1} to {Math.min(currentPage * itemsPerPage, totalResults)} of {totalResults} entries
              </div>
              <div className="flex items-center gap-2">
                <Button 
                  variant="outline" 
                  size="icon" 
                  className="h-8 w-8" 
                  disabled={currentPage === 1 || isLoading}
                  onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                  aria-label="Previous page"
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <div className="flex items-center justify-center min-w-[2rem] font-medium text-zinc-900">
                  {currentPage} / {totalPages}
                </div>
                <Button 
                  variant="outline" 
                  size="icon" 
                  className="h-8 w-8"
                  disabled={currentPage === totalPages || isLoading}
                  onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                  aria-label="Next page"
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={!!editingProduct} onOpenChange={(open) => !open && setEditingProduct(null)}>
        <DialogContent className="sm:max-w-[425px]">
          <form onSubmit={handleSaveEdit}>
            <DialogHeader>
              <DialogTitle>Edit Product</DialogTitle>
              <DialogDescription>
                Make changes to your product here. Click save when you're done.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="title">Title</Label>
                <Input
                  id="title"
                  value={editFormData.title}
                  onChange={(e) => setEditFormData({ ...editFormData, title: e.target.value })}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="price">Price ($)</Label>
                  <Input
                    id="price"
                    type="number"
                    step="0.01"
                    value={editFormData.price}
                    onChange={(e) => setEditFormData({ ...editFormData, price: parseFloat(e.target.value) })}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="stock">Stock</Label>
                  <Input
                    id="stock"
                    type="number"
                    value={editFormData.stock}
                    onChange={(e) => setEditFormData({ ...editFormData, stock: parseInt(e.target.value) })}
                  />
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setEditingProduct(null)}>
                Cancel
              </Button>
              <Button type="submit" disabled={updateMutation.isPending}>
                {updateMutation.isPending ? 'Saving...' : 'Save changes'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
