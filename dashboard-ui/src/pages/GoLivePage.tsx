import { useEffect, useState } from 'react';
import { getApiKeys, updateAllowedDomains } from '../lib/widget-api';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';

export const GoLivePage = () => {
  const [keys, setKeys] = useState<any[]>([]);
  const [domains, setDomains] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchKeys = async () => {
      try {
        const data = await getApiKeys();
        setKeys(data);
      } catch (err) {
        toast.error('Failed to load API keys');
      } finally {
        setLoading(false);
      }
    };
    fetchKeys();
  }, []);

  const handleUpdateDomains = async () => {
    try {
      const arr = domains.split(',').map(d => d.trim()).filter(Boolean);
      await updateAllowedDomains(arr);
      toast.success('Allowed domains updated');
    } catch (err) {
      toast.error('Failed to update domains');
    }
  };

  const publicKey = keys.find(k => k.type === 'public_search')?.prefix || 'pk_XXXXXXXXXXXXXXXX';

  const widgetSnippet = `<script src="https://cdn.mercury.com/widget.js"></script>
<script>
  Mercury.init({
    publicKey: '${publicKey}',
    container: '#mercury-search'
  });
</script>
<div id="mercury-search"></div>`;

  return (
    <div className="p-8 space-y-6 max-w-4xl">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Go Live</h2>
        <p className="text-muted-foreground mt-2">
          Embed Mercury into your application and manage your API keys.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>API Keys</CardTitle>
          <CardDescription>Your public and private keys for integrating Mercury.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {loading ? <p>Loading...</p> : (
            <div className="space-y-4">
              {keys.map(k => (
                <div key={k.id} className="flex flex-col space-y-1 p-4 border rounded-md">
                  <span className="font-semibold">{k.name} ({k.type})</span>
                  <code className="text-sm bg-muted p-1 rounded w-fit">{k.prefix}...</code>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Widget Snippet</CardTitle>
          <CardDescription>Copy and paste this snippet into your HTML to embed the search UI.</CardDescription>
        </CardHeader>
        <CardContent>
          <pre className="p-4 rounded-md bg-zinc-950 text-zinc-50 text-sm overflow-x-auto">
            {widgetSnippet}
          </pre>
          <Button 
            className="mt-4"
            variant="outline"
            onClick={() => {
              navigator.clipboard.writeText(widgetSnippet);
              toast.success('Snippet copied to clipboard');
            }}
          >
            Copy Snippet
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Security</CardTitle>
          <CardDescription>Restrict which domains can use your public search key.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Allowed Domains (comma separated)</Label>
            <Input 
              placeholder="e.g. localhost, mywebsite.com" 
              value={domains}
              onChange={e => setDomains(e.target.value)}
            />
          </div>
          <Button onClick={handleUpdateDomains}>Save Domains</Button>
        </CardContent>
      </Card>
    </div>
  );
};
