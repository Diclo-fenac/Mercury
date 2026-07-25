import React from 'react';
import ReactECharts from 'echarts-for-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export function TotalVisitors() {
  // Generate mock heatmap data
  const hours = ['09.00 - 12.00', '12.00 - 15.00', '15.00 - 18.00'];
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'];
  
  const data = [];
  for (let i = 0; i < hours.length; i++) {
    for (let j = 0; j < days.length; j++) {
      // Random value between 0 and 100
      data.push([j, i, Math.floor(Math.random() * 100)]);
    }
  }

  const option = {
    tooltip: {
      position: 'top',
      backgroundColor: '#18181b',
      borderColor: '#27272a',
      textStyle: { color: '#fff' },
      formatter: (params: any) => `${params.value[2]} visitors`
    },
    grid: {
      top: '20%',
      bottom: '5%',
      left: '25%',
      right: '5%'
    },
    xAxis: {
      type: 'category',
      data: days,
      splitArea: { show: true },
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#71717a', fontSize: 10 }
    },
    yAxis: {
      type: 'category',
      data: hours,
      splitArea: { show: true },
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#71717a', fontSize: 10, margin: 16 }
    },
    visualMap: {
      show: false,
      min: 0,
      max: 100,
      inRange: {
        color: ['#f4f4f5', '#d4d4d8', '#71717a', '#27272a', '#09090b'] // zinc scale
      }
    },
    series: [
      {
        type: 'heatmap',
        data: data,
        label: { show: false },
        itemStyle: {
          borderColor: '#fff',
          borderWidth: 2,
          borderRadius: 4
        }
      }
    ]
  };

  return (
    <Card className="rounded-xl shadow-sm border-border flex flex-col">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-zinc-500 uppercase tracking-wider flex items-center gap-2">
          <span className="w-4 h-4">👁</span> TOTAL VISITOR
        </CardTitle>
        <div className="flex gap-2">
          <div className="text-xs text-zinc-500 border border-zinc-200 rounded px-3 py-1">Daily ⌄</div>
          <div className="w-6 h-6 border border-zinc-200 rounded flex items-center justify-center text-zinc-500 hover:bg-zinc-50 cursor-pointer">
            ↗
          </div>
        </div>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col justify-between pt-4">
        <div className="flex items-baseline gap-2 mb-6">
          <h2 className="text-4xl font-bold tracking-tight text-zinc-900">3,247</h2>
          <div className="flex items-center text-green-500 bg-green-50 px-2 py-0.5 rounded text-xs font-medium">
            ↗ 1.8%
          </div>
          <span className="text-sm text-zinc-500 ml-1">Visitor</span>
        </div>

        <div className="space-y-3 mb-6 flex-1">
          <div className="flex justify-between items-center text-sm">
            <span className="text-zinc-500">Marketplace :</span>
            <span className="font-bold">300 people <span className="text-red-500 ml-1">↓</span></span>
          </div>
          <div className="flex justify-between items-center text-sm">
            <span className="text-zinc-500">Website :</span>
            <span className="font-bold">250 people <span className="text-green-500 ml-1">↑</span></span>
          </div>
          <div className="flex justify-between items-center text-sm">
            <span className="text-zinc-500">Store :</span>
            <span className="font-bold">400 people <span className="text-green-500 ml-1">↑</span></span>
          </div>
        </div>

        <div className="h-[120px] w-full">
          <ReactECharts option={option} style={{ height: '100%', width: '100%' }} />
        </div>
      </CardContent>
    </Card>
  );
}
