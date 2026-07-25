import { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { verifyToken } from '../lib/auth-api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../components/ui/card';
import { toast } from 'sonner';

export const AuthPage = () => {
  const [token, setTokenInput] = useState('');
  const [loading, setLoading] = useState(false);
  const setAuth = useAuthStore((state) => state.setAuth);
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token.trim()) return;

    setLoading(true);
    try {
      await verifyToken(token.trim());
      setAuth();
      toast.success('Authenticated successfully');
      
      const from = (location.state as any)?.from?.pathname || '/';
      navigate(from, { replace: true });
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Invalid Secret Key');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/40 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1 text-center">
          <CardTitle className="text-2xl font-bold">Login to Mercury</CardTitle>
          <CardDescription>
            Enter your private admin key (sk_...) to manage your search engine.
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleLogin}>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Input
                id="token"
                type="password"
                placeholder="sk_..."
                value={token}
                onChange={(e) => setTokenInput(e.target.value)}
                required
              />
            </div>
          </CardContent>
          <CardFooter className="flex flex-col space-y-4">
            <Button className="w-full" type="submit" disabled={loading || !token}>
              {loading ? 'Verifying...' : 'Login'}
            </Button>
            <div className="text-center text-sm text-muted-foreground">
              New to Mercury? <Link to="/onboard" className="underline hover:text-primary">Onboard a new organization</Link>
            </div>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
};
