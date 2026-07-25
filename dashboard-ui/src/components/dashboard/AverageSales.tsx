import React from 'react';
import ReactECharts from 'echarts-for-react';
import * as echarts from 'echarts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowUpRight } from 'lucide-react';

export function AverageSales() {
  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#18181b', // zinc-900
      borderColor: '#27272a',
      textStyle: { color: '#fafafa' },
      padding: [12, 16],
      axisPointer: {
        type: 'line',
        lineStyle: {
          color: '#bfdbfe',
          width: 24,
          type: 'solid',
          opacity: 0.3
        }
      }
    },
    grid: {
      top: '15%',
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'],
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        color: '#71717a', // zinc-500
        margin: 16,
      },
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: {
        lineStyle: {
          color: '#f4f4f5', // zinc-100
          type: 'dashed'
        }
      },
      axisLabel: {
        color: '#71717a',
        formatter: (value: number) => `$${value / 1000}k`
      }
    },
    series: [
      {
        name: 'Target',
        type: 'line',
        smooth: true,
        data: [18000, 22000, 22000, 26000, 22000, 22000, 25000],
        lineStyle: { color: '#e4e4e7', width: 2 }, // zinc-200
        symbol: 'circle',
        symbolSize: 8,
        itemStyle: {
          color: '#fff',
          borderColor: '#e4e4e7',
          borderWidth: 2
        }
      },
      {
        name: 'Revenue',
        type: 'line',
        smooth: true,
        data: [20000, 16000, 19000, 27000, 23000, 21000, 13000],
        lineStyle: { color: '#3b82f6', width: 2 }, // blue-500
        symbol: 'circle',
        symbolSize: 8,
        itemStyle: {
          color: '#fff',
          borderColor: '#3b82f6',
          borderWidth: 2
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(59, 130, 246, 0.2)' },
            { offset: 1, color: 'rgba(59, 130, 246, 0.0)' }
          ])
        }
      }
    ]
  };

  return (
    <Card className="rounded-xl shadow-sm border-border overflow-hidden">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div className="space-y-1">
          <CardTitle className="text-sm font-medium text-zinc-500 uppercase tracking-wider flex items-center gap-2">
            <span className="w-4 h-4 text-zinc-400">📊</span> AVERAGE SALES
          </CardTitle>
          <div className="flex items-baseline gap-2">
            <h2 className="text-3xl font-bold tracking-tight text-zinc-900">$1,389.652</h2>
            <div className="flex items-center text-green-500 bg-green-50 px-2 py-0.5 rounded text-xs font-medium">
              <ArrowUpRight className="w-3 h-3 mr-1" />
              1.8%
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          {/* Mock filters to match image */}
          <div className="text-xs text-zinc-500 border border-zinc-200 rounded px-3 py-1">All Product ⌄</div>
          <div className="text-xs text-zinc-500 border border-zinc-200 rounded px-3 py-1">2025 ⌄</div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-4 mb-4 text-sm">
          <div className="flex items-center gap-1.5 text-zinc-500">
            <div className="w-2 h-2 rounded-full bg-blue-500"></div> Revenue
          </div>
          <div className="flex items-center gap-1.5 text-zinc-500">
            <div className="w-2 h-2 rounded-full bg-zinc-300"></div> Target
          </div>
        </div>
        <ReactECharts option={option} style={{ height: '300px', width: '100%' }} />
      </CardContent>
    </Card>
  );
}
