import React from 'react';
import { AlertCircle, CheckCircle, ArrowLeft, Clock, Cpu, ShieldAlert, ShieldCheck } from 'lucide-react';

export default function PredictionResultPage({ result, setCurrentTab, onOpenFeedback }) {
  // If user navigates directly without a prediction, show friendly prompt
  if (!result) {
    return (
      <div className="p-12 max-w-xl mx-auto text-center space-y-4 animate-fadeIn">
        <div className="w-16 h-16 rounded-3xl bg-indigo-50 text-[#5b5bf7] flex items-center justify-center mx-auto shadow-xs">
          <ShieldAlert size={30} />
        </div>
        <h2 className="text-xl font-bold text-slate-900">No Prediction Selected</h2>
        <p className="text-xs text-slate-500 leading-relaxed">
          Please run an email through the scanner or select an item from the Admin Dashboard to inspect its threat signals.
        </p>
        <button
          onClick={() => setCurrentTab('check')}
          className="px-6 py-3 rounded-xl bg-[#5b5bf7] hover:bg-[#4f46e5] text-white text-xs font-semibold shadow-xs transition"
        >
          Open Email Scanner
        </button>
      </div>
    );
  }

  const isSpam = result.is_spam;
  const rawProb = typeof result.spam_probability === 'number' ? (result.spam_probability * 100).toFixed(1) : null;

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6 animate-fadeIn">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <p className="text-xs font-bold text-[#5b5bf7] tracking-wider uppercase mb-1">ANALYSIS COMPLETE</p>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Prediction result</h1>
          <p className="text-slate-500 text-sm mt-1">
            {isSpam
              ? 'Our model found multiple high-risk signals in this message.'
              : 'Our model verified this message as clean with low threat indicators.'}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-xs text-slate-400 bg-white px-3 py-1.5 rounded-xl border border-slate-200">
            <Cpu size={13} className="text-[#5b5bf7]" />
            <span>Model: <strong className="text-slate-700">{result.model_version || 'v3.8.2'}</strong></span>
            <span>•</span>
            <Clock size={13} />
            <span>Latency: <strong className="text-slate-700">{result.latency_ms || 1.4}ms</strong></span>
          </div>

          <button
            onClick={() => setCurrentTab('check')}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border border-slate-200/80 bg-white text-slate-700 hover:bg-slate-50 text-xs font-semibold shadow-xs transition"
          >
            <span>Check another email</span>
          </button>
        </div>
      </div>

      {/* Main Grid: Left Column (Verdict + Flagged) & Right Column (Risk Breakdown + Feedback) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Left Column (2 Cols) */}
        <div className="lg:col-span-2 space-y-6">
          {/* Main Verdict Card */}
          <div
            className={`rounded-3xl p-7 border transition-all ${
              isSpam
                ? 'bg-[#fff1f2] border-rose-100'
                : 'bg-[#ecfdf5] border-emerald-100'
            }`}
          >
            <div className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                {/* Red or Green Icon Badge */}
                <div
                  className={`w-12 h-12 rounded-2xl flex items-center justify-center text-white shrink-0 shadow-xs ${
                    isSpam ? 'bg-[#ef4444]' : 'bg-[#10b981]'
                  }`}
                >
                  {isSpam ? (
                    <span className="text-2xl font-black">!</span>
                  ) : (
                    <span className="text-2xl font-black">✓</span>
                  )}
                </div>

                <div>
                  <p
                    className={`text-[11px] font-bold tracking-wider uppercase mb-0.5 ${
                      isSpam ? 'text-rose-600' : 'text-emerald-700'
                    }`}
                  >
                    {isSpam ? 'HIGH CONFIDENCE' : 'VERIFIED LEGITIMATE'}
                  </p>
                  <h2 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">
                    {result.verdict_title}
                  </h2>
                  <p className="text-xs text-slate-600 mt-1 max-w-md">
                    {result.recommendation}
                  </p>
                </div>
              </div>

              {/* Confidence and Spam Probability Display */}
              <div className="text-right shrink-0">
                <p className="text-3xl md:text-4xl font-extrabold text-slate-900 tracking-tight">
                  {result.confidence}%
                </p>
                <p className="text-xs text-slate-500 font-medium">confidence</p>
                {rawProb && (
                  <p className="text-[11px] text-slate-400 mt-1">
                    Spam Prob: <strong className="text-slate-600">{rawProb}%</strong>
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Why It Was Flagged Card */}
          <div className="bg-white rounded-3xl border border-slate-200/80 p-7 shadow-xs">
            <h3 className="font-bold text-slate-900 text-base mb-5">
              {isSpam ? 'Why it was flagged' : 'Safety verification breakdown'}
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {(result.flagged_reasons || []).map((reason, idx) => {
                const isHigh = reason.severity === 'High';
                const isMed = reason.severity === 'Medium';
                return (
                  <div key={idx} className="bg-slate-50/70 border border-slate-100/80 rounded-2xl p-4 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-900">{reason.title}</span>
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          isHigh
                            ? 'bg-rose-100 text-rose-600'
                            : isMed
                            ? 'bg-amber-100 text-amber-700'
                            : 'bg-emerald-100 text-emerald-700'
                        }`}
                      >
                        {reason.severity}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 font-normal leading-relaxed">
                      {reason.description}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right Column (1 Col): Risk Breakdown & Feedback Card */}
        <div className="space-y-6">
          {/* Risk Breakdown Card */}
          <div className="bg-white rounded-3xl border border-slate-200/80 p-6 shadow-xs space-y-5">
            <h3 className="font-bold text-slate-900 text-sm">Risk breakdown</h3>

            {/* Content signals */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-semibold">
                <span className="text-slate-700">Content signals</span>
                <span className="text-slate-900">{result.risk_breakdown?.content_signals ?? 92}%</span>
              </div>
              <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    (result.risk_breakdown?.content_signals ?? 92) > 50 ? 'bg-rose-500' : 'bg-emerald-500'
                  }`}
                  style={{ width: `${result.risk_breakdown?.content_signals ?? 92}%` }}
                ></div>
              </div>
            </div>

            {/* Sender reputation */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-semibold">
                <span className="text-slate-700">Sender reputation</span>
                <span className="text-slate-900">{result.risk_breakdown?.sender_reputation ?? 81}%</span>
              </div>
              <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    (result.risk_breakdown?.sender_reputation ?? 81) > 70
                      ? 'bg-amber-500'
                      : (result.risk_breakdown?.sender_reputation ?? 81) > 40
                      ? 'bg-amber-400'
                      : 'bg-emerald-500'
                  }`}
                  style={{ width: `${result.risk_breakdown?.sender_reputation ?? 81}%` }}
                ></div>
              </div>
            </div>

            {/* Link safety */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-semibold">
                <span className="text-slate-700">Link safety</span>
                <span className="text-slate-900">{result.risk_breakdown?.link_safety ?? 96}%</span>
              </div>
              <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    (result.risk_breakdown?.link_safety ?? 96) > 50 ? 'bg-rose-500' : 'bg-emerald-500'
                  }`}
                  style={{ width: `${result.risk_breakdown?.link_safety ?? 96}%` }}
                ></div>
              </div>
            </div>
          </div>

          {/* Was this helpful? Card */}
          <div className="bg-[#0b1329] rounded-3xl p-6 text-white shadow-xs space-y-3">
            <h4 className="font-bold text-sm">Was this helpful?</h4>
            <p className="text-xs text-slate-400 leading-relaxed font-normal">
              Your feedback is recorded to calibrate continuous retraining cycles in DVC.
            </p>
            <button
              onClick={() => onOpenFeedback(result)}
              className="w-full py-3 px-4 rounded-xl bg-[#5b5bf7] hover:bg-[#4f46e5] text-white font-semibold text-xs transition shadow-sm"
            >
              Share feedback
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
