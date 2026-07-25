import { useQuery } from '@tanstack/react-query';
import { getAnalytics } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2, Search, Clock, AlertTriangle, TrendingUp, CheckCircle2, Circle } from 'lucide-react';
import ReactECharts from 'echarts-for-react';

export function OverviewDashboard() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['analytics'],
    queryFn: getAnalytics,
    refetchInterval: 10000, // Refetch every 10s
  });

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-64 space-y-4">
        <Loader2 className="h-8 w-8 animate-spin text-zinc-400" />
        <p className="text-zinc-500">Loading analytics...</p>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="flex flex-col items-center justify-center h-64 space-y-4">
        <AlertTriangle className="h-8 w-8 text-red-400" />
        <p className="text-red-500">Failed to load analytics.</p>
      </div>
    );
  }

  const topQueriesOption = {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'value' },
    yAxis: {
      type: 'category',
      data: data.top_queries.map((q: any) => q.query).reverse(),
      axisLabel: { color: '#71717a' }
    },
    series: [
      {
        type: 'bar',
        data: data.top_queries.map((q: any) => q.count).reverse(),
        itemStyle: { color: '#09090b', borderRadius: [0, 4, 4, 0] }
      }
    ]
  };

  const { has_ingested_catalog, has_merchandising_rules, has_live_searches } = data;
  const milestones = [
    true, // 1. Create tenant
    has_ingested_catalog, // 2. Add source
    has_ingested_catalog, // 3. Map fields
    has_ingested_catalog, // 4. Ingest
    has_live_searches, // 5. Test search
    has_live_searches // 6. Copy widget snippet
  ];
  const completedMilestones = milestones.filter(Boolean).length;
  const progressPercent = Math.round((completedMilestones / 6) * 100);
  const allCompleted = completedMilestones === 6;

  return (
    <div className="space-y-6">
      {/* Getting Started Progress */}
      {!allCompleted && (
        <Card className="rounded-xl shadow-sm border-zinc-200 bg-zinc-50/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg font-semibold flex items-center justify-between">
              Getting Started
              <span className="text-sm font-medium text-zinc-500">{progressPercent}% Completed</span>
            </CardTitle>
            <div className="w-full bg-zinc-200 h-2 rounded-full mt-2 overflow-hidden">
              <div 
                className="bg-indigo-500 h-2 rounded-full transition-all duration-500" 
                style={{ width: `${progressPercent}%` }} 
              />
            </div>
          </CardHeader>
          <CardContent className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            <div className="flex items-center gap-3 p-3 rounded-lg border bg-white border-green-200">
              <CheckCircle2 className="w-5 h-5 text-green-500 shrink-0" />
              <div>
                <p className="text-sm font-medium text-zinc-900">1. Create Tenant</p>
                <p className="text-xs text-zinc-500">Organization registered</p>
              </div>
            </div>
            <div className={`flex items-center gap-3 p-3 rounded-lg border ${has_ingested_catalog ? 'bg-white border-green-200' : 'bg-white border-zinc-200'}`}>
              {has_ingested_catalog ? <CheckCircle2 className="w-5 h-5 text-green-500 shrink-0" /> : <Circle className="w-5 h-5 text-zinc-300 shrink-0" />}
              <div>
                <p className="text-sm font-medium text-zinc-900">2. Add Source</p>
                <p className="text-xs text-zinc-500">Connect catalog feed</p>
              </div>
            </div>
            <div className={`flex items-center gap-3 p-3 rounded-lg border ${has_ingested_catalog ? 'bg-white border-green-200' : 'bg-white border-zinc-200'}`}>
              {has_ingested_catalog ? <CheckCircle2 className="w-5 h-5 text-green-500 shrink-0" /> : <Circle className="w-5 h-5 text-zinc-300 shrink-0" />}
              <div>
                <p className="text-sm font-medium text-zinc-900">3. Map Fields</p>
                <p className="text-xs text-zinc-500">Align schema attributes</p>
              </div>
            </div>
            <div className={`flex items-center gap-3 p-3 rounded-lg border ${has_ingested_catalog ? 'bg-white border-green-200' : 'bg-white border-zinc-200'}`}>
              {has_ingested_catalog ? <CheckCircle2 className="w-5 h-5 text-green-500 shrink-0" /> : <Circle className="w-5 h-5 text-zinc-300 shrink-0" />}
              <div>
                <p className="text-sm font-medium text-zinc-900">4. Ingest</p>
                <p className="text-xs text-zinc-500">Sync products to index</p>
              </div>
            </div>
            <div className={`flex items-center gap-3 p-3 rounded-lg border ${has_live_searches ? 'bg-white border-green-200' : 'bg-white border-zinc-200'}`}>
              {has_live_searches ? <CheckCircle2 className="w-5 h-5 text-green-500 shrink-0" /> : <Circle className="w-5 h-5 text-zinc-300 shrink-0" />}
              <div>
                <p className="text-sm font-medium text-zinc-900">5. Test Search</p>
                <p className="text-xs text-zinc-500">Verify in playground</p>
              </div>
            </div>
            <div className={`flex items-center gap-3 p-3 rounded-lg border ${has_live_searches ? 'bg-white border-green-200' : 'bg-white border-zinc-200'}`}>
              {has_live_searches ? <CheckCircle2 className="w-5 h-5 text-green-500 shrink-0" /> : <Circle className="w-5 h-5 text-zinc-300 shrink-0" />}
              <div>
                <p className="text-sm font-medium text-zinc-900">6. Copy Widget</p>
                <p className="text-xs text-zinc-500">Embed snippet on site</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Top Row: KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="rounded-xl shadow-sm border-border">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-zinc-500 uppercase tracking-wider">Total Queries</CardTitle>
            <Search className="w-4 h-4 text-zinc-400" />
          </CardHeader>
          <CardContent>
            <h2 className="text-3xl font-bold text-zinc-900">{data.total_queries}</h2>
            <p className="text-xs text-zinc-500 mt-1">All time search volume</p>
          </CardContent>
        </Card>

        <Card className="rounded-xl shadow-sm border-border">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-zinc-500 uppercase tracking-wider">Click-Through Rate</CardTitle>
            <TrendingUp className="w-4 h-4 text-zinc-400" />
          </CardHeader>
          <CardContent>
            <h2 className="text-3xl font-bold text-zinc-900">{data.click_through_rate}%</h2>
            <p className="text-xs text-zinc-500 mt-1">Percentage of searches leading to a click</p>
          </CardContent>
        </Card>

        <Card className="rounded-xl shadow-sm border-border">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-zinc-500 uppercase tracking-wider">Avg Latency</CardTitle>
            <Clock className="w-4 h-4 text-zinc-400" />
          </CardHeader>
          <CardContent>
            <h2 className="text-3xl font-bold text-zinc-900">{data.average_latency_ms} <span className="text-lg">ms</span></h2>
            <p className="text-xs text-zinc-500 mt-1">End-to-end response time</p>
          </CardContent>
        </Card>

        <Card className="rounded-xl shadow-sm border-border">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-zinc-500 uppercase tracking-wider">Zero Results</CardTitle>
            <AlertTriangle className="w-4 h-4 text-zinc-400" />
          </CardHeader>
          <CardContent>
            <h2 className="text-3xl font-bold text-zinc-900">{data.zero_result_count}</h2>
            <p className="text-xs text-zinc-500 mt-1">Queries with no matches</p>
          </CardContent>
        </Card>
      </div>
      
      {/* Bottom Row: Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="rounded-xl shadow-sm border-border lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-zinc-500" />
              Top Search Queries
            </CardTitle>
          </CardHeader>
          <CardContent>
            {data.top_queries.length > 0 ? (
              <ReactECharts option={topQueriesOption} style={{ height: '350px', width: '100%' }} />
            ) : (
              <div className="h-[350px] flex items-center justify-center text-zinc-500">
                No search queries recorded yet.
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
