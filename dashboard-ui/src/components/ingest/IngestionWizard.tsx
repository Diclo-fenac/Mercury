import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Database, FileJson, Link, CheckCircle2, AlertCircle } from 'lucide-react';
import { FileUploadStep } from './FileUploadStep';
import { MappingStep } from './MappingStep';
import { WebhookConfigStep } from './WebhookConfigStep';
import { ShopifyConfigStep } from './ShopifyConfigStep';
import { uploadCatalog } from '@/lib/api';
import Papa from 'papaparse';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';

type WizardStep = 'source' | 'configure' | 'mapping' | 'progress';

export function IngestionWizard() {
  const [currentStep, setCurrentStep] = useState<WizardStep>('source');
  const [sourceType, setSourceType] = useState<string | null>(null);
  
  // File data state
  const [csvHeaders, setCsvHeaders] = useState<string[]>([]);
  const [sampleData, setSampleData] = useState<any[]>([]);
  const [fileName, setFileName] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStats, setUploadStats] = useState<any>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const navigate = useNavigate();

  const sources: Array<{ id: string, name: string, description: string, icon: any, disabled?: boolean }> = [
    { id: 'file', name: 'File Upload', description: 'CSV or JSON files', icon: FileJson },
    { id: 'webhook', name: 'Webhook', description: 'Real-time ingestion endpoint', icon: Link },
    { id: 'shopify', name: 'Shopify (Soon)', description: 'One-click connector', icon: Database, disabled: true },
  ];

  const handleFileParsed = (headers: string[], data: any[], name: string) => {
    setCsvHeaders(headers);
    setSampleData(data);
    setFileName(name);
    setCurrentStep('mapping');
  };

  const handleMappingComplete = async (mapping: Record<string, string>) => {
    setCurrentStep('progress');
    setIsUploading(true);
    setUploadError(null);
    setUploadStats(null);

    try {
      // 1. Transform sampleData (which is the full parsed dataset) using mapping
      const mappedData = sampleData.map(row => {
        const newRow: Record<string, any> = {};
        Object.keys(mapping).forEach(targetField => {
          const sourceField = mapping[targetField];
          if (sourceField && sourceField !== 'ignore') {
            newRow[targetField] = row[sourceField];
          }
        });
        return newRow;
      });

      // 2. Unparse back to CSV
      const csvStr = Papa.unparse(mappedData);

      // 3. Create a File object
      const blob = new Blob([csvStr], { type: 'text/csv' });
      const mappedFile = new File([blob], fileName || 'mapped_catalog.csv', { type: 'text/csv' });

      // 4. Upload to FastAPI
      const response = await uploadCatalog(mappedFile);
      setUploadStats(response.stats);
      toast.success('Catalog ingested successfully!');
    } catch (err: any) {
      console.error('Upload failed:', err);
      setUploadError(err.response?.data?.detail || err.message || 'An error occurred during ingestion.');
      toast.error('Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const stepIndex = ['source', 'configure', 'mapping', 'progress'].indexOf(currentStep);

  return (
    <div className="max-w-4xl mx-auto py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-zinc-900">Add New Data Source</h1>
        <p className="text-zinc-500">Connect your product catalog to Mercury's indexing engine.</p>
      </div>

      <div className="flex items-center justify-between mb-8">
        {['Source', 'Configure', 'Mapping', 'Progress'].map((step, index) => (
          <div key={step} className="flex items-center gap-2">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-colors duration-300 ${
              index <= stepIndex ? 'bg-zinc-900 text-white' : 'bg-zinc-100 text-zinc-400'
            }`}>
              {index + 1}
            </div>
            <span className={`font-medium ${index <= stepIndex ? 'text-zinc-900' : 'text-zinc-400'}`}>
              {step}
            </span>
            {index < 3 && <div className={`w-12 h-px transition-colors duration-300 mx-2 ${index < stepIndex ? 'bg-zinc-900' : 'bg-zinc-200'}`} />}
          </div>
        ))}
      </div>

      {currentStep === 'source' && (
        <Card className="rounded-xl shadow-sm border-border">
          <CardHeader>
            <CardTitle>Select Source Type</CardTitle>
            <CardDescription>Choose how you want to ingest your product catalog.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {sources.map((source) => (
                <button
                  key={source.id}
                  disabled={source.disabled}
                  onClick={() => setSourceType(source.id)}
                  className={`relative p-6 text-left rounded-xl border-2 transition-all ${
                    source.disabled ? 'opacity-50 cursor-not-allowed bg-zinc-50 border-zinc-200' :
                    sourceType === source.id 
                      ? 'border-zinc-900 bg-zinc-50' 
                      : 'border-zinc-200 hover:border-zinc-300 hover:bg-zinc-50/50'
                  }`}
                >
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-4 ${
                    sourceType === source.id ? 'bg-zinc-900 text-white' : 'bg-zinc-100 text-zinc-600'
                  }`}>
                    <source.icon className="w-5 h-5" />
                  </div>
                  <h3 className="font-semibold text-zinc-900">{source.name}</h3>
                  <p className="text-sm text-zinc-500 mt-1">{source.description}</p>
                  
                  {source.disabled && (
                    <div className="mt-3 inline-block bg-zinc-100 text-zinc-500 text-xs px-2 py-1 rounded">Coming Soon</div>
                  )}

                  {sourceType === source.id && (
                    <div className="absolute top-4 right-4 text-zinc-900">
                      <CheckCircle2 className="w-5 h-5" />
                    </div>
                  )}
                </button>
              ))}
            </div>
          </CardContent>
          <CardFooter className="flex justify-end gap-3 border-t border-border pt-6">
            <Button variant="outline" className="rounded-lg">Cancel</Button>
            <Button 
              className="rounded-lg bg-zinc-900 text-white hover:bg-zinc-800"
              disabled={!sourceType}
              onClick={() => setCurrentStep('configure')}
            >
              Continue to Configuration
            </Button>
          </CardFooter>
        </Card>
      )}

      {currentStep === 'configure' && sourceType === 'file' && (
        <Card className="rounded-xl shadow-sm border-border">
          <CardHeader>
            <CardTitle>Upload File</CardTitle>
            <CardDescription>Upload a CSV or JSON file containing your catalog.</CardDescription>
          </CardHeader>
          <CardContent>
            <FileUploadStep onFileParsed={handleFileParsed} />
          </CardContent>
          <CardFooter className="flex justify-between border-t border-border pt-6">
            <Button variant="outline" onClick={() => setCurrentStep('source')}>Back</Button>
          </CardFooter>
        </Card>
      )}

      {currentStep === 'configure' && sourceType === 'webhook' && (
        <WebhookConfigStep onBack={() => setCurrentStep('source')} />
      )}

      {currentStep === 'configure' && sourceType === 'shopify' && (
        <ShopifyConfigStep onBack={() => setCurrentStep('source')} />
      )}

      {currentStep === 'mapping' && (
        <Card className="rounded-xl shadow-sm border-border">
          <CardHeader>
            <CardTitle>Map Fields</CardTitle>
            <CardDescription>Map the columns from <strong>{fileName}</strong> to Mercury's schema.</CardDescription>
          </CardHeader>
          <CardContent>
            <MappingStep 
              csvHeaders={csvHeaders} 
              sampleData={sampleData} 
              onMappingComplete={handleMappingComplete} 
            />
          </CardContent>
          <CardFooter className="flex justify-between border-t border-border pt-6">
            <Button variant="outline" onClick={() => setCurrentStep('configure')}>Back to Upload</Button>
          </CardFooter>
        </Card>
      )}

      {currentStep === 'progress' && (
        <Card className="rounded-xl shadow-sm border-border text-center py-12">
          <CardContent>
            {isUploading ? (
              <>
                <div className="w-16 h-16 border-4 border-zinc-200 border-t-zinc-900 rounded-full animate-spin mx-auto mb-6"></div>
                <h2 className="text-xl font-bold text-zinc-900 mb-2">Indexing Catalog...</h2>
                <p className="text-zinc-500">Uploading and processing your catalog through Mercury's engine.</p>
              </>
            ) : uploadError ? (
              <>
                <div className="w-16 h-16 rounded-full bg-red-50 flex items-center justify-center mx-auto mb-6">
                  <AlertCircle className="w-8 h-8 text-red-500" />
                </div>
                <h2 className="text-xl font-bold text-red-700 mb-2">Ingestion Failed</h2>
                <p className="text-red-500 mb-6">{uploadError}</p>
                <Button variant="outline" onClick={() => setCurrentStep('mapping')}>Retry Mapping</Button>
              </>
            ) : (
              <>
                <div className="w-16 h-16 rounded-full bg-green-50 flex items-center justify-center mx-auto mb-6">
                  <CheckCircle2 className="w-8 h-8 text-green-500" />
                </div>
                <h2 className="text-xl font-bold text-zinc-900 mb-2">Ingestion Complete</h2>
                <p className="text-zinc-500 mb-6">
                  Successfully processed {uploadStats?.total || 0} products.
                  ({uploadStats?.indexed || 0} indexed, {uploadStats?.errors || 0} errors).
                </p>
                <Button className="bg-zinc-900 text-white" onClick={() => navigate('/catalog')}>
                  View Catalog
                </Button>
              </>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
