import React, { useState, useEffect } from 'react';
import { Search, AlertTriangle, CheckCircle, Clock, Filter, Download, ArrowUpRight, SearchCheck } from 'lucide-react';
import { fetchStats, fetchHistory } from '../api';

export default function AdminDashboardPage({ setCurrentTab, onOpenFeedback, setLatestResult }) {
  const [stats, setStats] = useState(null);
  const [history, setHistory] = useState([]);
  const [filterType, setFilterType] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchStats().then(setStats);
    fetchHistory().then(setHistory);
  }, []);

  const filteredHistory = history.filter((item) => {
    const isSpam = item.is_spam || item.prediction.toLowerCase() === 'spam';
    if (filterType === 'spam' && !isSpam) return false;
    if (filterType === 'legit' && isSpam) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        item.subject.toLowerCase().includes(q) ||
        item.id.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const handleRowClick = (row) => {
    const isSpam = row.is_spam || row.prediction.toLowerCase() === 'spam';
    const confVal = parseInt(row.confidence) || (isSpam ? 96 : 97);
    if (setLatestResult) {
      setLatestResult({
        id: row.id,
        is_spam: isSpam,
        label: isSpam ? 'spam' : 'legitimate',
        confidence: confVal,
        verdict_title: isSpam ? 'Likely spam' : 'Likely legitimate',
        recommendation: isSpam
          ? 'Avoid clicking links, downloading files, or replying to the sender.'
          : 'This message appears safe. Standard email vigilance still applies.',
        risk_breakdown: {
          content_signals: isSpam ? 92 : 14,
          sender_reputation: isSpam ? 81 : 18,
          link_safety: isSpam ? 96 : 9
        },
        flagged_reasons: isSpam ? [
          {
            title: 'Urgency language',
            severity: 'High',
            description: '"Expires today" and "2 hours" pressure immediate action.'
          },
          {
            title: 'Suspicious offer',
            severity: 'High',
            description: 'An unsolicited high-value reward is a common spam pattern.'
          },
          {
            title: 'Unknown sender',
            severity: 'Medium',
            description: 'The sender domain has limited reputation history.'
          },
          {
            title: 'Call to action',
            severity: 'High',
            description: 'The message asks you to confirm account details via a link.'
          }
        ] : [
          {
            title: 'Verified vocabulary',
            severity: 'Low',
            description: 'Text patterns align with routine business dialogue.'
          },
          {
            title: 'No deceptive offers',
            severity: 'Low',
            description: 'No artificial prize claims or financial lures.'
          },
          {
            title: 'Sender authentication',
            severity: 'Low',
            description: 'Sender domain has established reputation.'
          },
          {
            title: 'Safe navigation',
            severity: 'Low',
            description: 'No coercive redirect links detected.'
          }
        ],
        model_version: 'v3.8.2',
        subject: row.subject
      });
      setCurrentTab('result');
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-7 animate-fadeIn">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <p className="text-xs font-bold text-[#5b5bf7] tracking-wider uppercase mb-1">OPERATIONS</p>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Admin dashboard</h1>
          <p className="text-slate-500 text-sm mt-1">
            Monitor classification activity, community feedback, and system performance.
          </p>
        </div>

        <button
          onClick={() => {
            const jsonStr = JSON.stringify(history, null, 2);
            const blob = new Blob([jsonStr], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `mailguard_report_${Date.now()}.json`;
            a.click();
          }}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border border-slate-200/80 bg-white text-slate-700 hover:bg-slate-50 text-xs font-semibold shadow-xs transition"
        >
          <Download size={14} className="text-slate-500" />
          <span>Export report</span>
        </button>
      </div>

      {/* 4 KPI Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Card 1: Total scans */}
        <div className="bg-white rounded-3xl border border-slate-200/80 p-6 shadow-xs relative">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-semibold text-slate-600">Total scans</span>
            <div className="w-7 h-7 rounded-full bg-indigo-50 text-[#5b5bf7] flex items-center justify-center">
              <Search size={13} />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-slate-900 tracking-tight">
            {stats ? `${(stats.total_scans / 1000).toFixed(1)}K` : '28.4K'}
          </p>
          <p className="text-xs text-slate-500 mt-2 font-medium">
            <span className="text-emerald-600 font-semibold">+12.8%</span> this month
          </p>
        </div>

        {/* Card 2: Spam detected */}
        <div className="bg-white rounded-3xl border border-slate-200/80 p-6 shadow-xs relative">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-semibold text-slate-600">Spam detected</span>
            <div className="w-7 h-7 rounded-full bg-rose-50 text-rose-600 flex items-center justify-center font-bold text-xs">
              !
            </div>
          </div>
          <p className="text-3xl font-extrabold text-slate-900 tracking-tight">
            {stats ? stats.spam_detected.toLocaleString() : '4,386'}
          </p>
          <p className="text-xs text-slate-500 mt-2 font-medium">
            15.4% of scans
          </p>
        </div>

        {/* Card 3: Model accuracy */}
        <div className="bg-white rounded-3xl border border-slate-200/80 p-6 shadow-xs relative">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-semibold text-slate-600">Model accuracy</span>
            <div className="w-7 h-7 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <CheckCircle size={13} />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-slate-900 tracking-tight">
            {stats ? `${stats.accuracy_percent}%` : '99.2%'}
          </p>
          <p className="text-xs text-slate-500 mt-2 font-medium">
            <span className="text-emerald-600 font-semibold">+0.3%</span> this week
          </p>
        </div>

        {/* Card 4: Review queue */}
        <div 
          onClick={() => setCurrentTab('feedback')}
          className="bg-white rounded-3xl border border-slate-200/80 p-6 shadow-xs relative cursor-pointer hover:border-amber-200 transition"
        >
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-semibold text-slate-600">Review queue</span>
            <div className="w-7 h-7 rounded-full bg-amber-50 text-amber-600 flex items-center justify-center">
              <Clock size={13} />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-slate-900 tracking-tight">
            {stats ? stats.review_queue_count : '37'}
          </p>
          <p className="text-xs text-slate-500 mt-2 font-medium">
            8 high priority
          </p>
        </div>
      </div>

      {/* Recent Classifications Table Container */}
      <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs overflow-hidden">
        {/* Table Header Controls */}
        <div className="p-6 border-b border-slate-100 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h3 className="text-base font-bold text-slate-900">Recent classifications</h3>
            <p className="text-xs text-slate-500 mt-0.5">Live stream of model predictions</p>
          </div>

          <div className="flex items-center gap-3">
            {/* Filter Toggle */}
            <div className="inline-flex rounded-xl border border-slate-200/80 bg-white p-1 text-xs">
              <button
                onClick={() => setFilterType('all')}
                className={`px-3 py-1 rounded-lg font-semibold transition ${
                  filterType === 'all' ? 'bg-slate-100 text-slate-900' : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                All
              </button>
              <button
                onClick={() => setFilterType('spam')}
                className={`px-3 py-1 rounded-lg font-semibold transition ${
                  filterType === 'spam' ? 'bg-rose-50 text-rose-600' : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                Spam
              </button>
              <button
                onClick={() => setFilterType('legit')}
                className={`px-3 py-1 rounded-lg font-semibold transition ${
                  filterType === 'legit' ? 'bg-emerald-50 text-emerald-600' : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                Legitimate
              </button>
            </div>

            <button
              onClick={() => setCurrentTab('feedback')}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl border border-slate-200/80 bg-white text-slate-700 hover:bg-slate-50 text-xs font-semibold shadow-xs transition"
            >
              <span>Review queue</span>
            </button>
          </div>
        </div>

        {/* Table Content */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50/60 text-slate-400 font-bold uppercase tracking-wider border-b border-slate-100">
              <tr>
                <th className="py-3.5 px-6">ID</th>
                <th className="py-3.5 px-6">Subject</th>
                <th className="py-3.5 px-6">Prediction</th>
                <th className="py-3.5 px-6">Confidence</th>
                <th className="py-3.5 px-6">Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {filteredHistory.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-slate-400 text-xs">
                    No classification records matching your filter.
                  </td>
                </tr>
              ) : (
                filteredHistory.map((row) => {
                  const isSpam = row.is_spam || row.prediction.toLowerCase() === 'spam';
                  return (
                    <tr 
                      key={row.id} 
                      onClick={() => handleRowClick(row)}
                      className="hover:bg-slate-50/70 cursor-pointer transition"
                      title="Click to view prediction analysis"
                    >
                      <td className="py-4 px-6 font-mono text-slate-400 text-[11px]">{row.id}</td>
                      <td className="py-4 px-6 text-slate-900 font-semibold max-w-xs truncate">{row.subject}</td>
                      <td className="py-4 px-6">
                        <span
                          className={`inline-flex px-2.5 py-1 rounded-full text-[11px] font-bold ${
                            isSpam
                              ? 'bg-rose-50 text-rose-600'
                              : 'bg-emerald-50 text-emerald-600'
                          }`}
                        >
                          {isSpam ? 'Spam' : 'Legitimate'}
                        </span>
                      </td>
                      <td className="py-4 px-6 text-slate-700 font-semibold">{row.confidence}</td>
                      <td className="py-4 px-6 text-slate-400">{row.time}</td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
