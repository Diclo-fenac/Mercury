import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export function TopProducts() {
  const option = useMemo(() => {
    // Create diagonal stripe pattern for the gray bars
    const patternCanvas = document.createElement('canvas');
    patternCanvas.width = 16;
    patternCanvas.height = 16;
    const ctx = patternCanvas.getContext('2d');
    if (ctx) {
      ctx.fillStyle = '#f4f4f5'; // zinc-100 base
      ctx.fillRect(0, 0, 16, 16);
      ctx.strokeStyle = '#e4e4e7'; // zinc-200 stripe
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(-4, 20);
      ctx.lineTo(20, -4);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(-4, 4);
      ctx.lineTo(4, -4);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(12, 20);
      ctx.lineTo(20, 12);
      ctx.stroke();
    }

    // Dark stripe pattern for the active bar
    const darkPatternCanvas = document.createElement('canvas');
    darkPatternCanvas.width = 16;
    darkPatternCanvas.height = 16;
    const darkCtx = darkPatternCanvas.getContext('2d');
    if (darkCtx) {
      darkCtx.fillStyle = '#27272a'; // zinc-800 base
      darkCtx.fillRect(0, 0, 16, 16);
      darkCtx.strokeStyle = '#3f3f46'; // zinc-700 stripe
      darkCtx.lineWidth = 2;
      darkCtx.beginPath();
      darkCtx.moveTo(-4, 20);
      darkCtx.lineTo(20, -4);
      darkCtx.stroke();
      darkCtx.beginPath();
      darkCtx.moveTo(-4, 4);
      darkCtx.lineTo(4, -4);
      darkCtx.stroke();
      darkCtx.beginPath();
      darkCtx.moveTo(12, 20);
      darkCtx.lineTo(20, 12);
      darkCtx.stroke();
    }

    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' }
      },
      grid: {
        top: '10%',
        left: '5%',
        right: '5%',
        bottom: '10%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: ['Shoes', 'Jacket', 'T-shirt'],
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: '#71717a' }
      },
      yAxis: {
        type: 'value',
        splitLine: {
          lineStyle: { type: 'dashed', color: '#e4e4e7' }
        },
        axisLabel: { color: '#71717a' }
      },
      series: [
        {
          type: 'bar',
          barWidth: '70%',
          itemStyle: {
            borderRadius: [4, 4, 0, 0],
            color: (params: any) => {
              if (params.dataIndex === 0) {
                return {
                  image: darkPatternCanvas,
                  repeat: 'repeat'
                };
              }
              return {
                image: patternCanvas,
                repeat: 'repeat'
              };
            }
          },
          label: {
            show: true,
            position: 'insideBottomLeft',
            distance: 12,
            formatter: '{c}',
            color: (params: any) => (params.dataIndex === 0 ? '#fff' : '#27272a'),
            fontWeight: 'bold',
            fontSize: 16
          },
          data: [180, 87, 56]
        }
      ]
    };
  }, []);

  return (
    <Card className="rounded-xl shadow-sm border-border">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-zinc-500 uppercase tracking-wider flex items-center gap-2">
          <span className="w-4 h-4">📦</span> TOP 3 PRODUCT
        </CardTitle>
        <div className="flex gap-2">
          <div className="text-xs text-zinc-500 border border-zinc-200 rounded px-3 py-1">Daily ⌄</div>
          <div className="w-6 h-6 border border-zinc-200 rounded flex items-center justify-center text-zinc-500 hover:bg-zinc-50 cursor-pointer">
            <span className="text-[10px]">⚖</span>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between mb-4 mt-2">
          <span className="text-sm text-zinc-500">Today's Total Sales :</span>
          <div className="flex items-center gap-1 font-bold text-sm text-zinc-900">
            318 units <div className="w-4 h-4 rounded-full bg-green-100 text-green-600 flex items-center justify-center text-[10px] ml-1">↑</div>
          </div>
        </div>
        <ReactECharts option={option} style={{ height: '240px', width: '100%' }} />
      </CardContent>
    </Card>
  );
}
