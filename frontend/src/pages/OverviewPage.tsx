import React, { useEffect, useState } from 'react';
import {
  DollarSign, ShoppingCart, Users, AlertTriangle, ArrowUpRight, ArrowDownRight,
  TrendingUp, Calendar, Info
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import { api } from '../services/api';
import { ExecutiveMetrics, TimeSeriesItem, BusinessInsightItem } from '../types';

export const OverviewPage: React.FC = () => {
  const [metrics, setMetrics] = useState<ExecutiveMetrics | null>(null);
  const [timeSeries, setTimeSeries] = useState<TimeSeriesItem[]>([]);
  const [insights, setInsights] = useState<BusinessInsightItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [m, ts, ins] = await Promise.all([
        api.getExecutiveSummary(),
        api.getTimeSeries('monthly'),
        api.getInsights()
      ]);
      setMetrics(m);
      setTimeSeries(ts);
      setInsights(ins);
    } catch (err: any) {
      setError(err.message || 'Failed to load executive overview data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          <div className="text-xs text-slate-400 font-mono">Loading authoritative metrics...</div>
        </div>
      </div>
    );
  }

  if (error || !metrics) {
    return (
      <div className="p-8">
        <div className="p-4 bg-rose-950/30 border border-rose-800/40 rounded-xl text-rose-300 text-sm">
          Failed to load metrics: {error}
        </div>
      </div>
    );
  }

  const m = metrics.metrics;
  const p = metrics.period;

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 tracking-tight">Executive Performance Overview</h2>
          <p className="text-xs text-slate-400 mt-1">
            Authoritative transactional metrics computed directly from PostgreSQL ledger.
          </p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700/80 text-xs text-slate-300 font-mono">
          <Calendar className="w-3.5 h-3.5 text-indigo-400" />
          <span>{p.start_date} → {p.end_date} (90-day window)</span>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Net Revenue */}
        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 shadow-sm space-y-3">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Total Net Revenue</span>
            <DollarSign className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100 font-mono">
            ${m.total_revenue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="flex items-center gap-1.5 text-xs">
            {m.revenue_growth_pct >= 0 ? (
              <span className="flex items-center text-emerald-400 font-medium font-mono">
                <ArrowUpRight className="w-3.5 h-3.5" />
                +{m.revenue_growth_pct}%
              </span>
            ) : (
              <span className="flex items-center text-rose-400 font-medium font-mono">
                <ArrowDownRight className="w-3.5 h-3.5" />
                {m.revenue_growth_pct}%
              </span>
            )}
            <span className="text-slate-400">vs preceding 90d</span>
          </div>
        </div>

        {/* Average Order Value (AOV) */}
        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 shadow-sm space-y-3">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Average Order Value</span>
            <ShoppingCart className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100 font-mono">
            ${m.average_order_value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="flex items-center gap-1.5 text-xs">
            {m.aov_growth_pct >= 0 ? (
              <span className="flex items-center text-emerald-400 font-medium font-mono">
                <ArrowUpRight className="w-3.5 h-3.5" />
                +{m.aov_growth_pct}%
              </span>
            ) : (
              <span className="flex items-center text-rose-400 font-medium font-mono">
                <ArrowDownRight className="w-3.5 h-3.5" />
                {m.aov_growth_pct}%
              </span>
            )}
            <span className="text-slate-400">AOV delta</span>
          </div>
        </div>

        {/* Active Accounts */}
        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 shadow-sm space-y-3">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Active Accounts (30d)</span>
            <Users className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100 font-mono">
            {m.active_customers_30d.toLocaleString()}
          </div>
          <div className="text-xs text-slate-400">
            Of {m.total_registered_customers.toLocaleString()} total registered
          </div>
        </div>

        {/* Churn Risk */}
        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 shadow-sm space-y-3">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>High Churn Risk</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-400 font-mono">
            {m.high_risk_customers.toLocaleString()}
          </div>
          <div className="text-xs text-slate-400">
            Accounts facing &gt;60d projected inactivity
          </div>
        </div>
      </div>

      {/* Revenue Trajectory Chart */}
      <div className="p-6 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-slate-200">Revenue Trajectory Over Time</h3>
            <p className="text-xs text-slate-400">Monthly aggregate net revenue ($USD) computed with window functions</p>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-indigo-400 font-medium">
            <TrendingUp className="w-4 h-4" />
            <span>Monthly Aggregates</span>
          </div>
        </div>

        <div className="h-72 w-full pt-4">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={timeSeries} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="colorRev" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="period" stroke="#64748b" tick={{ fontSize: 11 }} />
              <YAxis
                stroke="#64748b"
                tick={{ fontSize: 11 }}
                tickFormatter={(val) => `$${(val / 1000).toFixed(0)}k`}
              />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                formatter={(value: any) => [`$${Number(value).toLocaleString()}`, 'Revenue']}
              />
              <Area type="monotone" dataKey="revenue" stroke="#818cf8" strokeWidth={2} fillOpacity={1} fill="url(#colorRev)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Verified Business Insights Section */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-200">Critical Business Insights</h3>
          <span className="text-xs text-slate-400">Deterministic Engine Output</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {insights.slice(0, 3).map((ins) => (
            <div
              key={ins.id}
              className={`p-4 rounded-xl border space-y-2 ${
                ins.severity === 'critical'
                  ? 'bg-rose-950/20 border-rose-800/40 text-rose-200'
                  : ins.severity === 'warning'
                  ? 'bg-amber-950/20 border-amber-800/40 text-amber-200'
                  : 'bg-indigo-950/20 border-indigo-800/40 text-indigo-200'
              }`}
            >
              <div className="flex items-center justify-between text-xs font-semibold">
                <span className="uppercase tracking-wider font-mono text-[10px]">{ins.category}</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-900/60 border border-slate-700/50">
                  {ins.severity}
                </span>
              </div>
              <div className="font-medium text-xs text-slate-100">{ins.title}</div>
              <div className="text-[11px] text-slate-400">
                Window: <span className="text-slate-300 font-mono">{ins.comparison_period}</span>
              </div>
              <div className="pt-2 border-t border-slate-800/60 flex items-center gap-1.5 text-[10px] text-slate-400">
                <Info className="w-3 h-3 text-slate-400 shrink-0" />
                <span className="truncate">{ins.limitations}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
