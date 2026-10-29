import React, { useState, useEffect } from 'react';
import { 
  ArrowRight, 
  Check, 
  Sparkles, 
  ChevronDown, 
  RotateCcw, 
  AlertCircle,
  Layers,
  FileText,
  Mail,
  UploadCloud
} from 'lucide-react';
import { predictEmail, predictBatch, fetchSamples } from '../api';

export default function CheckEmailPage({ setCurrentTab, setLatestResult }) {
  const [activeMode, setActiveMode] = useState('single'); // 'single' | 'batch'
  const [sender, setSender] = useState('');
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [samples, setSamples] = useState([]);
  const [showSamplesMenu, setShowSamplesMenu] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  // Batch Mode State
  const [batchRawText, setBatchRawText] = useState('');
  const [batchResults, setBatchResults] = useState(null);
  const [batchLoading, setBatchLoading] = useState(false);

  useEffect(() => {
    fetchSamples()
      .then(setSamples)
      .catch((err) => {
        console.warn("Could not pre-load sample scenarios from backend:", err.message);
      });
  }, []);

  const handleUseSample = (sample) => {
    setSender(sample.sender);
    setSubject(sample.subject);
    setBody(sample.body);
    setShowSamplesMenu(false);
    setErrorMessage('');
  };

  const handleClear = () => {
    setSender('');
    setSubject('');
    setBody('');
    setErrorMessage('');
  };

  const handleAnalyzeSingle = async (e) => {
    e.preventDefault();
    const cleanSub = subject.trim();
    const cleanBody = body.trim();

    if (!cleanSub && !cleanBody) {
      setErrorMessage('Please enter an email subject line or message body to analyze.');
      return;
    }

    setErrorMessage('');
    setLoading(true);
    setLoadingStep(1);

    const stepTimer = setTimeout(() => {
      setLoadingStep(2);
    }, 350);

    try {
      // Direct call to FastAPI backend POST /predict
      const result = await predictEmail({
        sender: sender.trim() || 'sender@example.com',
        subject: cleanSub,
        body: cleanBody
      });

      setLatestResult(result);
      setCurrentTab('result');
    } catch (err) {
      setErrorMessage(`Backend API Error: ${err.message}. Ensure the FastAPI server is running on http://localhost:8000.`);
    } finally {
      clearTimeout(stepTimer);
      setLoading(false);
    }
  };

  const handleRunBatch = async (e) => {
    e.preventDefault();
    if (!batchRawText.trim()) {
      setErrorMessage('Please enter emails in CSV or delimiter format (Subject | Body).');
      return;
    }

    setErrorMessage('');
    setBatchLoading(true);

    try {
      const lines = batchRawText.split('\n').filter(l => l.trim().length > 0);
      const emailObjects = lines.map((line, idx) => {
        const parts = line.split('|');
        if (parts.length >= 2) {
          return {
            sender: `sender_${idx + 1}@domain.com`,
            subject: parts[0].trim(),
            body: parts.slice(1).join('|').trim()
          };
        }
        return {
          sender: `sender_${idx + 1}@domain.com`,
          subject: line.trim().slice(0, 50),
          body: line.trim()
        };
      });

      // Direct call to FastAPI backend POST /predict/batch
      const batchResp = await predictBatch(emailObjects);
      setBatchResults(batchResp);
    } catch (err) {
      setErrorMessage(`Batch API Error: ${err.message}`);
    } finally {
      setBatchLoading(false);
    }
  };

  const loadSampleBatch = () => {
    const sampleBatchText = 
`Claim your $10,000 cash prize now | Congratulations you won! Click here to verify identity within 2 hours.
Quarterly balance sheet overview | Hi team, please find attached the revised Q3 financials for review.
Urgent: account credentials compromised | Security alert: your account access will expire unless you click here now.
Project standup moved to 3 PM | The team sync is moved to Conference Room C this afternoon.`;
    setBatchRawText(sampleBatchText);
    setErrorMessage('');
  };

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6 animate-fadeIn">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <p className="text-xs font-bold text-[#5b5bf7] tracking-wider uppercase mb-1">EMAIL SCANNER</p>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Check an email</h1>
          <p className="text-slate-500 text-sm mt-1 max-w-xl">
            Paste message details below. MailGuard checks language patterns, links, sender signals, and known threat indicators.
          </p>
        </div>

        {/* Mode Selector & Sample Presets */}
        <div className="flex items-center gap-3">
          {/* Single vs Batch Mode Switcher */}
          <div className="inline-flex rounded-xl border border-slate-200/80 bg-white p-1 text-xs shadow-xs">
            <button
              type="button"
              onClick={() => setActiveMode('single')}
              className={`px-3 py-1.5 rounded-lg font-semibold transition ${
                activeMode === 'single' ? 'bg-[#eef2ff] text-[#4f46e5]' : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              Single Email
            </button>
            <button
              type="button"
              onClick={() => setActiveMode('batch')}
              className={`px-3 py-1.5 rounded-lg font-semibold transition ${
                activeMode === 'batch' ? 'bg-[#eef2ff] text-[#4f46e5]' : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              Batch Scanner
            </button>
          </div>

          {activeMode === 'single' ? (
            <div className="relative">
              <button
                type="button"
                onClick={() => setShowSamplesMenu(!showSamplesMenu)}
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border border-slate-200/80 bg-white text-slate-700 hover:bg-slate-50 text-xs font-semibold shadow-xs transition"
              >
                <Sparkles size={14} className="text-[#5b5bf7]" />
                <span>Use sample email</span>
                <ChevronDown size={14} className="text-slate-400" />
              </button>

              {showSamplesMenu && (
                <div className="absolute right-0 mt-2 w-80 bg-white rounded-2xl shadow-xl border border-slate-200/80 py-2.5 z-30 animate-fadeIn">
                  <p className="px-4 py-1 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                    Select Test Scenario
                  </p>
                  {samples.map((s, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleUseSample(s)}
                      className="w-full text-left px-4 py-2.5 text-xs text-slate-700 hover:bg-indigo-50/70 hover:text-indigo-700 transition flex flex-col border-b border-slate-50 last:border-b-0"
                    >
                      <span className="font-semibold text-slate-900">{s.label}</span>
                      <span className="text-[11px] text-slate-400 truncate mt-0.5">{s.subject}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <button
              type="button"
              onClick={loadSampleBatch}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border border-slate-200/80 bg-white text-slate-700 hover:bg-slate-50 text-xs font-semibold shadow-xs transition"
            >
              <FileText size={14} className="text-[#5b5bf7]" />
              <span>Load Sample Batch</span>
            </button>
          )}
        </div>
      </div>

      {/* Global Error Banner */}
      {errorMessage && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 flex items-start gap-3 text-xs text-rose-800 animate-fadeIn">
          <AlertCircle size={17} className="text-rose-600 shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="font-bold">Execution Error</p>
            <p className="mt-0.5">{errorMessage}</p>
          </div>
          <button onClick={() => setErrorMessage('')} className="text-rose-400 hover:text-rose-600">✕</button>
        </div>
      )}

      {/* Mode 1: Single Email Scanner */}
      {activeMode === 'single' ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
          {/* Form Card (2 Cols) */}
          <form onSubmit={handleAnalyzeSingle} className="lg:col-span-2 bg-white rounded-3xl border border-slate-200/80 p-7 shadow-xs space-y-5">
            <div>
              <label className="block text-xs font-semibold text-slate-800 mb-2">Sender email</label>
              <input
                type="text"
                value={sender}
                onChange={(e) => setSender(e.target.value)}
                placeholder="sender@example.com"
                className="w-full px-4 py-3 rounded-xl border border-slate-200 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#5b5bf7]/20 focus:border-[#5b5bf7] transition"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-800 mb-2">Subject line</label>
              <input
                type="text"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="Enter the email subject"
                className="w-full px-4 py-3 rounded-xl border border-slate-200 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#5b5bf7]/20 focus:border-[#5b5bf7] transition"
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-xs font-semibold text-slate-800">Email body</label>
                {(subject || body) && (
                  <button
                    type="button"
                    onClick={handleClear}
                    className="text-[11px] text-slate-400 hover:text-slate-600 flex items-center gap-1"
                  >
                    <RotateCcw size={11} />
                    <span>Clear form</span>
                  </button>
                )}
              </div>
              <textarea
                rows={8}
                value={body}
                onChange={(e) => setBody(e.target.value)}
                placeholder="Paste the email content here..."
                className="w-full px-4 py-3 rounded-xl border border-slate-200 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#5b5bf7]/20 focus:border-[#5b5bf7] transition resize-none"
              />
            </div>

            <div className="flex items-center justify-between pt-3 border-t border-slate-100">
              <span className="text-xs text-slate-400">
                Processed locally by scikit-learn pipeline (model v3.8.2).
              </span>

              <button
                type="submit"
                disabled={loading}
                className="flex items-center gap-2 bg-[#5b5bf7] hover:bg-[#4f46e5] disabled:opacity-75 text-white font-semibold text-xs px-6 py-3.5 rounded-xl shadow-xs transition-all hover:scale-[1.01] active:scale-[0.99]"
              >
                <span>
                  {loading
                    ? loadingStep === 1
                      ? 'Extracting TF-IDF features...'
                      : 'Classifying threat signals...'
                    : 'Analyze email'}
                </span>
                <ArrowRight size={15} />
              </button>
            </div>
          </form>

          {/* Right Info Cards (1 Col) */}
          <div className="space-y-5">
            <div className="bg-[#f0f4ff] rounded-3xl border border-indigo-100/70 p-6 shadow-xs">
              <h3 className="font-bold text-slate-900 text-sm mb-4">What we analyze</h3>
              <ul className="space-y-3.5">
                {[
                  'Suspicious words and urgency',
                  'Sender reputation signals',
                  'Deceptive links and domains',
                  'Message structure and intent'
                ].map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2.5 text-xs text-slate-700 font-medium">
                    <div className="w-4 h-4 rounded-full bg-indigo-200/60 text-[#4f46e5] flex items-center justify-center shrink-0 mt-0.5">
                      <Check size={11} strokeWidth={3} />
                    </div>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="bg-white rounded-3xl border border-slate-200/80 p-6 shadow-xs">
              <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">PRIVACY FIRST</p>
              <p className="text-xs text-slate-600 leading-relaxed font-normal">
                Message content is processed strictly in-memory to generate predictions. Raw bodies are never committed to permanent logs.
              </p>
            </div>
          </div>
        </div>
      ) : (
        /* Mode 2: Batch Email Scanner */
        <div className="space-y-6">
          <form onSubmit={handleRunBatch} className="bg-white rounded-3xl border border-slate-200/80 p-7 shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-900">Batch Email Input</h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Enter one email per line in format: <code className="bg-slate-100 px-1 py-0.5 rounded text-[#4f46e5]">Subject | Body</code>
                </p>
              </div>
              <button
                type="button"
                onClick={() => setBatchRawText('')}
                className="text-xs text-slate-400 hover:text-slate-600"
              >
                Clear
              </button>
            </div>

            <textarea
              rows={6}
              value={batchRawText}
              onChange={(e) => setBatchRawText(e.target.value)}
              placeholder="Subject line | Email body content here..."
              className="w-full px-4 py-3 rounded-xl border border-slate-200 font-mono text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#5b5bf7]/20 focus:border-[#5b5bf7] transition resize-none"
            />

            <div className="flex items-center justify-between pt-2 border-t border-slate-100">
              <span className="text-xs text-slate-400">
                {batchRawText.split('\n').filter(l => l.trim().length > 0).length} emails entered
              </span>
              <button
                type="submit"
                disabled={batchLoading}
                className="flex items-center gap-2 bg-[#5b5bf7] hover:bg-[#4f46e5] disabled:opacity-50 text-white font-semibold text-xs px-6 py-3 rounded-xl shadow-xs transition"
              >
                <span>{batchLoading ? 'Executing Batch Prediction...' : 'Run Batch Analysis'}</span>
                <ArrowRight size={14} />
              </button>
            </div>
          </form>

          {/* Batch Results View */}
          {batchResults && (
            <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs overflow-hidden animate-fadeIn">
              <div className="p-6 border-b border-slate-100 flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-50/50">
                <div>
                  <h3 className="text-base font-bold text-slate-900">Batch Classification Summary</h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Analyzed {batchResults.total} emails in {batchResults.batch_latency_ms}ms
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="px-3 py-1 rounded-full bg-rose-100 text-rose-700 text-xs font-bold">
                    Spam: {batchResults.spam_count}
                  </span>
                  <span className="px-3 py-1 rounded-full bg-emerald-100 text-emerald-700 text-xs font-bold">
                    Legitimate: {batchResults.legitimate_count}
                  </span>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-slate-400 font-bold uppercase tracking-wider border-b border-slate-100">
                    <tr>
                      <th className="py-3 px-6">ID</th>
                      <th className="py-3 px-6">Subject Snippet</th>
                      <th className="py-3 px-6">Verdict</th>
                      <th className="py-3 px-6">Spam Prob</th>
                      <th className="py-3 px-6">Confidence</th>
                      <th className="py-3 px-6">Latency</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-medium">
                    {batchResults.predictions.map((p, idx) => (
                      <tr key={idx} className="hover:bg-slate-50/70 transition">
                        <td className="py-3.5 px-6 font-mono text-slate-400 text-[11px]">{p.id}</td>
                        <td className="py-3.5 px-6 text-slate-900 font-semibold">{p.subject_snippet}</td>
                        <td className="py-3.5 px-6">
                          <span className={`inline-flex px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            p.is_spam ? 'bg-rose-50 text-rose-600' : 'bg-emerald-50 text-emerald-600'
                          }`}>
                            {p.label.toUpperCase()}
                          </span>
                        </td>
                        <td className="py-3.5 px-6 font-mono text-slate-600">{(p.spam_probability * 100).toFixed(1)}%</td>
                        <td className="py-3.5 px-6 font-semibold text-slate-800">{p.confidence}%</td>
                        <td className="py-3.5 px-6 text-slate-400">{p.latency_ms}ms</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
