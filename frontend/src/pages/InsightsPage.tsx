import React, { useEffect, useState } from 'react';
import { Sparkles, RefreshCw, AlertCircle, Info, ChevronDown, ChevronUp } from 'lucide-react';
import { api } from '../services/api';
import { BusinessInsightItem } from '../types';

export const InsightsPage: React.FC = () => {
  const [insights, setInsights] = useState<BusinessInsightItem[]>([]);
  const [categoryFilter, setCategoryFilter] = useState<string>('All');
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  useEffect(() => {
    loadInsights();
  }, []);

  const loadInsights = async () => {
    try {
      setLoading(true);
      const res = await api.getInsights();
      setInsights(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    try {
      setRefreshing(true);
      const res = await api.refreshInsights();
      setInsights(res);
    } catch (err) {
      console.error(err);
    } finally {
      setRefreshing(false);
    }
  };

  const filtered = categoryFilter === 'All'
    ? insights
    : insights.filter((i) => i.category.toLowerCase() === categoryFilter.toLowerCase());

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[400px]">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-indigo-400" />
            Deterministic Business Insights Ledger
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Rules-driven analytical findings derived from actual database records. Zero hallucinated commentary.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none"
          >
            <option value="All">All Categories</option>
            <option value="revenue">Revenue</option>
            <option value="retention">Retention</option>
            <option value="risk">Risk</option>
          </select>

          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
            <span>{refreshing ? 'Evaluating Rules...' : 'Re-Evaluate Insights'}</span>
          </button>
        </div>
      </div>

      {/* Insights Cards */}
      <div className="space-y-4">
        {filtered.length === 0 ? (
          <div className="p-8 text-center bg-slate-900 border border-slate-800 rounded-xl text-slate-400 text-xs">
            No insights found for the selected category filter.
          </div>
        ) : (
          filtered.map((item) => {
            const isExpanded = expandedId === item.id;
            return (
              <div
                key={item.id}
                className={`p-6 rounded-xl border transition-all ${
                  item.severity === 'critical'
                    ? 'bg-rose-950/20 border-rose-900/40'
                    : item.severity === 'warning'
                    ? 'bg-amber-950/20 border-amber-900/40'
                    : 'bg-slate-900 border-slate-800'
                }`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="space-y-2 flex-1">
                    <div className="flex items-center gap-2.5">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase tracking-wider ${
                        item.severity === 'critical'
                          ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                          : item.severity === 'warning'
                          ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                          : 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                      }`}>
                        {item.severity}
                      </span>
                      <span className="text-[11px] font-mono text-slate-400 uppercase">
                        {item.category} • Metric: {item.metric_name}
                      </span>
                      <span className="text-[11px] font-mono text-slate-400">
                        Period: {item.comparison_period}
                      </span>
                    </div>

                    <h3 className="text-base font-semibold text-slate-100">{item.title}</h3>
                  </div>

                  <button
                    onClick={() => setExpandedId(isExpanded ? null : item.id)}
                    className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition text-xs flex items-center gap-1 font-mono"
                  >
                    <span>{isExpanded ? 'Hide Evidence' : 'Inspect Evidence'}</span>
                    {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                  </button>
                </div>

                {/* Analytical Limitations */}
                <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-start gap-2 text-xs text-slate-400">
                  <Info className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                  <span className="leading-relaxed">
                    <span className="text-slate-300 font-medium">Analytical Limitation: </span>
                    {item.limitations}
                  </span>
                </div>

                {/* Expanded Supporting Evidence JSON */}
                {isExpanded && (
                  <div className="mt-4 p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-2 animate-fade">
                    <div className="text-[11px] font-mono font-semibold text-slate-300 uppercase tracking-wider">
                      Supporting Verification Evidence
                    </div>
                    <pre className="text-[11px] font-mono text-cyan-300/90 overflow-x-auto p-2 bg-slate-900/60 rounded border border-slate-800/80">
                      {JSON.stringify(item.supporting_evidence, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
