import React, { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
import { AlertTriangle } from 'lucide-react';
import { Button } from '../ui/button';

interface Props {
  children?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  private handleReload = () => {
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex flex-col items-center justify-center bg-zinc-50 p-4">
          <div className="max-w-md w-full bg-white p-8 rounded-xl shadow-sm border border-zinc-200 text-center space-y-4">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <AlertTriangle className="h-8 w-8 text-red-600" />
            </div>
            <h1 className="text-2xl font-bold text-zinc-900">Something went wrong</h1>
            <p className="text-zinc-500 text-sm">
              An unexpected error occurred in the application dashboard.
            </p>
            {this.state.error && (
              <div className="mt-4 p-4 bg-zinc-100 rounded-md text-left overflow-auto max-h-32">
                <code className="text-xs text-red-800 break-words font-mono">
                  {this.state.error.message}
                </code>
              </div>
            )}
            <div className="pt-4">
              <Button onClick={this.handleReload} className="w-full">
                Reload Page
              </Button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
