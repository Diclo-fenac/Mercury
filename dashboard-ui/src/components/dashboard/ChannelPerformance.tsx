import React from 'react';
import ReactECharts from 'echarts-for-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowUpRight, ArrowDownRight } from 'lucide-react';

export function ChannelPerformance() {
  const option = {
    series: [
      {
        type: 'gauge',
        startAngle: 180,
        endAngle: 0,
        min: 0,
        max: 100,
        splitNumber: 20,
        itemStyle: {
          color: '#18181b', // zinc-900 (black segment)
        },
        progress: {
          show: true,
          width: 32,
          itemStyle: {
            color: '#18181b', // filled color
          }
        },
        pointer: {
          show: false
        },
        axisLine: {
          lineStyle: {
            width: 32,
            color: [[1, '#e4e4e7']] // zinc-200 (gray background)
          }
        },
        axisTick: {
          show: false
        },
        splitLine: {
          show: true,
          length: 32,
          distance: -32,
          lineStyle: {
            color: '#ffffff', // split segments with white
            width: 6
          }
        },
        axisLabel: {
          show: false
        },
        title: {
          show: false
        },
        detail: {
          show: false
        },
        data: [{ value: 65 }]
      }
    ]
  };

  return (
    <Card className="rounded-xl shadow-sm border-border flex flex-col">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-zinc-500 uppercase tracking-wider flex items-center gap-2">
          <span className="w-4 h-4">📈</span> CHANNEL PERFORMANCE
        </CardTitle>
        <div className="w-6 h-6 border border-zinc-200 rounded flex items-center justify-center text-zinc-500 cursor-pointer hover:bg-zinc-50">
          ↗
        </div>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col">
        <div className="relative h-[160px] flex items-center justify-center mt-4">
          <ReactECharts option={option} style={{ height: '240px', width: '100%', position: 'absolute', top: -20 }} />
          <div className="absolute bottom-4 flex flex-col items-center">
            <h3 className="text-2xl font-bold text-zinc-900">16,432</h3>
            <p className="text-sm text-zinc-500">Product Sales</p>
          </div>
        </div>
        
        <div className="mt-auto space-y-4 pt-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-zinc-900"></div>
                <span className="text-sm font-medium text-zinc-900">Website</span>
              </div>
              <p className="text-xs text-zinc-500 ml-4">5,762 Product Sold <span className="text-green-500 ml-1">+1.8%</span></p>
            </div>
            <span className="font-bold text-sm">$1,378,975</span>
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-zinc-300"></div>
                <span className="text-sm font-medium text-zinc-600">Marketplace</span>
              </div>
              <p className="text-xs text-zinc-500 ml-4">6,843 Products Sold <span className="text-red-500 ml-1">-2.8%</span></p>
            </div>
            <span className="font-bold text-sm">$778,975</span>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-zinc-400"></div>
                <span className="text-sm font-medium text-zinc-600">Store</span>
              </div>
              <p className="text-xs text-zinc-500 ml-4">2,123 Products Sold <span className="text-red-500 ml-1">-2.8%</span></p>
            </div>
            <span className="font-bold text-sm">$778,975</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
