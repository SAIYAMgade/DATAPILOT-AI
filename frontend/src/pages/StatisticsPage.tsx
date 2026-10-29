import React, { useEffect, useState } from 'react';
import { Activity, HelpCircle, CheckCircle2, XCircle, Info } from 'lucide-react';
import { api } from '../services/api';
import { StatisticalTestResult } from '../types';

export const StatisticsPage: React.FC = () => {
  const [activeTest, setActiveTest] = useState<'kruskal' | 'chi2' | 'ci' | 'ols'>('kruskal');
  const [kruskalData, setKruskalData] = useState<StatisticalTestResult | null>(null);
  const [chi2Data, setChi2Data] = useState<StatisticalTestResult | null>(null);
  const [ciData, setCiData] = useState<any | null>(null);
  const [olsData, setOlsData] = useState<StatisticalTestResult | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAllStats();
  }, []);

  const loadAllStats = async () => {
    try {
      setLoading(true);
      const [k, c, ci, o] = await Promise.all([
        api.getSegmentComparison('acquisition_channel'),
        api.getChannelRetentionTest(),
        api.getConfidenceIntervals(0.95),
        api.getRevenueTrend()
      ]);
      setKruskalData(k);
      setChi2Data(c);
      setCiData(ci);
      setOlsData(o);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[400px]">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const renderTestCard = (test: StatisticalTestResult) => (
    <div className="space-y-6">
      {/* Test Meta Header */}
      <div className="p-6 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-xs font-mono text-indigo-400 font-semibold uppercase tracking-wider">
            {test.test_applied}
          </span>
          {test.statistically_significant !== undefined && (
            <span className={`px-2.5 py-1 rounded text-xs font-medium flex items-center gap-1.5 ${
              test.statistically_significant
                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                : 'bg-slate-800 text-slate-400 border border-slate-700'
            }`}>
              {test.statistically_significant ? <CheckCircle2 className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
              {test.statistically_significant ? 'Statistically Significant (p < 0.05)' : 'Not Statistically Significant'}
            </span>
          )}
        </div>

        <h3 className="text-base font-bold text-slate-100">{test.business_question}</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs pt-2">
          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1">
            <span className="font-semibold text-slate-400">Null Hypothesis (H₀):</span>
            <p className="text-slate-300 font-mono text-[11px]">{test.null_hypothesis}</p>
          </div>
          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1">
            <span className="font-semibold text-slate-400">Alternative Hypothesis (H₁):</span>
            <p className="text-slate-300 font-mono text-[11px]">{test.alternative_hypothesis}</p>
          </div>
        </div>
      </div>

      {/* Numerical Results Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <div className="text-xs text-slate-400">Test Statistic</div>
          <div className="text-2xl font-bold font-mono text-slate-100 mt-1">
            {test.test_statistic !== undefined ? test.test_statistic.toFixed(4) : 'N/A'}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Computed from observations</div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <div className="text-xs text-slate-400">p-value</div>
          <div className={`text-2xl font-bold font-mono mt-1 ${
            (test.p_value || 1) < 0.05 ? 'text-emerald-400' : 'text-slate-300'
          }`}>
            {test.p_value !== undefined ? (test.p_value < 0.0001 ? '< 0.0001' : test.p_value.toFixed(4)) : 'N/A'}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Significance threshold α = 0.05</div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <div className="text-xs text-slate-400">Effect Size</div>
          <div className="text-2xl font-bold font-mono text-indigo-400 mt-1">
            {test.effect_size ? `${test.effect_size.value} (${test.effect_size.magnitude})` : 'N/A'}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">
            {test.effect_size ? test.effect_size.metric : 'Measured effect'}
          </div>
        </div>
      </div>

      {/* Plain English Business Interpretation */}
      <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
        <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Business Interpretation</h4>
        <p className="text-sm text-slate-200 leading-relaxed font-medium">
          {test.interpretation}
        </p>
      </div>

      {/* Assumptions & Limitations Checklist */}
      <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
        <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
          <Info className="w-3.5 h-3.5 text-indigo-400" />
          Statistical Assumptions &amp; Methodological Limitations
        </h4>
        <ul className="space-y-1.5 text-xs text-slate-400 list-disc list-inside">
          {test.assumptions_and_limitations.map((item, i) => (
            <li key={i} className="leading-relaxed">
              <span className="text-slate-300">{item}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-slate-100">Hypothesis Testing &amp; Statistical Inference</h2>
        <p className="text-xs text-slate-400 mt-1">
          SciPy and Statsmodels engines testing transactional distributions, confidence boundaries, and channel dependencies.
        </p>
      </div>

      {/* Test Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-slate-800 pb-3">
        <button
          onClick={() => setActiveTest('kruskal')}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition ${
            activeTest === 'kruskal'
              ? 'bg-indigo-600 text-white shadow-sm'
              : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
          }`}
        >
          Transaction Values (Kruskal-Wallis)
        </button>
        <button
          onClick={() => setActiveTest('chi2')}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition ${
            activeTest === 'chi2'
              ? 'bg-indigo-600 text-white shadow-sm'
              : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
          }`}
        >
          Channel vs Retention (Chi-Square)
        </button>
        <button
          onClick={() => setActiveTest('ci')}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition ${
            activeTest === 'ci'
              ? 'bg-indigo-600 text-white shadow-sm'
              : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
          }`}
        >
          Metric Confidence Intervals (95% CI)
        </button>
        <button
          onClick={() => setActiveTest('ols')}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition ${
            activeTest === 'ols'
              ? 'bg-indigo-600 text-white shadow-sm'
              : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
          }`}
        >
          Monthly Revenue Trend (OLS)
        </button>
      </div>

      {/* Active Test View */}
      {activeTest === 'kruskal' && kruskalData && renderTestCard(kruskalData)}
      {activeTest === 'chi2' && chi2Data && renderTestCard(chi2Data)}
      {activeTest === 'ols' && olsData && renderTestCard(olsData)}

      {/* CI Card Custom View */}
      {activeTest === 'ci' && ciData && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* AOV CI */}
            <div className="p-6 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
              <div className="text-xs font-mono text-indigo-400 uppercase tracking-wider font-semibold">
                Average Order Value (Student&apos;s t CI)
              </div>
              <div className="text-3xl font-bold font-mono text-slate-100">
                ${ciData.average_order_value?.mean}
              </div>
              <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-400">95% Confidence Interval:</span>
                  <span className="font-mono text-emerald-400 font-semibold">
                    [${ciData.average_order_value?.ci_lower}, ${ciData.average_order_value?.ci_upper}]
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Sample Size:</span>
                  <span className="font-mono text-slate-300">{ciData.average_order_value?.sample_size} orders</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Standard Error (SE):</span>
                  <span className="font-mono text-slate-300">${ciData.average_order_value?.standard_error}</span>
                </div>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                With 95% confidence, the true population average order value lies between ${ciData.average_order_value?.ci_lower} and ${ciData.average_order_value?.ci_upper}.
              </p>
            </div>

            {/* Retention Rate CI */}
            <div className="p-6 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
              <div className="text-xs font-mono text-cyan-400 uppercase tracking-wider font-semibold">
                Active Customer Rate (Wilson Score CI)
              </div>
              <div className="text-3xl font-bold font-mono text-slate-100">
                {((ciData.active_customer_rate?.proportion || 0) * 100).toFixed(1)}%
              </div>
              <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-400">95% Wilson Score Interval:</span>
                  <span className="font-mono text-cyan-400 font-semibold">
                    [{((ciData.active_customer_rate?.ci_lower || 0) * 100).toFixed(1)}%, {((ciData.active_customer_rate?.ci_upper || 0) * 100).toFixed(1)}%]
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Active / Total Accounts:</span>
                  <span className="font-mono text-slate-300">
                    {ciData.active_customer_rate?.active_count} / {ciData.active_customer_rate?.total_count}
                  </span>
                </div>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                Wilson score interval provides robust asymmetric coverage for binomial proportions without normal approximation distortion.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
