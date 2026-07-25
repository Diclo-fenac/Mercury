import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { MoreHorizontal } from 'lucide-react';

export function RecentActivity() {
  const outgoing = [
    { name: 'Red Jacket', qty: 2, time: '5 minutes ago', price: '$1,500', color: 'bg-red-600' }
  ];
  
  const incoming = [
    { name: 'Black Jacket', qty: 2, time: '5 minutes ago', price: '$1,500', color: 'bg-zinc-900' }
  ];

  const ItemRow = ({ item }: { item: any }) => (
    <div className="flex items-center justify-between p-3 rounded-lg border border-zinc-100 bg-zinc-50/50 hover:bg-zinc-50 transition-colors">
      <div className="flex items-center gap-3">
        <div className={`w-10 h-10 rounded-md flex items-center justify-center ${item.color}`}>
           <span className="text-white text-xs font-bold">🧥</span>
        </div>
        <div>
          <h4 className="font-semibold text-sm text-zinc-900">{item.name}</h4>
          <p className="text-xs text-zinc-500">Qty : {item.qty} <span className="text-red-400 ml-1">{item.time}</span></p>
        </div>
      </div>
      <div className="flex flex-col items-end gap-1">
        <Button variant="ghost" size="icon" className="h-6 w-6 text-zinc-400">
          <MoreHorizontal className="h-4 w-4" />
        </Button>
        <span className="font-bold text-sm text-zinc-900">{item.price}</span>
      </div>
    </div>
  );

  return (
    <Card className="rounded-xl shadow-sm border-border flex flex-col h-full">
      <CardHeader className="flex flex-row items-center justify-between pb-4">
        <CardTitle className="text-sm font-medium text-zinc-500 uppercase tracking-wider flex items-center gap-2">
          <span className="w-4 h-4">⏱</span> RECENT ACTIVITY
        </CardTitle>
        <div className="w-6 h-6 border border-zinc-200 rounded flex items-center justify-center text-zinc-500 cursor-pointer hover:bg-zinc-50">
          ↗
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        <div>
          <h3 className="text-sm font-medium text-zinc-900 mb-3">Outgoing Products</h3>
          <div className="space-y-3">
            {outgoing.map((item, i) => <ItemRow key={i} item={item} />)}
          </div>
        </div>
        
        <div>
          <h3 className="text-sm font-medium text-zinc-900 mb-3">Incoming Products</h3>
          <div className="space-y-3">
            {incoming.map((item, i) => <ItemRow key={i} item={item} />)}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
