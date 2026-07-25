import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { createWebhookSource } from '@/lib/api';
import { toast } from 'sonner';

interface WebhookConfigStepProps {
  onBack: () => void;
}

export function WebhookConfigStep({ onBack }: WebhookConfigStepProps) {
  const navigate = useNavigate();
  const [source, setSource] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const generateSource = async () => {
    setLoading(true);
    try {
      const data = await createWebhookSource();
      setSource(data);
      toast.success('Webhook source generated');
    } catch (err: any) {
      toast.error(err.message || 'Failed to generate webhook source');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard');
  };

  return (
    <Card className="rounded-xl shadow-sm border-border">
      <CardHeader>
        <CardTitle>Configure Webhook Source</CardTitle>
        <CardDescription>Generate an endpoint to send real-time catalog updates to Mercury.</CardDescription>
      </CardHeader>
      <CardContent>
        {!source ? (
          <div className="text-center py-12">
            <p className="text-zinc-500 mb-6">Create a new webhook endpoint to start pushing JSON payloads.</p>
            <Button onClick={generateSource} disabled={loading}>
              {loading ? 'Generating...' : 'Generate Endpoint'}
            </Button>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="p-4 bg-zinc-50 rounded-lg border border-zinc-200">
              <label className="text-sm font-semibold text-zinc-900 block mb-2">Endpoint URL</label>
              <div className="flex gap-2">
                <code className="flex-1 bg-white p-2 rounded border border-zinc-200 text-sm overflow-x-auto">
                  {window.location.origin}{source.webhook_endpoint}
                </code>
                <Button variant="outline" onClick={() => copyToClipboard(`${window.location.origin}${source.webhook_endpoint}`)}>Copy</Button>
              </div>
            </div>

            <div className="p-4 bg-zinc-50 rounded-lg border border-zinc-200">
              <label className="text-sm font-semibold text-zinc-900 block mb-2">Webhook Secret Header (x-webhook-secret)</label>
              <div className="flex gap-2">
                <code className="flex-1 bg-white p-2 rounded border border-zinc-200 text-sm overflow-x-auto">
                  {source.webhook_secret}
                </code>
                <Button variant="outline" onClick={() => copyToClipboard(source.webhook_secret)}>Copy</Button>
              </div>
              <p className="text-xs text-zinc-500 mt-2">Include this in the headers of all POST requests to the endpoint.</p>
            </div>
            
            <p className="text-sm text-zinc-600 bg-amber-50 p-4 rounded-lg border border-amber-200">
              Note: Field mapping for webhooks requires a sample payload to be sent first. 
              Send a test payload to the endpoint, then visit the Webhook mappings page (Coming Soon).
            </p>
          </div>
        )}
      </CardContent>
      <CardFooter className="flex justify-between border-t border-border pt-6">
        <Button variant="outline" onClick={onBack}>Back to Source Selection</Button>
        {source && <Button onClick={() => navigate('/catalog')}>Done</Button>}
      </CardFooter>
    </Card>
  );
}
