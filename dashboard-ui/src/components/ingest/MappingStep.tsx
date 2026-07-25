import React, { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';

interface MappingStepProps {
  csvHeaders: string[];
  sampleData: any[];
  onMappingComplete: (mapping: Record<string, string>) => void;
}

export function MappingStep({ csvHeaders, sampleData, onMappingComplete }: MappingStepProps) {
  // Mercury's standard schema fields
  const targetFields = [
    { id: 'id', name: 'Product ID (Required)', required: true },
    { id: 'name', name: 'Product Name', required: true },
    { id: 'description', name: 'Description', required: false },
    { id: 'price', name: 'Price', required: true },
    { id: 'image_url', name: 'Image URL', required: false },
    { id: 'category', name: 'Category', required: false },
  ];

  // State to hold the mapping: { [targetFieldId]: csvHeader }
  const [mapping, setMapping] = useState<Record<string, string>>(() => {
    const initialMapping: Record<string, string> = {};
    targetFields.forEach(tf => {
      const match = csvHeaders.find(h => h.toLowerCase() === tf.id.toLowerCase() || h.toLowerCase() === tf.name.toLowerCase());
      if (match) initialMapping[tf.id] = match;
    });
    return initialMapping;
  });

  const handleSelect = (targetId: string, csvHeader: string) => {
    setMapping(prev => ({ ...prev, [targetId]: csvHeader }));
  };

  const getSampleValue = (header: string) => {
    if (!sampleData || sampleData.length === 0) return 'N/A';
    return String(sampleData[0][header] || 'N/A').slice(0, 30);
  };

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="bg-blue-50 border border-blue-200 text-blue-800 rounded-lg p-4 text-sm">
        <strong>Strict Mapping Mode:</strong> You must manually map your uploaded CSV columns to Mercury's target schema. This ensures zero data pollution in your search index.
      </div>

      <div className="border border-border rounded-xl overflow-hidden">
        <Table>
          <TableHeader className="bg-zinc-50">
            <TableRow>
              <TableHead className="w-[250px]">Mercury Target Field</TableHead>
              <TableHead>Your CSV Column</TableHead>
              <TableHead className="hidden md:table-cell text-zinc-400">Sample Value from row 1</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {targetFields.map((field) => (
              <TableRow key={field.id} className="bg-white">
                <TableCell className="font-medium text-zinc-900">
                  {field.name}
                  {field.required && <Badge variant="destructive" className="ml-2 text-[10px]">Required</Badge>}
                </TableCell>
                <TableCell>
                  <Select value={mapping[field.id]} onValueChange={(val: string) => handleSelect(field.id, val)}>
                    <SelectTrigger className="w-full bg-white">
                      <SelectValue placeholder="Select a column..." />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ignore" className="text-zinc-500 italic">-- Ignore this field --</SelectItem>
                      {csvHeaders.map(header => (
                        <SelectItem key={header} value={header}>{header}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </TableCell>
                <TableCell className="hidden md:table-cell text-zinc-500 text-sm">
                  {mapping[field.id] && mapping[field.id] !== 'ignore' 
                    ? <span className="font-mono bg-zinc-100 px-2 py-1 rounded">{getSampleValue(mapping[field.id])}</span>
                    : <span className="italic">Not mapped</span>}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <div className="flex justify-end pt-4">
        <Button 
          className="bg-zinc-900 text-white hover:bg-zinc-800" 
          onClick={() => onMappingComplete(mapping)}
        >
          Start Ingestion
        </Button>
      </div>
    </div>
  );
}
