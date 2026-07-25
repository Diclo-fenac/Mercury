import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertCircle } from 'lucide-react';

interface ShopifyConfigStepProps {
  onBack: () => void;
}

export function ShopifyConfigStep({ onBack }: ShopifyConfigStepProps) {
  return (
    <Card className="rounded-xl shadow-sm border-border">
      <CardHeader>
        <CardTitle>Shopify Integration</CardTitle>
        <CardDescription>Connect your Shopify store to automatically sync products.</CardDescription>
      </CardHeader>
      <CardContent className="py-12 text-center">
        <div className="w-16 h-16 rounded-full bg-blue-50 flex items-center justify-center mx-auto mb-6">
          <AlertCircle className="w-8 h-8 text-blue-500" />
        </div>
        <h2 className="text-xl font-bold text-zinc-900 mb-2">Coming Soon in V2</h2>
        <p className="text-zinc-500 max-w-md mx-auto">
          The one-click Shopify connector is currently in beta testing and will be released in the next major update.
          For now, please export your products as a CSV from Shopify and use the File Upload method.
        </p>
      </CardContent>
      <CardFooter className="flex justify-start border-t border-border pt-6">
        <Button variant="outline" onClick={onBack}>Back to Source Selection</Button>
      </CardFooter>
    </Card>
  );
}
