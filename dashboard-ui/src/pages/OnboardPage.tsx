import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { onboardTenant } from '../lib/auth-api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../components/ui/card';
import { toast } from 'sonner';

export const OnboardPage = () => {
  const [formData, setFormData] = useState({ name: '', slug: '', owner_email: '' });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const setAuth = useAuthStore((state) => state.setAuth);
  const navigate = useNavigate();

  const [errorMsg, setErrorMsg] = useState('');

  const handleOnboard = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg('');
    try {
      const data = await onboardTenant({ ...formData, plan: 'free' });
      setResult(data);
      toast.success('Organization created successfully!');
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to onboard';
      setErrorMsg(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const finishOnboarding = () => {
    if (result?.admin_key) {
      setAuth();
      navigate('/');
    }
  };

  if (result) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-muted/40 p-4">
        <Card className="w-full max-w-lg">
          <CardHeader>
            <CardTitle className="text-2xl font-bold text-green-600">Welcome to Mercury!</CardTitle>
            <CardDescription>
              Your organization has been created and your Typesense index is provisioned.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 bg-muted rounded-md border">
              <Label className="text-muted-foreground text-xs uppercase tracking-wider mb-1 block">Your Private Admin Key (sk_*)</Label>
              <code className="text-sm font-mono break-all">{result.admin_key}</code>
            </div>
            <div className="p-4 bg-muted rounded-md border">
              <Label className="text-muted-foreground text-xs uppercase tracking-wider mb-1 block">Your Public Search Key (pk_*)</Label>
              <code className="text-sm font-mono break-all">{result.search_key}</code>
            </div>
            <p className="text-sm text-muted-foreground">
              <strong>Important:</strong> Save your admin key in a password manager. You will need it to log in.
            </p>
          </CardContent>
          <CardFooter>
            <Button className="w-full" onClick={finishOnboarding}>
              Go to Dashboard
            </Button>
          </CardFooter>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/40 p-4">
      <Card className="w-full max-w-md border-zinc-300 dark:border-zinc-800 shadow-md">
        <CardHeader className="space-y-1 text-center">
          <CardTitle className="text-2xl font-bold">Onboard Organization</CardTitle>
          <CardDescription>
            Create a new tenant organization in Mercury.
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleOnboard}>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Organization Name</Label>
              <Input
                id="name"
                placeholder="Acme Corp"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
                className="focus-visible:ring-2 focus-visible:ring-blue-500"
                aria-invalid={!!errorMsg}
                aria-describedby={errorMsg ? "onboard-error" : undefined}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="slug">Slug (URL-friendly)</Label>
              <Input
                id="slug"
                placeholder="acme-corp"
                value={formData.slug}
                onChange={(e) => setFormData({ ...formData, slug: e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, '') })}
                required
                className="focus-visible:ring-2 focus-visible:ring-blue-500"
                aria-invalid={!!errorMsg}
                aria-describedby={errorMsg ? "onboard-error" : undefined}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="owner_email">Owner Email</Label>
              <Input
                id="owner_email"
                type="email"
                placeholder="admin@acme.com"
                value={formData.owner_email}
                onChange={(e) => setFormData({ ...formData, owner_email: e.target.value })}
                required
                className="focus-visible:ring-2 focus-visible:ring-blue-500"
                aria-invalid={!!errorMsg}
                aria-describedby={errorMsg ? "onboard-error" : undefined}
              />
            </div>
            
            {errorMsg && (
              <div id="onboard-error" className="text-sm font-medium text-destructive" role="alert">
                {errorMsg}
              </div>
            )}
          </CardContent>
          <CardFooter className="flex flex-col space-y-4">
            <Button className="w-full" type="submit" disabled={loading}>
              {loading ? 'Provisioning Tenant...' : 'Create Organization'}
            </Button>
            <div className="text-center text-sm text-muted-foreground">
              Already have an account? <Link to="/login" className="underline hover:text-primary">Login here</Link>
            </div>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
};
