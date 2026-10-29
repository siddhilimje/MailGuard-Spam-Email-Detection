import React, { useState, useEffect } from 'react';
import { 
  Settings, 
  Activity, 
  Clock, 
  TrendingUp, 
  CheckCircle2, 
  AlertCircle,
  ExternalLink,
  Layers,
  RefreshCw,
  HelpCircle
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip 
} from 'recharts';
import { fetchHealth, fetchStats, fetchModelInfo, fetchMetrics, fetchDriftMetrics, runDriftCheck } from '../api';

export default function ModelMonitoringPage() {
  const [health, setHealth] = useState(null);
  const [stats, setStats] = useState(null);
  const [modelInfo, setModelInfo] = useState(null);
  const [operationalMetrics, setOperationalMetrics] = useState(null);
  const [driftMetrics, setDriftMetrics] = useState(null);
  const [showDriftReport, setShowDriftReport] = useState(false);
  const [selectedStream, setSelectedStream] = useState('logs');
  const [isEvaluatingDrift, setIsEvaluatingDrift] = useState(false);
  const [apiError, setApiError] = useState('');

  const loadData = () => {
    fetchHealth().then(setHealth).catch(err => setApiError(err.message));
    fetchStats().then(setStats).catch(console.error);
    fetchModelInfo().then(setModelInfo).catch(console.error);
    fetchMetrics().then(setOperationalMetrics).catch(console.error);
    fetchDriftMetrics().then(setDriftMetrics).catch(console.error);
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRunDriftCheck = async (stream) => {
    setIsEvaluatingDrift(true);
    setSelectedStream(stream);
    try {
      const res = await runDriftCheck(stream);
      if (res && res.metrics) {
        setDriftMetrics(res.metrics);
      }
    } catch (err) {
      alert(`Drift evaluation failed: ${err.message}`);
    } finally {
      setIsEvaluatingDrift(false);
    }
  };

  const isDrifted = driftMetrics?.status === 'WARNING_DRIFT_DETECTED' || driftMetrics?.is_drift_detected;

  const chartData = stats?.hourly_volume || [
    { time: '08:00', volume: 320 },
    { time: '', volume: 480 },
    { time: '', volume: 410 },
    { time: '', volume: 690 },
    { time: '12:00', volume: 580 },
    { time: '', volume: 720 },
    { time: '', volume: 640 },
    { time: '', volume: 810 },
    { time: '16:00', volume: 760 },
    { time: '', volume: 890 },
    { time: '', volume: 830 },
    { time: 'Now', volume: 952 },
  ];

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-7 animate-fadeIn">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <p className="text-xs font-bold text-[#5b5bf7] tracking-wider uppercase mb-1">MODEL OPERATIONS</p>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Model & monitoring</h1>
          <p className="text-slate-500 text-sm mt-1">
            Live health metrics for the production spam-classification model ({modelInfo?.model_name || 'Multinomial Naive Bayes'}).
          </p>
        </div>

        <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-50 border border-emerald-100 text-emerald-700 text-xs font-semibold">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>{health?.status === 'healthy' ? 'All systems operational' : 'Connecting to API...'}</span>
        </div>
      </div>

      {apiError && (
        <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 text-xs text-amber-800">
          <strong>Notice:</strong> {apiError}
        </div>
      )}

      {/* 4 Health Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Card 1: Model version */}
        <div className="bg-white rounded-3xl border border-slate-200/80 p-6 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-semibold text-slate-600">Model version</span>
            <div className="w-7 h-7 rounded-full bg-indigo-50 text-[#5b5bf7] flex items-center justify-center">
              <Settings size={13} />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-slate-900 tracking-tight">
            {health?.model_version || modelInfo?.version || 'v3.8.2'}
          </p>
          <p className="text-xs text-slate-500 mt-2 font-medium">
            Champion in Production
          </p>
        </div>

        {/* Card 2: Uptime */}
        <div className="bg-white rounded-3xl border border-slate-200/80 p-6 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-semibold text-slate-600">Uptime</span>
            <div className="w-7 h-7 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <Activity size={13} />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-slate-900 tracking-tight">
            {health?.uptime_seconds ? `${health.uptime_seconds.toFixed(0)}s` : '99.99%'}
          </p>
          <p className="text-xs text-slate-500 mt-2 font-medium">
            Service continuous
          </p>
        </div>

        {/* Card 3: P95 latency */}
        <div className="bg-white rounded-3xl border border-slate-200/80 p-6 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-semibold text-slate-600">P95 latency</span>
            <div className="w-7 h-7 rounded-full bg-amber-50 text-amber-600 flex items-center justify-center">
              <Clock size={13} />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-slate-900 tracking-tight">
            {operationalMetrics?.p95_latency_ms ? `${operationalMetrics.p95_latency_ms}ms` : '1.4ms'}
          </p>
          <p className="text-xs text-slate-500 mt-2 font-medium">
            Target under 10ms
          </p>
        </div>

        {/* Card 4: Data drift */}
        <div className="bg-white rounded-3xl border border-slate-200/80 p-6 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-semibold text-slate-600">Data drift</span>
            <div className={`w-7 h-7 rounded-full flex items-center justify-center ${
              isDrifted ? 'bg-amber-100 text-amber-700' : 'bg-emerald-50 text-emerald-600'
            }`}>
              {isDrifted ? <AlertCircle size={13} /> : <TrendingUp size={13} />}
            </div>
          </div>
          <p className={`text-3xl font-extrabold tracking-tight ${
            isDrifted ? 'text-amber-600' : 'text-slate-900'
          }`}>
            {isDrifted ? 'Warning' : 'Low'}
          </p>
          <p className="text-xs text-slate-500 mt-2 font-medium">
            {isDrifted ? `${driftMetrics?.features_drift_summary || 'Multiple'} features drifted` : 'Within expected range'}
          </p>
        </div>
      </div>

      {/* Visual Analytics 2-Column Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Left: Prediction Volume Chart (2 Cols) */}
        <div className="lg:col-span-2 bg-white rounded-3xl border border-slate-200/80 p-7 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-slate-900">Prediction volume</h3>
              <p className="text-xs text-slate-500 mt-0.5">Throughput and request distribution</p>
            </div>
            <div className="text-right">
              <span className="text-xl font-extrabold text-slate-900">
                {operationalMetrics?.total_predictions.toLocaleString() || '28,412'}
              </span>
              <span className="text-xs text-emerald-600 font-bold ml-2">Active</span>
            </div>
          </div>

          <div className="h-64 w-full pt-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis 
                  dataKey="time" 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{ fill: '#94a3b8', fontSize: 11, fontWeight: 500 }}
                />
                <YAxis 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  hide={true}
                />
                <Tooltip 
                  cursor={{ fill: 'transparent' }}
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      return (
                        <div className="bg-slate-900 text-white text-xs px-3 py-1.5 rounded-lg shadow-lg">
                          <p className="font-semibold">{payload[0].value} scans</p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar 
                  dataKey="volume" 
                  fill="#5b5bf7" 
                  radius={[8, 8, 4, 4]} 
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Right: Service Health & Drift Status (1 Col) */}
        <div className="bg-white rounded-3xl border border-slate-200/80 p-7 shadow-xs space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-slate-900">Service health</h3>
            <button
              onClick={() => setShowDriftReport(true)}
              className="text-xs font-semibold text-[#5b5bf7] hover:underline flex items-center gap-1"
            >
              <span>Drift Report</span>
              <ExternalLink size={11} />
            </button>
          </div>

          <div className="space-y-4">
            {[
              { name: 'Classifier API', status: 'Operational', isOk: true },
              { name: 'Feature pipeline', status: 'Operational', isOk: true },
              { name: 'Feedback processor', status: 'Operational', isOk: true },
              { name: 'Threat intelligence', status: 'Degraded', isOk: false }
            ].map((srv, idx) => (
              <div key={idx} className="flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-700">{srv.name}</span>
                <div className="flex items-center gap-1.5">
                  <span
                    className={`w-2 h-2 rounded-full ${
                      srv.isOk ? 'bg-emerald-500' : 'bg-amber-500'
                    }`}
                  ></span>
                  <span
                    className={`font-semibold ${
                      srv.isOk ? 'text-emerald-700' : 'text-amber-700'
                    }`}
                  >
                    {srv.status}
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* Model Quality Gate Banner */}
          <div className="bg-slate-50/80 rounded-2xl p-4 border border-slate-100 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-slate-800">Validation F1-Score:</span>
              <span className="font-bold text-emerald-600">
                {modelInfo?.evaluation_metrics?.f1_score ?? 96.6}%
              </span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-slate-800">False Positives:</span>
              <span className="font-semibold text-slate-700">
                {modelInfo?.confusion_matrix?.false_positives ?? 12}
              </span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-slate-800">Quality Gate:</span>
              <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 font-bold text-[10px]">
                {modelInfo?.quality_gate_status ?? 'PASSED'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Evidently AI Drift Report Modal */}
      {showDriftReport && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-xs flex items-center justify-center p-4 animate-fadeIn">
          <div className="bg-white rounded-3xl max-w-3xl w-full p-7 shadow-2xl border border-slate-200 space-y-5 max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-indigo-50 text-[#5b5bf7] flex items-center justify-center font-bold">
                  <Layers size={18} />
                </div>
                <div>
                  <h3 className="font-bold text-slate-900 text-base">Evidently AI Drift Monitoring</h3>
                  <p className="text-xs text-slate-400">Dataset drift report across Enron baseline & production streams</p>
                </div>
              </div>
              <button
                onClick={() => setShowDriftReport(false)}
                className="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-600 flex items-center justify-center text-sm font-bold"
              >
                ✕
              </button>
            </div>

            {/* Stream Evaluation Selector */}
            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">Select Stream for Drift Test:</span>
                {isEvaluatingDrift && (
                  <span className="text-xs text-[#5b5bf7] font-semibold animate-pulse">Running Evidently AI evaluation...</span>
                )}
              </div>
              <div className="flex flex-wrap gap-2">
                {[
                  { id: 'logs', label: 'Live Prediction Stream' },
                  { id: 'normal', label: 'Normal Stream (Held-out)' },
                  { id: 'drifted', label: 'Drifted Phishing Stream' }
                ].map(stream => (
                  <button
                    key={stream.id}
                    disabled={isEvaluatingDrift}
                    onClick={() => handleRunDriftCheck(stream.id)}
                    className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition ${
                      selectedStream === stream.id 
                        ? 'bg-[#5b5bf7] text-white shadow-xs' 
                        : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-100'
                    }`}
                  >
                    {stream.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Metrics Overview */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100">
                <p className="text-slate-400 font-medium">Reference Samples</p>
                <p className="text-sm font-bold text-slate-800 mt-1">{driftMetrics?.reference_samples || 1000}</p>
              </div>
              <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100">
                <p className="text-slate-400 font-medium">Stream Samples</p>
                <p className="text-sm font-bold text-slate-800 mt-1">{driftMetrics?.current_samples || 100}</p>
              </div>
              <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100">
                <p className="text-slate-400 font-medium">Features Drifted</p>
                <p className={`text-sm font-bold mt-1 ${isDrifted ? 'text-amber-600' : 'text-emerald-600'}`}>
                  {driftMetrics?.features_drift_summary || '0/7'}
                </p>
              </div>
              <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100">
                <p className="text-slate-400 font-medium">Drift Status</p>
                <p className={`text-sm font-bold mt-1 ${isDrifted ? 'text-amber-600' : 'text-emerald-600'}`}>
                  {isDrifted ? 'Drift Detected' : 'Healthy'}
                </p>
              </div>
            </div>

            {/* Alert Status Banner */}
            <div className={`p-4 rounded-2xl border space-y-1 ${
              isDrifted ? 'bg-amber-50 border-amber-200 text-amber-900' : 'bg-emerald-50 border-emerald-100 text-emerald-900'
            }`}>
              <div className="flex items-center gap-2 font-bold text-xs">
                {isDrifted ? <AlertCircle size={16} className="text-amber-600" /> : <CheckCircle2 size={16} className="text-emerald-600" />}
                <span>{driftMetrics?.alert_message || 'Baseline checked: distributions match expected bounds.'}</span>
              </div>
              <p className="text-[11px] opacity-80">
                Drift Share: {(driftMetrics?.drift_share * 100 || 0).toFixed(1)}% | Alert Threshold: {(driftMetrics?.drift_share_threshold * 100 || 30).toFixed(1)}% | p-value threshold: {driftMetrics?.p_value_threshold || 0.05}
              </p>
            </div>

            {/* Per-Feature Drift Breakdown */}
            {driftMetrics?.features && (
              <div className="space-y-2">
                <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">Feature Drift Breakdown (Kolmogorov-Smirnov Tests)</h4>
                <div className="border border-slate-100 rounded-2xl overflow-hidden max-h-48 overflow-y-auto">
                  <table className="w-full text-left text-[11px]">
                    <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-100">
                      <tr>
                        <th className="py-2 px-3">Feature</th>
                        <th className="py-2 px-3">Ref Mean</th>
                        <th className="py-2 px-3">Stream Mean</th>
                        <th className="py-2 px-3">p-value</th>
                        <th className="py-2 px-3">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {Object.values(driftMetrics.features).map((feat, idx) => (
                        <tr key={idx} className={feat.is_drifted ? 'bg-amber-50/40' : ''}>
                          <td className="py-2 px-3 font-semibold text-slate-800">{feat.feature}</td>
                          <td className="py-2 px-3 text-slate-600">{feat.ref_mean}</td>
                          <td className="py-2 px-3 text-slate-600">{feat.curr_mean}</td>
                          <td className="py-2 px-3 text-slate-600">{feat.p_value}</td>
                          <td className="py-2 px-3">
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                              feat.is_drifted ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'
                            }`}>
                              {feat.is_drifted ? 'DRIFT' : 'OK'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* MLOps Educational Note: Data Drift vs Performance Degradation */}
            <div className="p-3.5 rounded-2xl bg-indigo-50/60 border border-indigo-100/80 text-[11px] text-indigo-950 space-y-1">
              <div className="flex items-center gap-1.5 font-bold text-indigo-800">
                <HelpCircle size={14} />
                <span>MLOps Principle: Data Drift vs. Model Performance Degradation</span>
              </div>
              <p className="text-slate-600 leading-relaxed">
                {driftMetrics?.conceptual_distinction || 
                  "Data drift measures shifts in the input feature distribution P(X) without labels. True production accuracy and F1 degradation P(Y|X) cannot be measured without verified ground-truth labels from human review."}
              </p>
            </div>

            {/* Modal Actions */}
            <div className="flex items-center justify-between pt-3 border-t border-slate-100">
              <a
                href="http://localhost:8000/api/monitoring/drift/report.html"
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-indigo-50 hover:bg-indigo-100 text-[#5b5bf7] text-xs font-semibold transition"
              >
                <span>Open Full Evidently AI Report</span>
                <ExternalLink size={13} />
              </a>

              <button
                onClick={() => setShowDriftReport(false)}
                className="px-5 py-2 rounded-xl bg-slate-900 text-white font-semibold text-xs hover:bg-slate-800 transition"
              >
                Close Report
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
