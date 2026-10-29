import React, { useEffect, useState } from 'react';
import { Database, AlertTriangle, CheckCircle, RefreshCw, XCircle } from 'lucide-react';
import { api } from '../services/api';
import { IngestionBatch } from '../types';

export const DataQualityPage: React.FC = () => {
  const [batches, setBatches] = useState<IngestionBatch[]>([]);
  const [selectedBatchId, setSelectedBatchId] = useState<number | null>(null);
  const [rejections, setRejections] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [seeding, setSeeding] = useState<boolean>(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  useEffect(() => {
    loadBatches();
  }, []);

  const loadBatches = async () => {
    try {
      setLoading(true);
      const res = await api.getBatches();
      setBatches(res);
      if (res.length > 0 && !selectedBatchId) {
        inspectBatch(res[0].id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const inspectBatch = async (batchId: number) => {
    try {
      setSelectedBatchId(batchId);
      const res = await api.getBatchRejections(batchId);
      setRejections(res.sample || []);
    } catch (err) {
      console.error(err);
    }
  };

  const handleSeed = async (corrupt: boolean) => {
    try {
      setSeeding(true);
      setStatusMsg(`Generating & ingesting ${corrupt ? 'corrupted' : 'clean'} batch...`);
      const res = await api.generateAndSeed(250, Math.floor(Math.random() * 10000), corrupt);
      setStatusMsg(`Done! Accepted: ${res.records_accepted}, Rejected: ${res.records_rejected}`);
      await loadBatches();
      setTimeout(() => setStatusMsg(null), 5000);
    } catch (err: any) {
      setStatusMsg(`Error: ${err.message}`);
    } finally {
      setSeeding(false);
    }
  };

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
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Database className="w-5 h-5 text-indigo-400" />
            Data Ingestion &amp; Quality Audit
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Transactional validation gate tracking schema anomalies, negative amounts, invalid keys, and duplicate transaction IDs.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {statusMsg && (
            <span className="text-xs text-amber-400 bg-amber-950/40 px-2.5 py-1 rounded border border-amber-800/40 animate-fade font-mono">
              {statusMsg}
            </span>
          )}
          <button
            onClick={() => handleSeed(true)}
            disabled={seeding}
            className="px-3 py-1.5 rounded-lg bg-amber-950/40 hover:bg-amber-900/60 text-amber-300 border border-amber-800/40 text-xs font-medium transition disabled:opacity-50"
          >
            {seeding ? 'Ingesting...' : 'Inject Corrupted Batch (Test Gate)'}
          </button>
          <button
            onClick={() => handleSeed(false)}
            disabled={seeding}
            className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition disabled:opacity-50"
          >
            {seeding ? 'Ingesting...' : 'Ingest Clean Batch'}
          </button>
        </div>
      </div>

      {/* Batches Table */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-800 text-xs font-semibold text-slate-300">
          Ingestion Batch Ledger
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400">
              <tr>
                <th className="py-2.5 px-4">Batch Reference</th>
                <th className="py-2.5 px-4">Source Type</th>
                <th className="py-2.5 px-4 text-right">Received</th>
                <th className="py-2.5 px-4 text-right">Accepted</th>
                <th className="py-2.5 px-4 text-right">Rejected</th>
                <th className="py-2.5 px-4 text-center">Status</th>
                <th className="py-2.5 px-4">Timestamp</th>
                <th className="py-2.5 px-4 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/40 text-slate-300 font-mono">
              {batches.map((b) => (
                <tr
                  key={b.id}
                  onClick={() => inspectBatch(b.id)}
                  className={`hover:bg-slate-800/40 cursor-pointer transition ${
                    selectedBatchId === b.id ? 'bg-slate-800/30' : ''
                  }`}
                >
                  <td className="py-2.5 px-4 text-indigo-400 font-semibold">{b.batch_ref}</td>
                  <td className="py-2.5 px-4 font-sans text-slate-300">{b.source_type}</td>
                  <td className="py-2.5 px-4 text-right">{b.records_received.toLocaleString()}</td>
                  <td className="py-2.5 px-4 text-right text-emerald-400">{b.records_accepted.toLocaleString()}</td>
                  <td className={`py-2.5 px-4 text-right ${b.records_rejected > 0 ? 'text-rose-400 font-bold' : 'text-slate-400'}`}>
                    {b.records_rejected.toLocaleString()}
                  </td>
                  <td className="py-2.5 px-4 text-center font-sans">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono ${
                      b.status === 'completed'
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        : b.status === 'partial'
                        ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                        : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                    }`}>
                      {b.status}
                    </span>
                  </td>
                  <td className="py-2.5 px-4 text-slate-400 font-sans text-[11px]">{b.created_at}</td>
                  <td className="py-2.5 px-4 text-center font-sans">
                    <button
                      onClick={(e) => { e.stopPropagation(); inspectBatch(b.id); }}
                      className="px-2 py-1 text-[11px] rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
                    >
                      Audit
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Rejections Log Audit Drawer */}
      <div className="p-6 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            Batch Rejection Audit Trail ({rejections.length} sampled rejections)
          </h3>
          <span className="text-xs font-mono text-slate-400">
            Selected Batch ID: {selectedBatchId || 'None'}
          </span>
        </div>

        {rejections.length === 0 ? (
          <div className="p-6 rounded-lg bg-slate-950 border border-slate-800 text-center text-xs text-slate-400">
            No rejected records for this batch. All incoming transactions complied with schema validation rules.
          </div>
        ) : (
          <div className="max-h-64 overflow-y-auto border border-slate-800 rounded-lg">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-950 border-b border-slate-800 text-slate-400 sticky top-0">
                <tr>
                  <th className="py-2 px-3">Row #</th>
                  <th className="py-2 px-3">Rejection Reason</th>
                  <th className="py-2 px-3">Raw Incoming Record</th>
                  <th className="py-2 px-3">Logged At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/40 text-slate-300">
                {rejections.map((rej, i) => (
                  <tr key={i} className="hover:bg-slate-800/30">
                    <td className="py-2 px-3 text-amber-400">{rej.row_index}</td>
                    <td className="py-2 px-3 font-semibold text-rose-300">{rej.reason}</td>
                    <td className="py-2 px-3 text-[10px] text-slate-400 max-w-md truncate" title={rej.raw_record}>
                      {rej.raw_record}
                    </td>
                    <td className="py-2 px-3 text-slate-400 text-[10px]">{rej.created_at}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
