import React, { useState } from 'react';
import { HelpCircle, Send, Sparkles, ShieldCheck, Info, ChevronDown, ChevronUp } from 'lucide-react';
import { api } from '../services/api';

const SUGGESTED_QUERIES = [
  "What is our total net revenue and how did it grow versus the previous 90-day period?",
  "Which customer accounts are at highest risk of churn and should be prioritized for retention?",
  "What are our customer segments and what revenue does each contribute?",
  "What does our monthly cohort retention matrix look like?",
  "Is there a statistically significant difference in transaction values across acquisition channels?"
];

export const AssistantPage: React.FC = () => {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<Array<{
    question: string;
    answer: string;
    intent: string;
    data: any;
    limitations: string;
  }>>([
    {
      question: "What is our total net revenue and how did it grow versus the previous 90-day period?",
      answer: "For the 90-day window, total net revenue is calculated directly from completed non-refunded transactions in PostgreSQL with window function deltas.",
      intent: "revenue_summary",
      data: { status: "initialized" },
      limitations: "Calculations exclude refunded and cancelled orders."
    }
  ]);
  const [showJson, setShowJson] = useState<number | null>(null);

  const handleSubmit = async (qText?: string) => {
    const q = (qText || question).trim();
    if (!q) return;

    try {
      setLoading(true);
      const res = await api.queryAssistant(q);
      setHistory((prev) => [res, ...prev]);
      setQuestion('');
    } catch (err: any) {
      setHistory((prev) => [
        {
          question: q,
          answer: `Error executing query: ${err.message}`,
          intent: "error",
          data: null,
          limitations: "Backend analytical execution failed."
        },
        ...prev
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 space-y-6 max-w-4xl mx-auto">
      {/* Title */}
      <div>
        <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <HelpCircle className="w-5 h-5 text-indigo-400" />
          Controlled AI Analytics Assistant
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Natural-language interface with deterministic query routing. Invokes approved backend analytical engines with zero mathematical hallucination.
        </p>
      </div>

      {/* Suggested Prompts */}
      <div className="space-y-2">
        <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
          Suggested Analytical Queries
        </span>
        <div className="flex flex-wrap gap-2">
          {SUGGESTED_QUERIES.map((sq, i) => (
            <button
              key={i}
              onClick={() => handleSubmit(sq)}
              className="text-left text-xs px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition"
            >
              {sq}
            </button>
          ))}
        </div>
      </div>

      {/* Query Input Box */}
      <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 shadow-sm space-y-3">
        <div className="flex items-center gap-2">
          <input
            type="text"
            placeholder="Ask a question about revenue, churn risk, customer segments, or cohorts..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') handleSubmit(); }}
            className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 text-xs text-slate-200 placeholder-slate-400 focus:outline-none focus:border-indigo-500"
          />
          <button
            onClick={() => handleSubmit()}
            disabled={loading || !question.trim()}
            className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition flex items-center gap-2 disabled:opacity-50"
          >
            <Send className="w-3.5 h-3.5" />
            <span>{loading ? 'Routing...' : 'Analyze'}</span>
          </button>
        </div>
        <div className="flex items-center justify-between text-[11px] text-slate-400">
          <span className="flex items-center gap-1.5 text-emerald-400">
            <ShieldCheck className="w-3.5 h-3.5" />
            Bounded Query Protocol Enforced (No Unrestricted SQL)
          </span>
          <span className="font-mono text-slate-400">Deterministic Engine Verified</span>
        </div>
      </div>

      {/* Conversation / Query History */}
      <div className="space-y-4">
        {history.map((item, idx) => (
          <div key={idx} className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-indigo-300 font-mono">
                Q: {item.question}
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                Intent: {item.intent}
              </span>
            </div>

            <div className="p-4 rounded-lg bg-slate-950 border border-slate-800/80 text-xs text-slate-200 leading-relaxed font-sans">
              {item.answer}
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-slate-800/60 text-[11px] text-slate-400">
              <div className="flex items-center gap-1.5">
                <Info className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                <span><strong className="text-slate-300">Analytical Boundary:</strong> {item.limitations}</span>
              </div>
              {item.data && (
                <button
                  onClick={() => setShowJson(showJson === idx ? null : idx)}
                  className="text-xs text-indigo-400 hover:text-indigo-300 font-mono flex items-center gap-1"
                >
                  <span>{showJson === idx ? 'Hide Structured Data' : 'View Raw Data'}</span>
                  {showJson === idx ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                </button>
              )}
            </div>

            {showJson === idx && (
              <pre className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-[10px] font-mono text-cyan-300 overflow-x-auto">
                {JSON.stringify(item.data, null, 2)}
              </pre>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
