import React, { useState } from 'react';
import { RefreshCw, CheckCircle, Database } from 'lucide-react';
import { api } from '../services/api';

interface NavbarProps {
  onRefreshData: () => void;
  activeModelTag?: string;
}

export const Navbar: React.FC<NavbarProps> = ({ onRefreshData, activeModelTag }) => {
  const [seeding, setSeeding] = useState(false);
  const [seedStatus, setSeedStatus] = useState<string | null>(null);

  const handleSeed = async (corrupt: boolean = false) => {
    try {
      setSeeding(true);
      setSeedStatus('Generating & ingesting synthetic records...');
      const res = await api.generateAndSeed(350, Math.floor(Math.random() * 1000), corrupt);
      setSeedStatus(`Ingested ${res.records_accepted} records (${res.records_rejected} rejected).`);
      setTimeout(() => setSeedStatus(null), 4000);
      onRefreshData();
    } catch (err: any) {
      setSeedStatus(`Failed: ${err.message}`);
    } finally {
      setSeeding(false);
    }
  };

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/80 backdrop-blur px-6 flex items-center justify-between z-10 sticky top-0">
      <div className="flex items-center gap-4">
        <h1 className="text-sm font-semibold text-slate-200">
          Decision Intelligence Platform
        </h1>
        {activeModelTag && (
          <span className="hidden md:inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-mono bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
            <CheckCircle className="w-3 h-3 text-indigo-400" />
            Model: {activeModelTag}
          </span>
        )}
      </div>

      <div className="flex items-center gap-3">
        {seedStatus && (
          <span className="text-xs text-amber-400 bg-amber-950/40 px-2.5 py-1 rounded border border-amber-800/40 animate-fade">
            {seedStatus}
          </span>
        )}

        <button
          onClick={() => handleSeed(false)}
          disabled={seeding}
          className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition disabled:opacity-50"
          title="Regenerates 350 SME accounts and ~12k transactions into PostgreSQL"
        >
          <Database className="w-3.5 h-3.5 text-cyan-400" />
          <span>{seeding ? 'Generating...' : 'Seed Clean Data'}</span>
        </button>

        <button
          onClick={() => handleSeed(true)}
          disabled={seeding}
          className="hidden sm:flex items-center gap-2 px-3 py-1.5 text-xs font-medium rounded-lg bg-amber-950/30 hover:bg-amber-900/40 text-amber-300 border border-amber-800/40 transition disabled:opacity-50"
          title="Generates corrupted records to test rejection engine"
        >
          <Database className="w-3.5 h-3.5 text-amber-400" />
          <span>Seed Corrupted Data</span>
        </button>

        <button
          onClick={onRefreshData}
          className="p-1.5 text-slate-400 hover:text-slate-200 rounded-lg bg-slate-800/80 hover:bg-slate-700 border border-slate-700 transition"
          title="Refresh All Views"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
