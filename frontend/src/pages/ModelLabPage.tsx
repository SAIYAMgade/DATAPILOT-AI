import React, { useEffect, useState } from 'react';
import {
  FlaskConical, CheckCircle2, Sliders, Play, Award, BarChart3, HelpCircle
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line
} from 'recharts';
import { api } from '../services/api';
import { ModelVersionItem } from '../types';

export const ModelLabPage: React.FC = () => {
  const [versions, setVersions] = useState<ModelVersionItem[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<ModelVersionItem | null>(null);
  const [modelType, setModelType] = useState<string>('RandomForest');
  const [obsDays, setObsDays] = useState<number>(90);
  const [predDays, setPredDays] = useState<number>(60);
  const [targetRecall, setTargetRecall] = useState<number>(0.75);
  const [training, setTraining] = useState<boolean>(false);
  const [trainStatus, setTrainStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    loadModels();
  }, []);

  const loadModels = async () => {
    try {
      setLoading(true);
      const res = await api.getModelVersions();
      setVersions(res);
      if (res.length > 0) {
        const active = res.find((m) => m.is_active) || res[0];
        setSelectedVersion(active);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleTrain = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setTraining(true);
      setTrainStatus('Training model with temporal cross-validation...');
      const res = await api.trainModel(modelType, obsDays, predDays, targetRecall);
      setTrainStatus(`Model trained successfully! Tag: ${res.version_tag}`);
      await loadModels();
      setTimeout(() => setTrainStatus(null), 5000);
    } catch (err: any) {
      setTrainStatus(`Training error: ${err.message}`);
    } finally {
      setTraining(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[400px]">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const m = selectedVersion?.metrics;
  const cm = m?.confusion_matrix;
  const fi = selectedVersion?.feature_importance || [];
  const curve = m?.threshold_tradeoff_curve || [];

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <FlaskConical className="w-5 h-5 text-indigo-400" />
            Model Laboratory &amp; Governance
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Audit evaluation metrics, feature importances, precision-recall trade-offs, and train new models with strict temporal splits.
          </p>
        </div>
      </div>

      {/* Train New Model Panel */}
      <div className="p-6 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <Sliders className="w-4 h-4 text-indigo-400" />
            Train New Model Version
          </h3>
          {trainStatus && (
            <span className="text-xs font-mono text-cyan-400 animate-fade">
              {trainStatus}
            </span>
          )}
        </div>

        <form onSubmit={handleTrain} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 text-xs">
          <div>
            <label className="block text-slate-400 mb-1 font-medium">Model Architecture</label>
            <select
              value={modelType}
              onChange={(e) => setModelType(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none"
            >
              <option value="RandomForest">Random Forest (100 Trees)</option>
              <option value="LogisticRegression">Logistic Regression (L2)</option>
              <option value="Baseline">Dummy Classifier (Baseline)</option>
            </select>
          </div>

          <div>
            <label className="block text-slate-400 mb-1 font-medium">Observation Window</label>
            <select
              value={obsDays}
              onChange={(e) => setObsDays(Number(e.target.value))}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none"
            >
              <option value={60}>60 Days History</option>
              <option value={90}>90 Days History (Standard)</option>
              <option value={120}>120 Days History</option>
            </select>
          </div>

          <div>
            <label className="block text-slate-400 mb-1 font-medium">Prediction Horizon</label>
            <select
              value={predDays}
              onChange={(e) => setPredDays(Number(e.target.value))}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none"
            >
              <option value={30}>30 Days Ahead</option>
              <option value={60}>60 Days Ahead (Standard)</option>
              <option value={90}>90 Days Ahead</option>
            </select>
          </div>

          <div>
            <label className="block text-slate-400 mb-1 font-medium">Target Recall Tuning</label>
            <select
              value={targetRecall}
              onChange={(e) => setTargetRecall(Number(e.target.value))}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none"
            >
              <option value={0.60}>60% Recall (Higher Precision)</option>
              <option value={0.75}>75% Recall (Balanced)</option>
              <option value={0.85}>85% Recall (Catch More Churn)</option>
            </select>
          </div>

          <div className="flex items-end">
            <button
              type="submit"
              disabled={training}
              className="w-full h-9 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-medium transition flex items-center justify-center gap-2 disabled:opacity-50"
            >
              <Play className="w-3.5 h-3.5" />
              <span>{training ? 'Fitting Model...' : 'Train Model'}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Selected Model Scorecard */}
      {selectedVersion && m && (
        <div className="space-y-6">
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Inspect Model</span>
              <div className="text-base font-bold text-slate-100 flex items-center gap-2 font-mono">
                {selectedVersion.version_tag}
                {selectedVersion.is_active && (
                  <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-sans">
                    Active Production
                  </span>
                )}
              </div>
            </div>
            <div className="text-xs text-slate-400 font-mono">
              Observation: {selectedVersion.observation_days}d • Prediction: {selectedVersion.prediction_days}d • Trained: {selectedVersion.created_at}
            </div>
          </div>

          {/* Metrics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
              <div className="text-xs text-slate-400">ROC-AUC</div>
              <div className="text-xl font-bold font-mono text-indigo-400 mt-1">{m.roc_auc}</div>
              <div className="text-[10px] text-slate-400 mt-0.5">Discrimination</div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
              <div className="text-xs text-slate-400">PR-AUC</div>
              <div className="text-xl font-bold font-mono text-cyan-400 mt-1">{m.pr_auc}</div>
              <div className="text-[10px] text-slate-400 mt-0.5">Precision-Recall AUC</div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
              <div className="text-xs text-slate-400">F1-Score</div>
              <div className="text-xl font-bold font-mono text-slate-100 mt-1">{m.f1_score}</div>
              <div className="text-[10px] text-slate-400 mt-0.5">Harmonic Mean</div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
              <div className="text-xs text-slate-400">Recall</div>
              <div className="text-xl font-bold font-mono text-emerald-400 mt-1">{m.recall}</div>
              <div className="text-[10px] text-slate-400 mt-0.5">At-Risk Capture</div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
              <div className="text-xs text-slate-400">Precision</div>
              <div className="text-xl font-bold font-mono text-slate-100 mt-1">{m.precision}</div>
              <div className="text-[10px] text-slate-400 mt-0.5">Positive Predictive</div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
              <div className="text-xs text-slate-400">Brier Score</div>
              <div className="text-xl font-bold font-mono text-slate-300 mt-1">{m.brier_score}</div>
              <div className="text-[10px] text-slate-400 mt-0.5">Calibration Loss</div>
            </div>
          </div>

          {/* Visuals: Confusion Matrix & Feature Importance */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Confusion Matrix */}
            <div className="p-6 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
              <h3 className="text-sm font-semibold text-slate-200">Confusion Matrix (Holdout Test Set)</h3>
              {cm ? (
                <div className="grid grid-cols-2 gap-3 text-xs pt-2">
                  <div className="p-4 rounded-lg bg-emerald-950/20 border border-emerald-900/40 text-center">
                    <div className="text-[10px] text-slate-400 uppercase font-mono">True Negatives (Retained)</div>
                    <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">{cm.true_negatives}</div>
                  </div>
                  <div className="p-4 rounded-lg bg-amber-950/20 border border-amber-900/40 text-center">
                    <div className="text-[10px] text-slate-400 uppercase font-mono">False Positives (False Alarm)</div>
                    <div className="text-2xl font-bold font-mono text-amber-400 mt-1">{cm.false_positives}</div>
                  </div>
                  <div className="p-4 rounded-lg bg-rose-950/20 border border-rose-900/40 text-center">
                    <div className="text-[10px] text-slate-400 uppercase font-mono">False Negatives (Missed Churn)</div>
                    <div className="text-2xl font-bold font-mono text-rose-400 mt-1">{cm.false_negatives}</div>
                  </div>
                  <div className="p-4 rounded-lg bg-indigo-950/20 border border-indigo-900/40 text-center">
                    <div className="text-[10px] text-slate-400 uppercase font-mono">True Positives (Caught Churn)</div>
                    <div className="text-2xl font-bold font-mono text-indigo-400 mt-1">{cm.true_positives}</div>
                  </div>
                </div>
              ) : (
                <div className="text-xs text-slate-400">No confusion matrix data available.</div>
              )}
            </div>

            {/* Feature Importance */}
            <div className="p-6 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
              <h3 className="text-sm font-semibold text-slate-200">Top Predictive Features</h3>
              <div className="h-56 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={fi} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis type="number" stroke="#64748b" tick={{ fontSize: 10 }} />
                    <YAxis dataKey="feature" type="category" stroke="#64748b" tick={{ fontSize: 10 }} width={120} />
                    <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }} />
                    <Bar dataKey="importance" fill="#818cf8" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Threshold Trade-Off Curve */}
          {curve.length > 0 && (
            <div className="p-6 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
              <h3 className="text-sm font-semibold text-slate-200">Precision-Recall Decision Threshold Trade-Off Curve</h3>
              <div className="h-60 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={curve}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="threshold" stroke="#64748b" tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tick={{ fontSize: 11 }} domain={[0, 1]} />
                    <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }} />
                    <Line type="monotone" dataKey="precision" stroke="#38bdf8" name="Precision" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="recall" stroke="#34d399" name="Recall" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="f1" stroke="#f59e0b" name="F1-Score" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Model Versions History */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-800 text-xs font-semibold text-slate-300">
          Model Version History
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400">
              <tr>
                <th className="py-2.5 px-4">Version Tag</th>
                <th className="py-2.5 px-4">Model Type</th>
                <th className="py-2.5 px-4">ROC-AUC</th>
                <th className="py-2.5 px-4">PR-AUC</th>
                <th className="py-2.5 px-4">Recall</th>
                <th className="py-2.5 px-4">Precision</th>
                <th className="py-2.5 px-4">Threshold</th>
                <th className="py-2.5 px-4">Status</th>
                <th className="py-2.5 px-4">Trained Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/40 text-slate-300 font-mono">
              {versions.map((ver) => (
                <tr
                  key={ver.id}
                  onClick={() => setSelectedVersion(ver)}
                  className={`hover:bg-slate-800/40 cursor-pointer transition ${
                    selectedVersion?.id === ver.id ? 'bg-slate-800/30' : ''
                  }`}
                >
                  <td className="py-2.5 px-4 text-indigo-400 font-semibold">{ver.version_tag}</td>
                  <td className="py-2.5 px-4 font-sans">{ver.model_type}</td>
                  <td className="py-2.5 px-4">{ver.metrics?.roc_auc}</td>
                  <td className="py-2.5 px-4">{ver.metrics?.pr_auc}</td>
                  <td className="py-2.5 px-4 text-emerald-400">{ver.metrics?.recall}</td>
                  <td className="py-2.5 px-4">{ver.metrics?.precision}</td>
                  <td className="py-2.5 px-4">{ver.threshold}</td>
                  <td className="py-2.5 px-4 font-sans">
                    {ver.is_active ? (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        Active
                      </span>
                    ) : (
                      <span className="text-[10px] text-slate-400">Archived</span>
                    )}
                  </td>
                  <td className="py-2.5 px-4 text-slate-400 text-[11px] font-sans">{ver.created_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
