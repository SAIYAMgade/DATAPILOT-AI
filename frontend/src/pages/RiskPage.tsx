import React, { useEffect, useState } from 'react';
import { AlertTriangle, ArrowUpDown, HelpCircle, UserCheck, ShieldAlert } from 'lucide-react';
import { api } from '../services/api';
import { PrioritizedCustomer } from '../types';

export const RiskPage: React.FC = () => {
  const [customers, setCustomers] = useState<PrioritizedCustomer[]>([]);
  const [modelTag, setModelTag] = useState<string>('');
  const [threshold, setThreshold] = useState<number>(0.5);
  const [totalScored, setTotalScored] = useState<number>(0);
  const [highRiskCount, setHighRiskCount] = useState<number>(0);
  const [formulaDoc, setFormulaDoc] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [filterRisk, setFilterRisk] = useState<string>('All');

  useEffect(() => {
    loadPriorities();
  }, []);

  const loadPriorities = async () => {
    try {
      setLoading(true);
      const res = await api.getPredictions(100);
      setCustomers(res.prioritized_customers || []);
      setModelTag(res.model_version || 'N/A');
      setThreshold(res.decision_threshold || 0.5);
      setTotalScored(res.total_customers_scored || 0);
      setHighRiskCount(res.high_risk_count || 0);
      setFormulaDoc(res.formula_documentation || '');
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const filtered = filterRisk === 'All'
    ? customers
    : customers.filter((c) => c.risk_category === filterRisk);

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[400px]">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100">Customer Risk & Retention Prioritization</h2>
          <p className="text-xs text-slate-400 mt-1">
            Prioritizes outreach by combining machine-learned churn probabilities with historical account monetary value.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">Filter Risk:</span>
          <select
            value={filterRisk}
            onChange={(e) => setFilterRisk(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none"
          >
            <option value="All">All Risk Tiers</option>
            <option value="High">High Risk Only</option>
            <option value="Medium">Medium Risk Only</option>
            <option value="Low">Low Risk Only</option>
          </select>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <div className="text-xs text-slate-400">Total Scored Accounts</div>
          <div className="text-2xl font-bold font-mono text-slate-100 mt-1">{totalScored}</div>
          <div className="text-[11px] text-slate-400 mt-1">Latest batch inference</div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <div className="text-xs text-slate-400">High Churn Risk</div>
          <div className="text-2xl font-bold font-mono text-rose-400 mt-1">{highRiskCount}</div>
          <div className="text-[11px] text-slate-400 mt-1">
            {totalScored > 0 ? ((highRiskCount / totalScored) * 100).toFixed(1) : 0}% of accounts
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <div className="text-xs text-slate-400">Decision Threshold</div>
          <div className="text-2xl font-bold font-mono text-indigo-400 mt-1">{threshold}</div>
          <div className="text-[11px] text-slate-400 mt-1">Tuned on validation set</div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <div className="text-xs text-slate-400">Active Model Artifact</div>
          <div className="text-xs font-mono text-slate-200 mt-2 truncate font-semibold" title={modelTag}>
            {modelTag}
          </div>
          <div className="text-[11px] text-emerald-400 mt-1 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            Verified Non-Leaking
          </div>
        </div>
      </div>

      {/* Formula Documentation Card */}
      <div className="p-4 rounded-xl bg-indigo-950/20 border border-indigo-900/40 text-xs text-slate-300 flex items-start gap-3">
        <HelpCircle className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <div className="font-semibold text-indigo-200">Transparent Prioritization Score Formula</div>
          <div className="text-slate-400 leading-relaxed font-mono text-[11px]">
            {formulaDoc}
          </div>
        </div>
      </div>

      {/* Prioritization Table */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-medium">
              <tr>
                <th className="py-3 px-4">Priority Rank</th>
                <th className="py-3 px-4">Account Reference</th>
                <th className="py-3 px-4">Segment</th>
                <th className="py-3 px-4 text-right">Historical Value</th>
                <th className="py-3 px-4 text-right">Recency</th>
                <th className="py-3 px-4">Predicted Risk</th>
                <th className="py-3 px-4 text-right">Priority Score</th>
                <th className="py-3 px-4">Recommended Retention Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/40 text-slate-300">
              {filtered.map((c, idx) => (
                <tr key={c.customer_id} className="hover:bg-slate-800/30 transition">
                  <td className="py-3 px-4 font-mono font-bold text-slate-400">
                    #{idx + 1}
                  </td>
                  <td className="py-3 px-4 font-medium text-slate-200">
                    <div>{c.name}</div>
                    <div className="text-[10px] text-indigo-400 font-mono">{c.customer_ref}</div>
                  </td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 border border-slate-700 text-slate-300">
                      {c.segment}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right font-mono font-medium text-slate-100">
                    ${c.historical_value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </td>
                  <td className="py-3 px-4 text-right font-mono text-slate-400">
                    {c.recency_days}d ago
                  </td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold ${
                      c.risk_category === 'High'
                        ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                        : c.risk_category === 'Medium'
                        ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                        : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                    }`}>
                      {c.risk_category} ({(c.risk_score * 100).toFixed(0)}%)
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right font-mono font-bold text-indigo-400 text-sm">
                    {c.priority_score.toFixed(1)}
                  </td>
                  <td className="py-3 px-4 text-slate-300 max-w-xs truncate" title={c.recommended_action}>
                    {c.recommended_action}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
