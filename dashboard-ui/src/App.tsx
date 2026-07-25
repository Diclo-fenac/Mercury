import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { DashboardLayout } from './components/layout/DashboardLayout';
import { AuthGuard } from './components/layout/AuthGuard';
import { ErrorBoundary } from './components/layout/ErrorBoundary';
import { OverviewDashboard } from './components/dashboard/OverviewDashboard';
import { IngestionWizard } from './components/ingest/IngestionWizard';
import { CatalogTable } from './components/catalog/CatalogTable';
import { AuthPage } from './pages/AuthPage';
import { OnboardPage } from './pages/OnboardPage';

import { GoLivePage } from './pages/GoLivePage';

import { MerchandisingPage } from './pages/MerchandisingPage';

import { ThemeProvider } from './components/ui/theme-provider';
import { Toaster } from './components/ui/sonner';

function App() {
  return (
    <ThemeProvider defaultTheme="system" storageKey="vite-ui-theme">
      <BrowserRouter basename="/dashboard">
        <ErrorBoundary>
          <Routes>
            <Route path="/login" element={<AuthPage />} />
            <Route path="/onboard" element={<OnboardPage />} />
            
            <Route path="/" element={<AuthGuard><DashboardLayout><OverviewDashboard /></DashboardLayout></AuthGuard>} />
            <Route path="/catalog" element={<AuthGuard><DashboardLayout><CatalogTable /></DashboardLayout></AuthGuard>} />
            <Route path="/merchandising" element={<AuthGuard><DashboardLayout><MerchandisingPage /></DashboardLayout></AuthGuard>} />
            <Route path="/ingest" element={<AuthGuard><DashboardLayout><IngestionWizard /></DashboardLayout></AuthGuard>} />
            <Route path="/go-live" element={<AuthGuard><DashboardLayout><GoLivePage /></DashboardLayout></AuthGuard>} />
            
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </ErrorBoundary>
      </BrowserRouter>
      <Toaster />
    </ThemeProvider>
  );
}

export default App;
