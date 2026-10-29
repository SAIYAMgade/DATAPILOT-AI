import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { CohortData } from '../types';

export const CohortsPage: React.FC = () => {
  const [cohortData, setCohortData] = useState<CohortData | null>(null);
  const [viewMode, setViewMode] = useState<'retention' | 'revenue'>('retention');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCohorts();
  }, []);

  const loadCohorts = async () => {
    try {
      setLoading(true);
      const res = await api.getCohortMatrix();
      setCohortData(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getHeatmapColor = (pct: number | null) => {
    if (pct === null) return 'bg-slate-950 text-slate-400';
    if (pct >= 80) return 'bg-emerald-900/60 text-emerald-200';
    if (pct >= 60) return 'bg-emerald-950/80 text-emerald-300';
    if (pct >= 40) return 'bg-indigo-950/60 text-indigo-300';
    if (pct >= 20) return 'bg-slate-800 text-slate-300';
    return 'bg-slate-900 text-slate-400';
  };

  if (loading || !cohortData) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[400px]">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const matrix = viewMode === 'retention' ? cohortData.retention_matrix : cohortData.revenue_matrix;

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100">Customer Cohort Retention Matrix</h2>
          <p className="text-xs text-slate-400 mt-1">
            Track customer activity retention and cohort lifetime revenue by acquisition month.
          </p>
        </div>
        <div className="flex items-center gap-1 bg-slate-900 p-1 rounded-lg border border-slate-800">
          <button
            onClick={() => setViewMode('retention')}
            className={`px-3 py-1 text-xs rounded font-medium transition ${
              viewMode === 'retention' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Retention Rate (%)
          </button>
          <button
            onClick={() => setViewMode('revenue')}
            className={`px-3 py-1 text-xs rounded font-medium transition ${
              viewMode === 'revenue' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Cohort Revenue ($)
          </button>
        </div>
      </div>

      {/* Cohort Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <div className="text-xs text-slate-400">Total Tracked Cohorts</div>
          <div className="text-2xl font-bold text-slate-100 font-mono mt-1">
            {cohortData.cohort_summary.length}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Monthly acquisition groups</div>
        </div>
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <div className="text-xs text-slate-400">Avg Month-1 Retention</div>
          <div className="text-2xl font-bold text-emerald-400 font-mono mt-1">
            {(
              cohortData.cohort_summary
                .filter((s) => s.month_1_retention_pct !== null)
                .reduce((acc, s) => acc + (s.month_1_retention_pct || 0), 0) /
              Math.max(1, cohortData.cohort_summary.filter((s) => s.month_1_retention_pct !== null).length)
            ).toFixed(1)}%
          </div>
          <div className="text-[11px] text-slate-400 mt-1">First recurring transaction rate</div>
        </div>
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <div className="text-xs text-slate-400">Rule Definition</div>
          <div className="text-xs text-slate-300 mt-1 font-mono leading-relaxed">
            Active = ≥1 qualifying completed transaction in the respective month.
          </div>
        </div>
      </div>

      {/* Heatmap Matrix Table */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-medium">
              <tr>
                <th className="py-3 px-4 sticky left-0 bg-slate-950 z-10">Cohort</th>
                <th className="py-3 px-4 text-right">Size</th>
                {cohortData.period_columns.map((p) => (
                  <th key={p} className="py-3 px-3 text-center font-mono">
                    {p}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/40 font-mono">
              {matrix.map((row) => (
                <tr key={row.cohort} className="hover:bg-slate-800/30">
                  <td className="py-2.5 px-4 sticky left-0 bg-slate-900 font-semibold text-slate-200 z-10 border-r border-slate-800">
                    {row.cohort}
                  </td>
                  <td className="py-2.5 px-4 text-right text-slate-300 font-medium border-r border-slate-800">
                    {row.size}
                  </td>
                  {cohortData.period_columns.map((p) => {
                    const val = row[p];
                    return (
                      <td
                        key={p}
                        className={`py-2.5 px-3 text-center border-r border-slate-800/30 text-[11px] font-medium transition ${
                          viewMode === 'retention' ? getHeatmapColor(val) : 'bg-slate-900 text-slate-300'
                        }`}
                      >
                        {val === null
                          ? '—'
                          : viewMode === 'retention'
                          ? `${val}%`
                          : `$${Number(val).toLocaleString()}`}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-400 flex items-center justify-between">
        <span>Note: Cells marked with &apos;—&apos; denote future observation windows that have not yet elapsed.</span>
        <span className="font-mono text-slate-400">Anti-Leakage Standard</span>
      </div>
    </div>
  );
};
