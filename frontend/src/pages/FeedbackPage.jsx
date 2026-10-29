import React, { useState } from 'react';
import { ThumbsUp, ThumbsDown, CheckCircle, RefreshCw, AlertCircle, ArrowRight, ShieldCheck, Sparkles } from 'lucide-react';
import { triggerModelRetrain } from '../api';

export default function FeedbackPage({ onOpenFeedback }) {
  const [items, setItems] = useState([
    {
      id: 'FB-201',
      scan_id: 'MG-10480',
      subject: 'Urgent: verify your identity',
      user_verdict: 'Spam',
      model_verdict: 'Spam',
      status: 'Approved',
      confidence: '94%',
      time: '10 min ago'
    },
    {
      id: 'FB-202',
      scan_id: 'MG-10476',
      subject: 'Exclusive discount promo on electronics',
      user_verdict: 'Spam',
      model_verdict: 'Legitimate',
      status: 'Pending Review',
      confidence: '68%',
      time: '32 min ago'
    },
    {
      id: 'FB-203',
      scan_id: 'MG-10471',
      subject: 'Invoice #49281 from Vendor Partners',
      user_verdict: 'Legitimate',
      model_verdict: 'Spam',
      status: 'Pending Review',
      confidence: '71%',
      time: '1 hour ago'
    }
  ]);

  const [retrainCount, setRetrainCount] = useState(42);
  const targetThreshold = 100;
  const [isRetraining, setIsRetraining] = useState(false);
  const [retrainResult, setRetrainResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  const handleApprove = (id) => {
    setItems((prev) =>
      prev.map((item) => (item.id === id ? { ...item, status: 'Approved' } : item))
    );
    setRetrainCount((c) => Math.min(targetThreshold, c + 1));
  };

  const handleRetrain = async () => {
    setIsRetraining(true);
    setErrorMessage('');
    setRetrainResult(null);

    try {
      const res = await triggerModelRetrain(false);
      if (res && res.retraining) {
        setRetrainResult(res.retraining);
        setRetrainCount(0); // Reset cycle progress
      }
    } catch (err) {
      setErrorMessage(`Retraining failed: ${err.message}`);
    } finally {
      setIsRetraining(false);
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-7 animate-fadeIn">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <p className="text-xs font-bold text-[#5b5bf7] tracking-wider uppercase mb-1">ACTIVE LEARNING</p>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Review queue & feedback</h1>
          <p className="text-slate-500 text-sm mt-1">
            Human-in-the-loop review pool to validate ambiguous predictions and curate new training batches.
          </p>
        </div>

        <button
          disabled={isRetraining}
          onClick={handleRetrain}
          className={`inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-white text-xs font-semibold shadow-sm transition ${
            isRetraining ? 'bg-indigo-300 cursor-not-allowed' : 'bg-[#5b5bf7] hover:bg-[#4f46e5]'
          }`}
        >
          <RefreshCw size={13} className={isRetraining ? 'animate-spin' : ''} />
          <span>{isRetraining ? 'Training Candidate Model...' : 'Retrain on New Labels'}</span>
        </button>
      </div>

      {/* Retraining Outcome Banner */}
      {retrainResult && (
        <div className={`p-5 rounded-3xl border space-y-2 animate-fadeIn ${
          retrainResult.gate_passed ? 'bg-emerald-50 border-emerald-200 text-emerald-950' : 'bg-amber-50 border-amber-200 text-amber-950'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 font-bold text-sm">
              {retrainResult.gate_passed ? <CheckCircle className="text-emerald-600" size={18} /> : <AlertCircle className="text-amber-600" size={18} />}
              <span>Model Retraining Outcome: [{retrainResult.status}]</span>
            </div>
            <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${
              retrainResult.gate_passed ? 'bg-emerald-200 text-emerald-800' : 'bg-amber-200 text-amber-800'
            }`}>
              Quality Gate: {retrainResult.gate_passed ? 'PASSED' : 'REJECTED'}
            </span>
          </div>

          <p className="text-xs">
            {retrainResult.gate_passed 
              ? `Candidate ${retrainResult.candidate_version} met all quality thresholds and was successfully promoted to production!`
              : `Candidate model failed quality gate thresholds. Production model preserved as ${retrainResult.active_production_version}.`}
          </p>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 text-xs font-semibold">
            <div className="p-2.5 rounded-xl bg-white/70">
              <span className="text-slate-500 block text-[10px] font-bold">New Samples Ingested:</span>
              <span className="text-slate-900">{retrainResult.new_samples_added} emails</span>
            </div>
            <div className="p-2.5 rounded-xl bg-white/70">
              <span className="text-slate-500 block text-[10px] font-bold">Validation F1-Score:</span>
              <span className="text-emerald-700">{retrainResult.metrics?.f1_score}%</span>
            </div>
            <div className="p-2.5 rounded-xl bg-white/70">
              <span className="text-slate-500 block text-[10px] font-bold">Validation Accuracy:</span>
              <span className="text-slate-900">{retrainResult.metrics?.accuracy}%</span>
            </div>
            <div className="p-2.5 rounded-xl bg-white/70">
              <span className="text-slate-500 block text-[10px] font-bold">False Positive Rate:</span>
              <span className="text-slate-900">{retrainResult.metrics?.false_positive_rate}% ({retrainResult.metrics?.false_positives} FPs)</span>
            </div>
          </div>
        </div>
      )}

      {errorMessage && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-xs text-rose-800">
          <strong>Error:</strong> {errorMessage}
        </div>
      )}

      {/* Retraining Threshold Banner */}
      <div className="bg-white rounded-3xl border border-slate-200/80 p-6 shadow-xs space-y-3">
        <div className="flex items-center justify-between text-xs font-bold text-slate-800">
          <span>Continuous Retraining Trigger Progress</span>
          <span className="text-[#5b5bf7]">{retrainCount} / {targetThreshold} Validated Emails</span>
        </div>
        <div className="w-full h-2.5 rounded-full bg-slate-100 overflow-hidden">
          <div
            className="h-full rounded-full bg-[#5b5bf7] transition-all duration-500"
            style={{ width: `${(retrainCount / targetThreshold) * 100}%` }}
          ></div>
        </div>
        <p className="text-[11px] text-slate-400">
          When human-validated feedback samples are collected, an automated MLflow tracking and Quality Gate validation cycle triggers.
        </p>
      </div>

      {/* Feedback Queue Table */}
      <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="p-6 border-b border-slate-100">
          <h3 className="text-base font-bold text-slate-900">Flagged messages pending verification</h3>
          <p className="text-xs text-slate-500 mt-0.5">Community feedback submitted from prediction scans</p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50/60 text-slate-400 font-bold uppercase tracking-wider border-b border-slate-100">
              <tr>
                <th className="py-3.5 px-6">Queue ID</th>
                <th className="py-3.5 px-6">Scan ID</th>
                <th className="py-3.5 px-6">Subject</th>
                <th className="py-3.5 px-6">User Verdict</th>
                <th className="py-3.5 px-6">Model Verdict</th>
                <th className="py-3.5 px-6">Confidence</th>
                <th className="py-3.5 px-6">Status</th>
                <th className="py-3.5 px-6 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {items.map((row) => (
                <tr key={row.id} className="hover:bg-slate-50/60 transition">
                  <td className="py-4 px-6 font-semibold text-slate-800">{row.id}</td>
                  <td className="py-4 px-6 font-mono text-[11px] text-slate-500">{row.scan_id}</td>
                  <td className="py-4 px-6 text-slate-800 font-medium max-w-xs truncate">{row.subject}</td>
                  <td className="py-4 px-6 font-semibold">
                    <span className={row.user_verdict === 'Spam' ? 'text-rose-600' : 'text-emerald-600'}>
                      {row.user_verdict}
                    </span>
                  </td>
                  <td className="py-4 px-6 font-semibold">
                    <span className={row.model_verdict === 'Spam' ? 'text-rose-600' : 'text-emerald-600'}>
                      {row.model_verdict}
                    </span>
                  </td>
                  <td className="py-4 px-6 font-semibold text-slate-700">{row.confidence}</td>
                  <td className="py-4 px-6">
                    <span
                      className={`px-2.5 py-1 rounded-full text-[10px] font-bold ${
                        row.status === 'Approved'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-100'
                          : 'bg-amber-50 text-amber-700 border border-amber-100'
                      }`}
                    >
                      {row.status}
                    </span>
                  </td>
                  <td className="py-4 px-6 text-right">
                    {row.status !== 'Approved' ? (
                      <button
                        onClick={() => handleApprove(row.id)}
                        className="px-3 py-1.5 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-[#5b5bf7] text-xs font-semibold transition"
                      >
                        Verify & Queue
                      </button>
                    ) : (
                      <span className="text-slate-400 text-xs font-medium">Ready</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
