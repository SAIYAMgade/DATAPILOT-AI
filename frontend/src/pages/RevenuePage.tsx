import React, { useEffect, useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell
} from 'recharts';
import { api } from '../services/api';
import { TimeSeriesItem, Breakdowns, ParetoData } from '../types';

const COLORS = ['#6366f1', '#38bdf8', '#34d399', '#f59e0b', '#ec4899', '#8b5cf6'];

export const RevenuePage: React.FC = () => {
  const [timeSeries, setTimeSeries] = useState<TimeSeriesItem[]>([]);
  const [breakdowns, setBreakdowns] = useState<Breakdowns | null>(null);
  const [pareto, setPareto] = useState<ParetoData | null>(null);
  const [granularity, setGranularity] = useState<'monthly' | 'weekly'>('monthly');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadRevenueData();
  }, [granularity]);

  const loadRevenueData = async () => {
    try {
      setLoading(true);
      const [ts, br, pt] = await Promise.all([
        api.getTimeSeries(granularity),
        api.getBreakdowns(),
        api.getPareto()
      ]);
      setTimeSeries(ts);
      setBreakdowns(br);
      setPareto(pt);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !breakdowns || !pareto) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[400px]">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Title & Granularity toggle */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100">Revenue Analytics & Distribution</h2>
          <p className="text-xs text-slate-400 mt-1">
            Multidimensional sales breakdowns, cohort trends, and customer concentration analysis.
          </p>
        </div>
        <div className="flex items-center gap-1 bg-slate-900 p-1 rounded-lg border border-slate-800">
          <button
            onClick={() => setGranularity('monthly')}
            className={`px-3 py-1 text-xs rounded font-medium transition ${
              granularity === 'monthly' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Monthly
          </button>
          <button
            onClick={() => setGranularity('weekly')}
            className={`px-3 py-1 text-xs rounded font-medium transition ${
              granularity === 'weekly' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Weekly
          </button>
        </div>
      </div>

      {/* Main Revenue & Growth Chart */}
      <div className="p-6 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
        <h3 className="text-sm font-semibold text-slate-200">Revenue & Period-over-Period Growth</h3>
        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={timeSeries}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="period" stroke="#64748b" tick={{ fontSize: 11 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 11 }} tickFormatter={(val) => `$${(val / 1000).toFixed(0)}k`} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                formatter={(val: any) => [`$${Number(val).toLocaleString()}`, 'Revenue']}
              />
              <Bar dataKey="revenue" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Multi-Column Breakdowns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Category Breakdown */}
        <div className="p-6 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
          <h3 className="text-sm font-semibold text-slate-200">Revenue by Product Category</h3>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={breakdowns.by_category} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis type="number" stroke="#64748b" tick={{ fontSize: 10 }} tickFormatter={(val) => `$${(val / 1000).toFixed(0)}k`} />
                <YAxis dataKey="name" type="category" stroke="#64748b" tick={{ fontSize: 11 }} width={120} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                  formatter={(val: any) => [`$${Number(val).toLocaleString()}`, 'Revenue']}
                />
                <Bar dataKey="revenue" fill="#38bdf8" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Channel Breakdown */}
        <div className="p-6 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
          <h3 className="text-sm font-semibold text-slate-200">Revenue by Acquisition Channel</h3>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={breakdowns.by_channel} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis type="number" stroke="#64748b" tick={{ fontSize: 10 }} tickFormatter={(val) => `$${(val / 1000).toFixed(0)}k`} />
                <YAxis dataKey="channel" type="category" stroke="#64748b" tick={{ fontSize: 11 }} width={110} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                  formatter={(val: any) => [`$${Number(val).toLocaleString()}`, 'Revenue']}
                />
                <Bar dataKey="revenue" fill="#34d399" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Pareto Concentration Analysis */}
      <div className="p-6 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h3 className="text-sm font-semibold text-slate-200">Customer Revenue Concentration (Pareto Curve)</h3>
            <p className="text-xs text-slate-400">Cumulative percentage of revenue generated by descending customer percentiles</p>
          </div>
          <div className="px-3 py-1 rounded bg-indigo-950/40 border border-indigo-800/40 text-xs font-mono text-indigo-300">
            Top 20% generate: {pareto.top_20_pct_generates}% revenue
          </div>
        </div>

        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={pareto.concentration_points}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="customer_pct" stroke="#64748b" tick={{ fontSize: 11 }} tickFormatter={(v) => `${v}% custs`} />
              <YAxis stroke="#64748b" tick={{ fontSize: 11 }} tickFormatter={(v) => `${v}% rev`} domain={[0, 100]} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                formatter={(val: any) => [`${val}%`, 'Cumulative Revenue']}
              />
              <Line type="monotone" dataKey="cumulative_revenue_pct" stroke="#ec4899" strokeWidth={3} dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
