import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import Papa from 'papaparse';
import { UploadCloud, File, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

interface FileUploadStepProps {
  onFileParsed: (headers: string[], data: any[], filename: string) => void;
}

export function FileUploadStep({ onFileParsed }: FileUploadStepProps) {
  const [error, setError] = useState<string | null>(null);
  const [isParsing, setIsParsing] = useState(false);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setError(null);
    setIsParsing(true);

    if (file.type === 'text/csv' || file.name.endsWith('.csv')) {
      Papa.parse(file, {
        header: true,
        skipEmptyLines: true,
        complete: (results) => {
          setIsParsing(false);
          if (results.errors.length > 0) {
            setError(`Error parsing CSV: ${results.errors[0].message}`);
            return;
          }
          if (results.meta.fields && results.data.length > 0) {
            onFileParsed(results.meta.fields, results.data, file.name);
          } else {
            setError('The CSV file appears to be empty or lacks headers.');
          }
        },
        error: (err) => {
          setIsParsing(false);
          setError(err.message);
        }
      });
    } else if (file.type === 'application/json' || file.name.endsWith('.json')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const json = JSON.parse(e.target?.result as string);
          const dataArray = Array.isArray(json) ? json : [json];
          if (dataArray.length === 0) throw new Error('JSON array is empty.');
          const headers = Object.keys(dataArray[0]);
          onFileParsed(headers, dataArray, file.name);
        } catch (err: any) {
          setError(`Invalid JSON: ${err.message}`);
        } finally {
          setIsParsing(false);
        }
      };
      reader.readAsText(file);
    } else {
      setIsParsing(false);
      setError('Unsupported file format. Please upload a CSV or JSON file.');
    }
  }, [onFileParsed]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/json': ['.json']
    },
    maxFiles: 1
  });

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div 
        {...getRootProps()} 
        className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors ${
          isDragActive ? 'border-zinc-900 bg-zinc-50' : 'border-zinc-200 hover:border-zinc-300 hover:bg-zinc-50/50'
        }`}
      >
        <input {...getInputProps()} />
        <div className="w-16 h-16 rounded-full bg-zinc-100 flex items-center justify-center mx-auto mb-4">
          <UploadCloud className="w-8 h-8 text-zinc-500" />
        </div>
        <h3 className="text-lg font-semibold text-zinc-900 mb-1">
          {isDragActive ? 'Drop the file here' : 'Click or drag file to upload'}
        </h3>
        <p className="text-zinc-500 text-sm mb-4">
          Support for a single CSV or JSON file containing your product catalog.
        </p>
        <Button variant="secondary" className="pointer-events-none">
          Browse Files
        </Button>
      </div>

      <div className="text-sm text-zinc-500 flex items-center justify-center gap-2">
        <File className="w-4 h-4" />
        All parsing is done locally in your browser. Your data is secure.
      </div>
    </div>
  );
}
