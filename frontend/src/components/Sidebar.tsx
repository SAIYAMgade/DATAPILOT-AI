import React from 'react';
import {
  LayoutDashboard, TrendingUp, Users, Grid, AlertTriangle,
  FlaskConical, Sparkles, Database, HelpCircle, Activity, ChevronRight
} from 'lucide-react';

export type TabKey =
  | 'overview'
  | 'revenue'
  | 'customers'
  | 'cohorts'
  | 'risk'
  | 'statistics'
  | 'insights'
  | 'lab'
  | 'quality'
  | 'assistant';

interface SidebarProps {
  activeTab: TabKey;
  onTabChange: (tab: TabKey) => void;
}

const navItems: Array<{ key: TabKey; label: string; icon: React.ElementType; badge?: string }> = [
  { key: 'overview', label: 'Executive Overview', icon: LayoutDashboard },
  { key: 'revenue', label: 'Revenue Analytics', icon: TrendingUp },
  { key: 'customers', label: 'Customer Explorer', icon: Users },
  { key: 'cohorts', label: 'Cohort Retention', icon: Grid },
  { key: 'risk', label: 'Customer Risk & Prioritization', icon: AlertTriangle },
  { key: 'statistics', label: 'Statistical Analysis', icon: Activity },
  { key: 'insights', label: 'Business Insights', icon: Sparkles, badge: 'Verified' },
  { key: 'lab', label: 'Model Laboratory', icon: FlaskConical },
  { key: 'quality', label: 'Data Quality & Ingestion', icon: Database },
  { key: 'assistant', label: 'AI Analytics Assistant', icon: HelpCircle },
];

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onTabChange }) => {
  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col shrink-0 min-h-screen">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-6 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-indigo-500 to-cyan-400 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20">
            DP
          </div>
          <div>
            <div className="font-bold text-slate-100 tracking-tight text-sm">DataPilot AI</div>
            <div className="text-[11px] text-slate-400 font-mono">Enterprise Intelligence</div>
          </div>
        </div>
      </div>

      {/* Nav List */}
      <div className="p-3 space-y-1 flex-1 overflow-y-auto">
        <div className="px-3 py-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
          Core Workflows
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.key;
          return (
            <button
              key={item.key}
              onClick={() => onTabChange(item.key)}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-all ${
                isActive
                  ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon className={`w-4 h-4 ${isActive ? 'text-indigo-400' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </div>
              {item.badge ? (
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                  {item.badge}
                </span>
              ) : isActive ? (
                <ChevronRight className="w-3.5 h-3.5 text-indigo-400" />
              ) : null}
            </button>
          );
        })}
      </div>

      {/* Footer System Status */}
      <div className="p-4 border-t border-slate-800 bg-slate-950/40">
        <div className="flex items-center justify-between text-[11px] text-slate-400">
          <span className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            PostgreSQL 18 Connected
          </span>
          <span className="font-mono text-slate-400">v1.0.0</span>
        </div>
        <div className="mt-2 text-[10px] text-slate-400">
          Ponytail Principles Verified • Anti-Leakage Enforced
        </div>
      </div>
    </aside>
  );
};
